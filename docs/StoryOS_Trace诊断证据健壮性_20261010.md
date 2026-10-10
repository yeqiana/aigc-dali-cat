# StoryOS Trace 诊断结果稳健性（2026-10-10）

Trace 是诊断，不是 Episode Stage Authority。流式摘要的单一异常事件（非法数字、NaN、Inf、负时间）过去可能使汇总中毒或异常退出。本轮只对统计用的 `elapsed_ms` 做非负有限数过滤，无效时按零毫秒统计并保留原事件数和状态数，不写回原始回执/事件。

MySQL 模式仍只从 `runtime_fact_store.load_trace_events` 读取，不允许因查询失败而采用本地 JSONL 作为权威。产物仍标记 `diagnostic_only: true`、`stage_authority: false`。这不是提高模型速度的实验，不得算作生产性能增益。
