# WEB Runtime V2.0

普通 ChatGPT Web 的目标是：**尽量连续自动执行 + 永不失忆 + checkpoint 续跑**。

规则：
- GitHub URL + story 分支后先读 `START_HERE.md`。
- 用户说“全自动”后，不在正常节点反复询问是否继续。
- 只要当前会话还能继续调用图片/文件工具，就继续生产，不人为停在 3 张或 10 张。
- 每完成关键节点更新 checkpoint。
- 产品工具或文件收集能力确实阻断时，记录 `last_completed / next_action / locked_frames`；下一轮直接恢复，不要求用户复述故事、画风、已锁帧。
- GitHub 可写则保存 `<episode>/meta/runtime-checkpoint.json`；只读时在当前会话保留同结构 checkpoint。
- 无法把全部图片文件集中成 ZIP 时不得谎称 ZIP 已完成。

runtime=`WEB`。
