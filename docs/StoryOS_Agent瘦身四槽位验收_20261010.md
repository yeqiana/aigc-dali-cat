# StoryOS Agent / Runtime 瘦身四槽位（2026-10-10）

> 开发分支：`feature/storyos-agent-slim-20261010`。本文件记录可复测的增量优化；未授权正式生产或 MySQL/Attempt 改写。

## 改造原则

- 图片生成、Review Authority、Generation Attempt、Revision、跨 Episode 共享 5 张容量、SHA-bound 证据和 Snapshot 一律保留。
- 不进行影子审核到正式审核的无证据切换；不在业务链增加新的 Agent、Gate 或状态机。
- 窄模型任务只提供锁定的局部输入；任何未验证输入仍 fail closed。
- 已确定的持久化结论不得因重复进程恢复而无故改写缓存时间戳。
- Trace 是诊断数据；进程内冻结配置仅解析一次。
- 性能提升需要对同等 Episode 的真实完整生产链复测，禁止把历史耗时直接当作新实测速度。

## 四槽位

1. **Agent Context**：Caption 像素审阅指令限定为附件和冻结字幕，对应进程以当前 Episode 为 `-C` 工作目录，输出用绝对路径；正式 Review Authority 未改变。
2. **Review Hot Path + Cache**：Caption 无字幕分支减少一次 frame_records 全量扫描，ensure() 复用 dirty_frames 已获得的 SHA 帧索引，降低重复 Authority/文件读取；Critic Cache 仅在相同证据 SHA/路径/决定时避免重复落盘。缓存不是审核权威。
3. **Runtime Trace**：对进程固定 Trace Policy 执行一次 JSON 解析，避免每个嵌套属性重复读配置。
4. **回归和文档**：运行针对性 pytest；新旧行为差异需保持跨 Episode 容量、数据库/Revision 契约兼容，不直接调整已锁 Episode。

## 验收要求

`python -m pytest -q tests/system/test_storyos_agent_slimdown.py`

再运行现有 Caption / Critic Cache / Runtime Trace 的相关测试。此分支未进行付费模型生产；正式生产前仍需独立 Preflight。
