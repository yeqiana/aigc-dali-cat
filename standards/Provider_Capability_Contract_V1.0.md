# Provider Capability Contract V1.0

Provider Capability Contract 只描述真实图像 Provider / Transport 能保证什么、不能保证什么。

正式生产区分三层：
1. requested_canvas：Story OS 请求目标。
2. provider_raw_canvas：Provider 实际返回 RAW 尺寸。
3. release_canvas：NP01 标准化后的正式尺寸。

当前 GPT-Image-2 桌面/Codex 内建图像通道：
- 接收目标画布意图；
- 不声明 exact RAW canvas guarantee；
- RAW 尺寸必须本地测量；
- Release Canvas 仍必须精确符合 Episode 锁定画布。

不变量：
- RAW 非 exact 不自动重生图；
- 先检查 ratio_delta；
- NP01 自动阈值内允许无裁切 Lanczos 标准化；
- Provider Receipt 是 Evidence，不是 Authority；
- Production Ledger 只能由单写入者绑定 Receipt。
