# Story OS V2.5.1.1｜Forced Candidate Gate

本补丁把 V2.5.1 的 Raw Candidate Budget 从“Agent 应该调用”升级为“正式生图入口自动执行”。

- 单帧正式 Worker 自动 claim。
- Codex Logical Batch 通过单帧 Worker 自动 claim。
- Provider/Native Batch 在 Batch Worker 自动 claim。
- `codex_subscription_image.py generate-for-frame` 直接 CLI 自动 claim。
- 同一 Queue Item 技术重试复用 token，不额外扣次数。
- 技术异常 release token，不消耗候选预算。
- 真正成功生成的内容候选才占一次。
- 默认 original / repair / exception 各最多 2 次。
- 第 3 个内容候选硬 STOP，不再伪装成技术失败继续重试。
- 不修改 Story / Visual / Final Review / Release 创作规则。
