# Story OS JSON Governance Report

日期：2026-09-20
审计命令：`python scripts/phase9_mysql_json_audit.py --strict`
阈值：16,384 bytes

## 1. 数据库 JSON 字段清单

以下是当前 live MySQL 实际发现的 18 个 JSON 字段。`max_bytes` 是当前数据最大单行序列化大小，不是字段类型容量。

| 表 | 字段 | max bytes | 使用场景 | 治理决定 |
|---|---|---:|---|---|
| TB_RUNTIME_REQUEST | PAYLOAD | 13,728 | Runtime Request projection/document ref | 保留 bounded JSON；稳定查询字段再 typed 化 |
| TB_HOST_REQUEST | PAYLOAD | 11,077 | Host request projection/document ref | 保留 bounded JSON；大正文走 Artifact |
| TB_METRIC_SNAPSHOT | PAYLOAD | 9,333 | 指标 projection/document ref | 保留 bounded JSON；聚合指标 typed 化 |
| TB_RUNTIME_REVIEW_REQUEST | PAYLOAD | 8,625 | Review lifecycle projection | 保留 bounded JSON；全文走 Artifact |
| TB_RELEASE_RECORD | PAYLOAD | 7,343 | Release summary/document ref | 保留 bounded JSON |
| TB_EPISODE_CONTRACT | PAYLOAD | 6,215 | 小型 Episode contract projection | 保留 bounded JSON |
| TB_TASK | PAYLOAD | 4,953 | 低频 task extension | 保留；`runner_events` 已外置 |
| TB_PRODUCTION_ATTEMPT | PAYLOAD | 4,311 | Attempt evidence extension | 保留 bounded JSON |
| TB_FRAME_REVIEW | PAYLOAD | 3,389 | Review summary/issues/ref | 保留 bounded JSON |
| TB_APPROVAL_RECORD | PAYLOAD | 3,117 | Approval summary/ref | 保留 bounded JSON |
| TB_PROVIDER_RECEIPT | PAYLOAD | 1,758 | Provider sanitized extension | 保留 bounded JSON |
| TB_PROMPT_PACKAGE | PAYLOAD | 1,471 | Prompt hash/summary/ref | 保留 bounded JSON |
| TB_FRAME_CONTRACT | PAYLOAD | 801 | Frame contract projection | 保留 bounded JSON |
| TB_EVENT_LOG | PAYLOAD | 306 | Event payload | 保留动态事件 JSON |
| TB_EVENT_LOG | METADATA | 2 | Event metadata | 保留动态事件 JSON |
| PLATFORM_LATEST_RECORD | payload | 0 | Latest-record snapshot | 保留，当前无数据 |
| TB_REVIEW_RECORD | PAYLOAD | 0 | Review summary/ref | 保留，当前无数据 |
| TB_TRACE_SPAN | ATTRIBUTES | 0 | Observability attributes | 保留，当前无数据 |

审计结果：`json_columns=18`、`oversized_columns=0`、`unapproved_columns=0`。此前“17 个”的口径遗漏了 `PLATFORM_LATEST_RECORD.payload`，本报告以 live schema 为准。

## 2. 大 JSON 清理结果

本轮唯一超 16KiB 的 live 行是 `TB_TASK.PAYLOAD` 中的 checkpoint `runner_events`，原始约 16.8KiB。迁移后 MySQL 只保存：

```text
projection_type = RUNTIME_CHECKPOINT_EVENTS_REF
event_count
source_bytes
source_sha256
document.rel / document.sha256 / document.bytes
```

读取时必须通过 SHA256、字节数和事件数校验；校验失败直接失败，不从旧 Episode JSON 偷读。迁移脚本默认 dry-run，只有显式 `--apply` 才写入。

## 3. 生产 JSON 文件盘点

可复跑命令：

```text
python scripts/phase95_runtime_json_inventory.py --root .storyos/runtime/episodes --root episodes
```

当前盘点：

| 范围 | JSON 数 | 总大小 | MySQL 归类 | Redis 归类 | File 归类 | UNKNOWN | EXPORT_ONLY 子集 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `.storyos/runtime/episodes` | 290 | 12,013,893B | 247 | 24 | 19 | 0 | 0 |
| `episodes` 历史/兼容目录 | 1,105 | 16,072,051B | 727 | 76 | 302 | 0 | 36 |

Runtime Workspace 生产路径 UNKNOWN=0；历史/兼容目录也已从 14 个 UNKNOWN 收敛到 0，过程中未删除任何历史文件。原 14 项已逐项明确 owner：8 项归 MySQL durable contract/artifact/release/migration，6 项归 File historical/archive/system manifest。本次全量回归后复跑盘点，排除的 7,279 个文件 / 16,587,532B 属于 `_external`、`_tests` 等非生产材料；该数字会随测试夹具增减，不计入生产 Authority。`episode_performance`、`workflow_performance`、`quota_observability` 已归入 MySQL metrics projection 族，全文仍应按需要外置为 Artifact。

## 4. Writer / Reader 归属

| 文件/路径 | 归属 | 当前判断 |
|---|---|---|
| `meta/runtime-checkpoint.json`、`meta/runtime-dag-state.json` | MySQL durable projection | 历史/兼容文件，不能继续作为 authority |
| `meta/runtime/next-action.json`、`driver*.json`、heartbeat、circuit breaker | Redis hot state | Redis 模式禁止 fallback；真实 Episode 已 workspace-native |
| `meta/runtime/metrics/*.json` | MySQL metric projection | 文件是兼容/派生材料，MySQL 是读取权威；大正文不得继续内嵌 projection |
| `meta/runtime/approvals/*.json`、`releases/*.json`、`review-documents/*.json` | Artifact/document evidence | MySQL 只保存索引/引用，文件本身保留为可审计文档 |
| `meta/runtime/checkpoint-events/*.json` | Artifact/document evidence | 由 checkpoint persistence 写入，MySQL ref + SHA 读取 |
| `trace-events.jsonl`、worker raw logs | File local diagnostics | 不是 MySQL/Redis authority |
| `release-manifest.json`、`final-candidate-snapshot.json` | Export-only view | 只消费 verified snapshot，不推进状态 |
| `meta/production-queue.json` | Redis queue | 14 个真实 Episode 已 workspace-native；仅 6 个 `_tests/driver-*` 保留空的 legacy fixture |

## 5. 下一轮治理门槛

1. UNKNOWN 文件必须有明确 owner、writer、reader、生命周期和删除/保留策略。
2. 新增 JSON 必须进入批准清单，否则 strict audit 失败。
3. 任何超过 16KiB 的 JSON 必须在 CI/迁移脚本中转为 BLOB 或 Artifact reference。
4. 不能通过删除本地文件制造“治理通过”；必须先完成 MySQL/Redis 回读和 kill/restart/resume 证据。
5. 健康评分已增加 Worker 运行实例边界 + 60 分钟滑动窗口：SUCCESS/FAILED 仅统计 `max(instance_started_at, window_started_at)` 之后的终结 span；RUNNING span 始终保留用于 stuck 检测，避免重启掩盖悬挂执行。
