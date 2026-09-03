# Batch Image Runtime V1.0

## 定位

Batch Image Runtime 是 Production 执行优化层，不是新的创作权威，也不是第二状态机。

权威保持：

`Story / Storyboard / Character Contract / Resolved Frame Contract`

Batch Contract 是 Derived Execution Envelope。

## 默认批量

- Production 正文：5 张 / request
- Visual Lock：不启用 Batch
- 最后一批不足 5 张时允许 partial batch
- Provider 首个真实 Batch 同时作为 Capability Probe
- Probe/Transport 失败后回退现有 single-frame worker

## 单帧证据链

Batch 返回的每张图继续独立：

- Frame Contract SHA
- Prompt Package SHA
- RAW
- Provider Receipt
- Normalize
- Production Ledger
- Fast Scout / Final Review

## Repair Gate

内容候选失败计算：

- deviation_score: 0..100
- criticality_score: 0..100

只有两者均 >= 80 才允许 High×High 提前单帧返修。

其他内容失败在 Batch 原始生成未完成前必须 `WAIT_BATCH`。

技术失败不进入内容评分，也不消耗内容返修额度。
