# Story OS Storage Architecture v1.0

日期：2026-09-20
适用分支：`story-platform-v3`

## 1. 三层权威模型

| 数据类别 | 唯一权威 | 允许的本地文件 | 禁止行为 |
|---|---|---|---|
| Runtime State / durable facts | MySQL `story_os_runtime` | 仅导出视图或迁移期间证据 | 以 `runtime-checkpoint.json`、`runtime-dag-state.json` 作为数据库替身 |
| Hot State / current pointer | Redis 127.0.0.1:6379 | 旧 Episode 的 activation-guarded 兼容副本 | Redis 模式故障时静默读写 JSON |
| Artifact / large document or binary | File/Object Workspace + MySQL Artifact Index | 原始文件、证据文档、媒体 | 将全文、图片信息或大事件序列混入 JSON 字段 |

模型可简写为：

```text
Runtime State -> MySQL
Hot State     -> Redis
Artifact      -> File/Object + MySQL index(SHA256, BYTE_SIZE, URI)
```

## 2. MySQL 设计约束

- inline JSON 的硬门槛为 16KiB；当前 live DB 审计为 18 个 JSON 字段、0 个超阈值、0 个未批准字段。
- 大正文使用 `BLOB/MEDIUMBLOB + SHA256 + BYTE_SIZE` 或 Artifact Index 引用。现有 `TB_ARTIFACT_INDEX.METADATA_BLOB/METADATA_SHA256` 和 `TB_PRODUCTION_LEDGER_AUTHORITY.DOCUMENT_BLOB/DOCUMENT_SHA256` 属于该模式。
- `TB_TASK.PAYLOAD` 只保留低频任务扩展和文档 projection；`runner_events` 已迁移为外部文档引用。
- JSON 只承载 bounded extension、动态属性、小型 projection；稳定查询字段优先使用 typed column。

## 3. 运行时写入边界

### MySQL

Event、Trace、Artifact、Workflow、Task、Runtime Request、Host Request、Review、Release、Metric 等 durable record 通过 repository 写入 MySQL。读仓储返回契约字段的小写名称，Trace 数据库列名映射如下：

```text
START_TIME -> started_at
END_TIME   -> ended_at
ELAPSED_MS -> duration_ms
ERROR_TEXT -> error
SPAN_NAME  -> operation
```

### Redis

`hot_state_bridge.py` 是 current pointer、heartbeat、lock、queue、resume/circuit-breaker 等热状态的入口。Redis 模式下 Redis 异常直接报错，不使用文件 fallback；队列审计确认 14 个真实 Episode 已 workspace-native，剩余 6 个 `legacy_pinned` 仅为 `_tests/driver-*` 空夹具。

### Artifact

大 JSON、原始 worker 证据、媒体和报告存放在 Runtime Workspace/File/Object；数据库保存引用、SHA256、字节数和必要索引。`materialize_export` 生成的 JSON 是显式导出物，不是运行时权威。

## 4. 验证结果

- MySQL：8.0.46，database `story_os_runtime`。
- Redis：8.10.1，AOF enabled。
- Runtime smoke：47 PASS、0 FAIL、2 SKIPPED；探针自清理通过，本轮保留探针已精确清除，当前 MySQL 探针基线为 42/0/0、Redis DBSIZE=1。
- checkpoint externalization：事件序列 SHA/count 校验和 mismatch fail-closed 测试通过。
- Recovery soak：worker crash 8/8、recovery execution 6/6；恢复后的健康输入从 MySQL Trace Repository 读取。
- Runtime Worker health scope：默认 60 分钟滑动窗，并以当前 Worker `instance_started_at` 再收窄终结 Trace；旧 RUNNING span 不被过滤，继续承担 stuck 信号。真实单 tick evidence 已记录 instance/window。

## 5. 历史兼容边界

旧历史目录继续保留用于兼容、导出或审计，不能以“目录里还有 JSON”直接判定 Authority 旁路。当前 Runtime Workspace 生产 UNKNOWN=0，历史 `episodes` UNKNOWN 也已从 14 收敛到 0；其中 durable contract/artifact/release/migration 归 MySQL，历史源数据、归档元数据和系统 manifest 归 File。健康评分已采用 Worker 实例 + 时间窗口径，因此旧失败终结 Trace 不再影响新实例；旧 RUNNING span 仍保留为真实 stuck 信号。
