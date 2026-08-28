# WORK Runtime V2.0

ChatGPT Work 是“一次下达任务、尽量做到最终交付”的主入口。

用户给 GitHub 地址、story 分支和目标任务并要求“全自动”后：
- 先读 `START_HERE.md`，按权威索引最小读取必要规范。
- 不把任务降级成只给提示词；当前 Work 工具能直接完成的就直接完成。
- 先三张真实性校准，再四张视觉准入，再 Batch。
- 每帧最多一次内容返修。
- 不在每张图后问“继续吗”。
- 只有登录、权限、安全确认、工具限制或不可消解硬冲突才暂停。
- 能生成最终文件/ZIP时直接交付。

checkpoint 优先写仓库 `<episode>/meta/runtime-checkpoint.json`；仓库不可写时写 Work workspace。
自动审查记为 `delegated_auto_review`。
