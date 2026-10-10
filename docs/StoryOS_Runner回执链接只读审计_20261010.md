# StoryOS Runner Durable 与模型回执链接审计（2026-10-10）

命令：`python scripts/storyos_runner_receipt_link_audit.py <episode_dir>`

这是**只读、白名单字段**诊断：分析本地 FAILED/TIMEOUT 的模型回执能否通过 `runner_request_id` 与现有 `codex_user_runner.read_task_result` 持久结果关联。输出不含 request_id、原始日志、提示词、会话内容、凭据或用户身份。查不到链接不能自动重跑模型，也不能认为后台 Runner 未保存结果；找到返回码为零的结果仍须走既有 SHA、Revision、Review Authority 校验。

初步实查《五十亩山地之后》6 条失败/超时回执：2 条含 runner_request_id 且匹配到持久结果，但返回码为非零；4 条没有该 ID（其中包含全部 3 条 PREIMAGE TIMEOUT）。这说明当前本地模型回执**不足以单独决定恢复与重试**。需要再读既有 scoped worker / Capsule / Inflight 证据和 MySQL 权威状态；不得依据此审计擅自写 Attempt 或重派生图。

补充审计：旧回执在 `runner_request_id` 缺失时若有严格 32 位十六进制 `call_id`，可尝试精确检查对应持久结果的 `request_id` 是否完全相同。即使命中，也只标为 `CALL_ID_DURABLE_HINT_UNVERIFIED`，绝不授予 ADOPT/自动重试权。此前 4 条缺少 Runner ID 的回执使用此路径未找到匹配结果；这**不证明**任务未完成或其他存储路径不存在。
