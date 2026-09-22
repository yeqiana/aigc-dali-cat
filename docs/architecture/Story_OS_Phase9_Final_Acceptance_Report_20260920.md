# Story OS Phase9 Final Acceptance Report

日期：2026-09-20
分支：`story-platform-v3`
范围：Phase9.5 数据库字段治理、运行时权威链路、生产硬化

## 1. 结论

Phase9.5 的数据库收口、Runtime Authority、生产 JSON 归属、MySQL/Redis 生产烟测与恢复演练均已通过。历史目录 14 个 UNKNOWN 已逐项建立 owner 并收敛为 0；Runtime Worker 健康评分已增加运行实例边界与 60 分钟滑动时间窗。当前无 Phase9.5 生产 Authority 或数据治理阻塞。

## 2. 验收矩阵

| 路径 | 本次证据 | 结果 |
|---|---|---|
| JSON 字段审计 | `python scripts/phase9_mysql_json_audit.py --strict`：18 个 JSON 字段，0 个超阈值，0 个未批准 | PASS |
| 大 JSON 清理 | `TB_TASK.PAYLOAD` 的 `runner_events` 从内嵌正文改为 Runtime Workspace 文档引用 + SHA256；目标行已应用 | PASS |
| 生产 JSON 扫描 | Runtime Workspace 290 个生产 JSON / 12,013,893B，生产 UNKNOWN=0；历史 `episodes` 1,105 个 JSON 已从 UNKNOWN=14 收敛到 0（MySQL 727 / Redis 76 / File 302） | PASS |
| Runtime Authority | MySQL 事实、Redis 热状态、File/Object Artifact；Redis bridge 禁止 redis 模式回退文件 | PASS |
| 生产烟测 | `phase9_runtime_smoke.py --mode mysql`：47 PASS、0 FAIL、2 SKIPPED；探针自清理通过，随后本轮保留探针也精确清除，当前 MySQL 42/0/0、Redis DBSIZE=1 | PASS |
| Kill/restart/resume | `phase95-recovery-d.json`：worker crash 8/8、recovery execution 6/6；恢复健康读取 MySQL trace | PASS |
| 健康评分实例/时间窗 | `phase95-health-window-validation.json`：真实 MySQL/Redis 单 tick，instance/window 证据已落盘，health=100、0 open incident；窗口专项测试通过 | PASS |
| 全量回归 | `tests/platform`：446 passed；`tests/system`：1,244 passed、1 skipped、90 subtests passed | PASS |
| 文档冻结 | 本报告、Storage Architecture v1.0、JSON Governance Report | PASS |

## 3. 关键变更

1. `runtime_checkpoint_persistence.py` 不再把 `runner_events` 整体塞进 `TB_TASK.PAYLOAD`。大事件序列写入 `meta/runtime/checkpoint-events/<sha256>.json`，MySQL 仅保存 projection type、事件数、字节数、SHA256 和文档相对引用。
2. MySQL 读取时对文档存在性、字节数、SHA256、事件数做 fail-closed 校验；缺文件或校验不一致不会静默回退旧 JSON。
3. Event、Trace、Artifact MySQL 读仓储统一列名大小写，并将 `START_TIME/END_TIME/ELAPSED_MS/ERROR_TEXT` 映射为 Trace 契约字段，修复真实 MySQL 驱动与验收代码之间的读字段偏差。
4. `phase9_mysql_json_audit.py --strict` 固化 16KiB inline JSON 门槛和批准字段清单；`phase95_checkpoint_payload_migrate.py` 提供 dry-run/指定 task apply 迁移入口。
5. `phase95_runtime_json_inventory.py` 固化只读 JSON 文件盘点，不删除历史文件、不改变 Episode 阶段。
6. MySQL 模式的 Runtime Worker 健康读取改为 MySQL Trace Repository；探针使用实际 `TB_*` 表名，且 MySQL authority 下不再把 Legacy 缺失误报为一致性告警。
7. Runtime Worker 健康评分不再直接消费全量历史终结 Trace：SUCCESS/FAILED 仅统计当前 Worker 实例启动后且位于 60 分钟滑动窗内的 span；旧 RUNNING 仍参与 stuck 检测。instance/window 参数同时写入 summary、health inputs 和 evidence。

## 4. 收口结果

- 历史/归档目录 UNKNOWN 已从 14 收敛到 0，所有文件保留且明确 owner/lifecycle，没有通过删除历史文件制造通过。
- 健康评分实例/时间窗策略已落代码、专项测试与真实 Worker evidence；历史失败终结 span 不再污染新 Worker。
- 生产队列边界已验收：14 个真实 Episode 均 workspace-native；6 个 legacy-pinned 仅为 `_tests/driver-*` 空夹具，不再作为生产遗留项。
