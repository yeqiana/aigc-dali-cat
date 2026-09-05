# WEB Runtime

当前 Story OS 版本以根目录 `story_os_manifest.json` 为准。

普通 ChatGPT Web 的目标仍是：尽量连续自动执行 + checkpoint 续跑。V2.6.1 起 WEB 与 WORK 一样属于产品运行时，**不得因为本机存在 codex.exe 就静默启动本地 Codex**。

用户明确“全自动”后，不在四张 Visual Lock 准入、Batch 等正常节点反复询问继续。只要当前会话还能调用图片/文件工具就继续；真正遇到产品工具边界时，记录 `last_completed / next_action / locked_frames / failed_frames`，下一轮直接恢复。

GitHub 可写时使用 `<episode>/meta/runtime-checkpoint.json`；只读时在对话中保持同 schema。Concept / Story 独立评审使用 `WEB_ISOLATED` provenance。图片优先使用产品图片能力；无法把真实图片文件写回工作区时必须返回 `HOST_ACTION_REQUIRED`，Checkpoint 记为 `HOST_WAIT`（正常宿主握手，不计作故障 BLOCKED），禁止回退 Codex Subscription。无法实际收集全部图片二进制时，不得谎称已经生成 ZIP。
