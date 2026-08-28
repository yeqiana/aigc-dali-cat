# WORK Runtime V2.0.2

ChatGPT Work 仍是“一次下达任务、尽量做到最终交付”的主入口。用户给 GitHub 地址、story 分支和目标任务并要求全自动后，读取 `START_HERE.md` 与本文件，连续执行 Golden Path。

Work 不需要调用本地 Codex orchestrator；当前 Work 工具可以读写工作区、调用图片工具、保存文件时就直接完成。只有登录/权限/安全确认/产品工具边界或一次内容返修仍失败时才暂停。

checkpoint 优先写仓库 `<episode>/meta/runtime-checkpoint.json`，否则写 Work workspace。自动审查记为 `delegated_auto_review`，不得伪称用户亲眼审核。能收集最终文件时直接生成交付 ZIP。
