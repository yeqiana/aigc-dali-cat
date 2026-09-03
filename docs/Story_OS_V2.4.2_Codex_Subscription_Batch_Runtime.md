# Story OS V2.4.2｜Codex Subscription Batch Runtime

## 为什么做这个小版本

用户使用 ChatGPT Plus / Codex 订阅，没有 OpenAI API Key。

V2.4.1 的 OpenAI Image API `n=5` 路径因此不会启用；当前 Codex image-generation bridge
又没有原生 `n/count` 参数。

V2.4.2 不再把这件事当成“Batch 不可用”，而是正式支持：

`1 个 Story OS Batch → 5 个独立 Codex 单图 Worker 并行`

这叫 **Logical Batch / Fan-out**。

它不是：

`1 Provider HTTP Request → 5 Images`

所以 Capability Evidence 必须明确：

- logical_batch = true
- native_multi_image = false
- single_http_request = false

## 默认并行策略

- Batch Size：5
- 初始最大 Codex 图片并行：5
- 自适应：5 → 3 → 1
- 一个任务完成，线程池自动补下一个
- 技术失败只重试失败帧
- 已成功帧禁止因为同批其他帧技术失败而重新生成

## Review Barrier

生成 worker 在 Logical Batch 中只负责生图，不提前启动 Fast Scout。

等本批原始 5 个 worker 都 terminal 后：

- 成功帧进入 Review
- 技术失败走技术重试
- 内容失败进入 Deviation × Criticality Gate

因此保持：

`deviation >= 80 AND criticality >= 80`

才允许 High×High 紧急单帧返修。

## Plus / Codex

这条路径不要求 `OPENAI_API_KEY`。

它使用本机已登录的 Codex CLI / ChatGPT Codex 订阅能力。

底层实际仍是 5 个独立 image_generation 调用，因此会消耗对应 Codex/ChatGPT 套餐使用量。
