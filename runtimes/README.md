# Story OS V2.0 Multi-Runtime

本目录只决定“当前环境如何执行”，不决定“故事应该怎么写”。

唯一创作权威仍是 `standards/制作规范_正式版.md`；
唯一 episode 阶段事实源仍是 `<episode>/meta/episode-state.json`。

自动路由，不询问用户选择模式：

```text
有可写仓库文件系统 + terminal / code execution → CODEX
否则，有 ChatGPT Work 持久工作区 / 长任务能力 → WORK
否则 → WEB
```

三个 runtime 共用同一套故事规范、真实性、M00、Capture Profile、字幕规则、回归库与 Episode State。
