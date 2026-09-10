# Phase 9 - P9.27 数据底座收口（弃用 UPSERT 收敛 + 巡检调度入口）

日期：2026-09-10
分支：story-platform-v3
代码基线：273c048（本批改动仍在工作树未提交）
验证方式：本机 Python 3.12.10 + pymysql 1.4.6，真实实例 121.89.82.216:9000（MySQL 8.0.46 / utf8mb4 / utf8mb4_unicode_ci）

## 结论

本批处理 P9.26/P9.27 遗留清单里的两个数据底座缺口，都已在真实实例上取证：

1. 三个 MySQL Repository 的 UPSERT 从 MySQL 8.0.20 起弃用的 `VALUES(col)` 迁到 row-alias
   写法（`INSERT ... VALUES (...) AS new ON DUPLICATE KEY UPDATE col = new.col`）。真实实例
   对照实测：旧写法在 `SHOW WARNINGS` 里返回 2 条 `1287`，新写法 `SHOW WARNINGS` 为空。
2. 新增 `scripts/phase9_consistency_scan.py`，把 Legacy(JSONL) vs MySQL 一致性巡检从"只能在
   测试与冒烟脚本内部调用"变成可被计划任务 / CI 直接调用的独立命令，默认只读取证，用退出码
   表达结论。

真实实例端到端 11 项检查 0 失败；探测行与探测目录已清理，三表回到空表。

## 1. 弃用语法收敛

改动前（MySQL 8.0.20+ 弃用）：

```sql
INSERT INTO event_log (...) VALUES (...)
ON DUPLICATE KEY UPDATE event_type=VALUES(event_type), ...
```

改动后（row-alias，8.0.19+）：

```sql
INSERT INTO event_log (...) VALUES (...) AS new
ON DUPLICATE KEY UPDATE event_type=new.event_type, ...
```

三个仓储同步迁移：

| 文件 | 常量 |
| --- | --- |
| platform/repository/mysql/mysql_event_repository.py | `_EVENT_UPSERT_SQL` |
| platform/repository/trace/mysql_trace_repository.py | `_TRACE_UPSERT_SQL` |
| platform/repository/artifact/mysql_artifact_repository.py | `_ARTIFACT_UPSERT_SQL` |

真实实例对照（同一条连接、同一张 event_log）：

| 写法 | `SHOW WARNINGS` |
| --- | --- |
| `... ON DUPLICATE KEY UPDATE payload=VALUES(payload)` | codes = `["1287", "1287"]` |
| `... VALUES (...) AS new ON DUPLICATE KEY UPDATE payload=new.payload` | `[]`（空） |

语义未变：仍按主键幂等覆盖，`save()` 的参数与顺序未动，公共接口未改。

## 2. 巡检调度入口

新增 `scripts/phase9_consistency_scan.py`：

```
Legacy JSONL --+
               +--> RuntimeConsistencyChecker --> RuntimeConsistencyScan --> Evidence JSON
MySQL 三表   --+
```

用法（凭据只从环境变量读取，不写进仓库任何文件）：

