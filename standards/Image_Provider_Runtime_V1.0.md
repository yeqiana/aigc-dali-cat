# Image Provider Runtime V1.0

Image Provider Runtime 是 Story OS 的执行适配层。

它只回答：

- 当前请求应该走哪个图片 Provider；
- Provider 是否支持 native multi-image；
- Provider 请求尺寸/输出数量/Request ID 等执行证据；
- 技术失败如何回落。

它不拥有：

- Story；
- Storyboard；
- Character Contract；
- Frame Contract；
- Episode Stage。

## Provider 顺序

1. `OPENAI_API_KEY` 存在时，OpenAI Image API 可作为正式 Batch Provider。
2. 无 API Key 时，Codex Subscription 保持兼容路径。
3. Secret 永远不写入仓库或 Episode Evidence。

## Multi-image

GPT-Image-2 Image API 的 `n` 支持 1..10。

Story OS 默认 5 帧 Batch 使用 `n=5`。

`output_index -> Frame` 是 Story OS 的执行映射约定，必须经过逐帧审核，
不能把 Provider 返回顺序当成新的创作权威。
