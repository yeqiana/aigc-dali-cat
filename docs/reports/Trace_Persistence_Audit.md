# Trace Persistence Audit

日期：2026-09-21

## 证据

`platform/repository/trace/mysql_trace_repository.py` 存在真实 `INSERT INTO TB_TRACE_SPAN ... ON DUPLICATE KEY UPDATE`，读侧有 `get/list_all/iter_all`。`TraceObserver.start()` 先保存 RUNNING，`AgentRuntime._finish_trace()` 通过同一 Observer 保存终态。

## 发现与修复

此前 `platform/api/default_app.py` 创建 AgentRuntime 时没有注入 TraceObserver repository，导致默认 API 链路只读 AgentRuntime 内存，`TB_TRACE_SPAN` 不会被该入口写入。现在默认 composition 明确注入 `MySqlTraceRepository(MySqlConnection())` 和 `trace_sink=trace_observer.save`。

## 边界

- 不从 `TB_EVENT_LOG` 回填 `TB_TRACE_SPAN`。
- 不改变 `TB_EVENT_LOG` 的 Event Authority 或写入协议。
- JSONL / RuntimeAdapter 既有兼容路径保留；本次只补默认 Platform Agent Runtime 的 MySQL 接线。
- MySQL 不可用时不静默伪造 Trace；真实调用会暴露连接错误。

## 物理主键说明

当前 schema 的物理主键是 `SPAN_ID`，而 Trace identity 逻辑上由 `(TRACE_ID, SPAN_ID)` 表示。生成器使用全局 UUID 片段保证 span_id 全局唯一；复合主键迁移仍是架构决策，不在本次无现场数据验证的收口中执行。
