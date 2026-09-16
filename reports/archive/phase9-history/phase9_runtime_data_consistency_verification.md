# Phase 9 - P9.26.6 Runtime Data Consistency Verification

日期：2026-09-10
分支：story-platform-v3
验证方式：本机 Python 3.12.10 + pymysql 1.4.6，真实实例 121.89.82.216:9000（MySQL 8.0.46 / utf8mb4 / utf8mb4_unicode_ci）

## 结论

P9.26.6 完成：已建立 Legacy(JSONL) 与 MySQL 的一致性校验器与全量巡检，四类异常（legacy_only / mysql_only / 字段差异 / 重复数据）在真实 MySQL 上逐项复现并按策略收敛。真实实例端到端 21 项检查全部通过，探测数据已清理，三表回到空表状态。

## 1. 校验范围

| 实体 | 主键 | 比对字段 | JSON/Hash 字段 |
| --- | --- | --- | --- |
| Event | event_id | event_type / aggregate_type / aggregate_id / occurred_at / trace_id / task_id | payload / metadata |
| Trace | (trace_id, span_id) | operation / status / started_at / ended_at / duration_ms / request_id / episode_id / task_id / parent_span_id / error | inputs / outputs / attributes |
| Artifact | artifact_id | artifact_type / path / sha256 / owner_type / owner_id / created_by / created_at / trace_id / task_id | metadata |

单条结果三态：MATCH / MISMATCH / MISSING（reason 区分 legacy_only / mysql_only / both_missing）。

## 2. 归一化规则

两侧物理形态不同，直接比对会产生假差异，因此先归一化：

- 时间：Legacy 经 `default=str` 落盘为字符串，MySQL 为 DATETIME(6) 对象且 pymysql 写入不带时区。统一按“墙钟时间”格式化为 `%Y-%m-%dT%H:%M:%S.%f`；缺失微秒补零。
- 枚举：统一取 `.value`。
- JSON 字段：解析后按 canonical JSON（sort_keys + 紧凑分隔符）计算 SHA-256 比对，兼容 MySQL 侧返回的 JSON 字符串。

本轮测试中修复了一处真实缺陷：`occurred_at` 等时间字段原先只做字符串化，导致 Legacy 字符串与 MySQL datetime 必然判为 MISMATCH。修正后同一实体的双写数据稳定判 MATCH。

## 3. 巡检与异常策略

巡检流程：读取 Legacy -> 读取 MySQL -> 按主键 Diff -> 生成 Evidence。

| 情况 | 处理 | 开关 |
| --- | --- | --- |
| Legacy 有，MySQL 无 | 补偿写（由 Legacy 记录重建契约写入 MySQL） | compensating_write |
| MySQL 有，Legacy 无 | 记录异常，不自动删除 | record_anomalies |
| 字段差异 | 进入修复队列（含字段级 diff 与两侧 hash） | repair_queue |
| 重复数据 | 幂等合并，保留首条并记录重复主键 | merge_duplicates |

策略默认只读取证（compensating_write 默认关闭），写动作必须显式开启。

## 4. 真实实例实测

基线：三表均为空表，双写 1 条 Event + 1 条 Trace + 1 条 Artifact（含中文 payload、嵌套 JSON、Boolean、微秒时间）后开始巡检。

| 场景 | 结果 |
| --- | --- |
| 双写写入 | Event / Trace / Artifact 三侧均 {legacy: OK, mysql: OK} |
| 单条比对 | compare_event / compare_trace / compare_artifact 均 MATCH，field_diffs 为空 |
| 全量巡检 | 三类实体 counts 均为 match=1，其余为 0 |
| Legacy 有 / MySQL 无 | 正确识别 legacy_only=1 |
| 补偿写 | compensated=[p9probe-evt2-*]，MySQL 复查已存在，复扫 match=2 |
| MySQL 有 / Legacy 无 | 正确识别 mysql_only=1，并写入 anomalies |
| 字段差异 | 篡改 MySQL payload 后判定 MISMATCH(field_diff)，payload hash 不匹配、metadata hash 仍匹配，repair_queue 生成 1 条 |
| 修复回写 | MySQL 重写为与 Legacy 一致后复查恢复 MATCH |
| 重复数据 | Legacy 追加重复行后 duplicates=[p9probe-evt-*]，total_legacy 按键合并为 1 |
| 数据清理 | DELETE 探测主键后三表行数与巡检前完全一致（0/0/0） |

汇总：21 项检查，0 失败（ALL_OK TRUE）。

## 5. 代码与测试

新增：

- platform/repository/consistency/__init__.py
- platform/repository/consistency/runtime_consistency_checker.py —— ConsistencyStatus / ConsistencyReport / RuntimeConsistencyChecker / RuntimeConsistencyScan / ScanPolicy
- tests/platform/test_runtime_consistency_checker.py（9 例）

测试：tests/platform 全量 137 passed / 0 failed（原 125 + P9.26.5 新增 4 + 本阶段新增 9，其中 1 例为时间归一化回归）。

## 6. 风险与限制

- 巡检已改为优先走 keyset 分页流式读取（P9.27 `iter_all`），真实数据量下的耗时基准仍未采集。
- 未做自动调度：巡检目前需人工/脚本触发，无常驻任务与告警接入。
- 补偿写是单向的（Legacy -> MySQL），MySQL 独有数据只记录异常不自动处理。
- 时间比对按墙钟时间，不同时区写入但墙钟相同的记录会被判为一致。P9.27 已在写入侧统一为 naive UTC，两侧约定一致；Runtime 内部生成时间的两套写法仍需收敛。
- 校验器尚未接入生产写入链路，本轮为 Runtime Data Foundation 阶段首次真实接线验证。
