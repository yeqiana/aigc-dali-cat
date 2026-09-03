# Story OS V2.4 Batch Image Runtime

V2.4 将正式图片生产从单帧请求升级为 Batch Runtime。

默认：
- 5 images / one image_generation call
- 最多 2 个 Batch 并行（首次 Capability Probe 前为 1）
- Visual Lock 保持 1+3
- Batch Provider 不支持时回退单帧
- 每帧证据链完全独立

Repair Gate：
- Deviation >= 80
- Criticality >= 80
- 两者都高：允许 High×High 紧急单帧返修
- 其他内容失败：等待当前 Batch 原始生成完成后再判断
- 技术失败不计内容返修

Batch 是 Runtime Evidence，不是 Episode Stage。
