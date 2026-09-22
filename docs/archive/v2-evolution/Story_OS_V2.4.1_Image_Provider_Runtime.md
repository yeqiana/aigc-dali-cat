# Story OS V2.4.1｜Image Provider Runtime

## 目标

V2.4.1 把 V2.4 Batch Runtime 从单一 Codex image-generation bridge 解耦为 Provider Runtime。

默认选择：

1. 存在 `OPENAI_API_KEY`：优先使用 OpenAI Image API。
2. 没有 API Key：保留 Codex Subscription 路径。
3. API 传输失败：仍由既有 Batch Scheduler 进入技术失败/fallback，不消耗内容返修额度。

## OpenAI Image API

GPT-Image-2 的 Image API 支持 `n=1..10`。

Story OS 正文默认仍使用 `images_per_batch=5`，因此一次 Batch 会发：

`n=5`

如果后续把 `images_per_batch` 调成 10，则允许：

`n=10`

### 重要语义边界

Image API 只有一个 `prompt` 字段和一个 `n` 字段。OpenAI 官方只保证一次请求返回多张图，
**不保证“输出1一定执行提示词里的Frame1、输出2一定执行Frame2”这种多语义槽位绑定**。

因此 Story OS 的：

`output_index -> Frame`

是执行约定，不是 Provider 权威保证。

所以 V2.4.1 强制保留：

- Frame Contract SHA
- 每帧 Provider Receipt
- Normalize
- Fast Scout / Final Frame Review
- Deviation × Criticality Repair Gate

如果原生 n=5 的语义槽位表现不好，应通过证据把该 Provider 模式降级，而不是伪造成功。

## API 凭据

只读取环境变量：

`OPENAI_API_KEY`

可选：

`OPENAI_BASE_URL`
`OPENAI_ORG_ID`
`OPENAI_PROJECT_ID`

任何 Secret 都禁止写入 Story OS 配置、Trace、Ledger 或 Receipt。

## Canvas

GPT-Image-2 API 自定义尺寸要求边长可被16整除。

因此：

- 4:5 Release 1080×1350 → Provider Request 1088×1360 → Normalize 1080×1350
- 9:16 Release 1080×1920 → Provider Request 1152×2048 → Normalize 1080×1920

两组均保持精确目标宽高比，不裁切。
