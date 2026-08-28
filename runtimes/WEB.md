# WEB Runtime V2.0.1

普通 ChatGPT Web 的目标仍是：尽量连续自动执行 + checkpoint 续跑。

用户明确“全自动”后，不在三张校准、四张视觉准入、Batch 等正常节点反复询问继续。只要当前会话还能调用图片/文件工具就继续；真正遇到产品工具边界时，记录 `last_completed / next_action / locked_frames / failed_frames`，下一轮直接恢复。

GitHub 可写时使用 `<episode>/meta/runtime-checkpoint.json`；只读时在对话中保持同 schema。无法实际收集全部图片二进制时，不得谎称已经生成 ZIP。