```powershell
$env:STORYOS_MYSQL_HOST="..."; $env:STORYOS_MYSQL_PORT="..."
$env:STORYOS_MYSQL_USER="..."; $env:STORYOS_MYSQL_PWD="..."
$env:STORYOS_MYSQL_DB="story_os_runtime"
python scripts/phase9_consistency_scan.py --jsonl-root .storyos
```

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--jsonl-root` | `STORYOS_RUNTIME_JSONL_ROOT` 或 `.storyos` | Legacy 侧根目录 |
| `--entity` | 全部 | 只巡检 event / trace / artifact，可重复 |
| `--compensate` | 关闭 | 对 legacy_only 执行补偿写（Legacy -> MySQL）；默认只读取证 |
| `--evidence-file` | `.storyos/smoke/phase9_consistency_scan_evidence.json` | 证据 JSON |
| `--quiet` | 关闭 | 只留汇总 |

退出码：`0` 一致；`2` 发现不一致 / 异常；`3` 参数或环境错误。

判定口径（`_entity_verdict`）：`mismatch`、未补偿的 `legacy_only`、`mysql_only`、`duplicates`
任一非零即判不一致；开启 `--compensate` 后，已补偿的 legacy_only 不再计为未决问题，但计数仍
如实保留原始值。

边界：这是"可被调度的单次巡检命令"，不是常驻任务；脚本自己不排程、不告警、不清理数据。

## 3. 真实实例实测

| 步骤 | 结果 |
| --- | --- |
| dual_write_facts | Legacy 3 行 / MySQL 3 行（3 event + 2 trace + 1 artifact，含中文 payload、嵌套 JSON、布尔、微秒时间） |
| scan_consistent_exit0 | exit 0；event match=3、trace match=2、artifact match=1，mismatch / legacy_only / mysql_only / duplicates 全 0 |
| scan_stdout_sample | 终端逐实体行 + `consistent=True` |
| row_alias_upsert_no_warning | `SHOW WARNINGS` = `[]` |
| legacy_values_syntax_still_warns_1287 | codes = `["1287", "1287"]` |
| scan_detects_mismatch_exit2 | exit 2；event mismatch=1，issues=`["mismatch=1"]`（篡改 MySQL payload） |
| restore_returns_consistent_exit0 | exit 0；mismatch=0，duplicates=[]（回写原始 payload 后恢复一致） |
| scan_detects_mysql_only_exit2 | exit 2；mysql_only=1，anomalies=`[p9scan-evt-mysql-only]`（只写 MySQL 不写 Legacy） |
| evidence_has_no_credentials | 证据 JSON 无密码明文，`password_present=true`、`host=121.89.82.216` |
| cleanup_removes_probe_rows | probe_left=`{event_log:0, trace_span:0, artifact_index:0}`，total 同为 0 |
| cleanup_files_removed | 探测目录与证据文件均已删除 |

汇总：11 项，failed=0。
### 3.1 补偿写路径复测（同批复现，11 项 0 失败）

独立复跑了“只写 Legacy -> 巡检发现 -> 补偿写 -> 恢复一致”这条缺陷路径，验证 `--compensate` 不是纸面开关：

| 步骤 | 结果 |
| --- | --- |
| seed_legacy_only | Legacy 写入 event/trace/artifact 各 1 条，MySQL 侧无对应行 |
| scan_legacy_only_exit2 | exit 2；`consistent=False`，`inconsistent=['event','trace','artifact']` |
| scan_compensate_exit0 | `--compensate`；exit 0；`consistent=True`（Legacy -> MySQL 补偿写） |
| scan_after_compensate_exit0 | 去掉 `--compensate` 只读复检仍 exit 0（补偿结果稳定，非临时态） |
| evidence_consistent_flag | 证据 JSON `summary.consistent=true`，`inconsistent_entities=[]` |
| per_entity_match_counts | `entities_detail` 中 event/trace/artifact 的 match 均为 1 |
| evidence_records_env_without_secret | 证据只记 host=121.89.82.216 / port=9000 / database=story_os_runtime 与 `password_present=true` |
| evidence_has_no_password | 证据全文中不含密码字符串 |
| legacy_values_syntax_warns_1287 | 旧写法 `SHOW WARNINGS` = `["1287"]` |
| row_alias_upsert_no_warning | 新写法 `SHOW WARNINGS` = `[]` |
| cleanup_back_to_zero | 三表 `event_log / trace_span / artifact_index` 探测行全部回到 0 |


终端实际输出（首次一致巡检）：

```
Story OS V3 Phase9 一致性巡检
  jsonl_root=...\.storyos\smoke\consistency_scan_probe
  entity=event,trace,artifact compensate=False
  event    legacy=3 mysql=3 match=3 mismatch=0 legacy_only=0 mysql_only=0 duplicates=0
  trace    legacy=2 mysql=2 match=2 mismatch=0 legacy_only=0 mysql_only=0 duplicates=0
  artifact legacy=1 mysql=1 match=1 mismatch=0 legacy_only=0 mysql_only=0 duplicates=0

== 汇总 ==
  consistent=True inconsistent=[]
```

## 4. 代码与测试

新增：

- scripts/phase9_consistency_scan.py
- tests/platform/test_phase9_consistency_scan_script.py（10 例，全离线，用假 MySQL 连接）
- tests/platform/test_mysql_upsert_row_alias.py（2 例，锁住新写法不回归到 `VALUES(col)`）

修改：

- platform/repository/mysql/mysql_event_repository.py
- platform/repository/trace/mysql_trace_repository.py
- platform/repository/artifact/mysql_artifact_repository.py

测试：tests/platform 全量 211 passed / 0 failed（原 199 + 本批 12）；
tests/system 186 passed + 16 subtests；合计 397 passed + 16 subtests。

## 5. 仍未完成

- 巡检无调度载体：本批交付的是可调度命令，常驻任务与告警通道仍未接入。
- 补偿写是单向的（Legacy -> MySQL）；MySQL 独有数据只记录异常，不自动处理。
- 连接是"每线程连接"，不是连接池：没有连接数上限与空闲回收。
- 数据库账号仍是 `root@%` + GRANT OPTION，且与 nacos_config 等库共用同一实例。
- 时间比对按墙钟时间；写入侧已统一 naive UTC，跨时区同墙钟仍会被判一致。
- 常驻 Runtime Worker 仍无进程载体，Runtime Smoke 是 in-process 取证。
- Redis 在本机（127.0.0.1:6379，allkeys-lru），MySQL 在远端，实例物理割裂。
