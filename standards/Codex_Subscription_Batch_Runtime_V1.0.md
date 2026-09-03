# Codex Subscription Batch Runtime V1.0

## 定位

这是 Story OS 的逻辑 Batch 执行层。

对用户和 Story OS：
`1 Batch = 5 Frames`

对底层 Codex：
`5 个独立单帧 image_generation worker 并行执行`

它不是 OpenAI Image API 的 native `n=5`，也不得把它伪装成单次 Provider 多图。

## 目标

- 不需要 OPENAI_API_KEY；
- 使用 ChatGPT Plus / Codex 登录态；
- 默认一批 5 帧；
- 默认最多 5 个 Codex 单图 worker 同时在途；
- 任一 worker 完成后立即收集结果；
- Production Ledger 仍由 Scheduler 单写；
- 单个技术失败只重试失败帧，不重生已经成功的帧；
- 内容返修仍受 Deviation × Criticality + Batch Barrier 控制。

## 证据语义

Capability 必须记录：

- provider = codex_subscription
- transport = codex_subscription_parallel_fanout
- native_multi_image = false
- logical_batch = true
- single_http_request = false

这样不会把逻辑 Batch 错记成 Provider 原生多图。
