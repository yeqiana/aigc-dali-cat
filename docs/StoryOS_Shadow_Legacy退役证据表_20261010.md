# StoryOS Shadow / Legacy 退役证据表（2026-10-10）

此表只用于瘦身治理，不是生产 Gate，不修改 `config/storyos.yaml`，不触发数据迁移或付费模型。

## 实际配置分组

- 已正式接管：Character Finalize、Visual Narrative Prepare（Production true / Shadow false）。保留真实技术故障时的 Legacy fallback；除非有真实 Canary 与回滚测试，不得强删。
- 仅影子运行：World Prepare、Story Semantic Critic、PREIMAGE Semantic Critic、Final Semantic Critic（Production false / Shadow true）。**不得直接删掉正式旧 Review**，需要确认影子开销和真实对照样本。
- P4 Capability Router：Production true / Shadow true，保持 Scheduler 唯一 dispatch owner，不能在此轮删除路由护栏或切换执行器。
- P5 Guardian Facade：Production false / Shadow true，目前只给诊断建议，不能赋予新恢复/Retry Authority。

## 退役验收序列

1. `python scripts/storyos_shadow_inventory.py --json` 只读打印当前清单（不会执行模型）。
2. 分别采集目标组件的调用数、额外模型 Token、维护成本以及真实对照 Review，不能只凭 `shadow_enabled` 判定用量。
3. 若同一个 Review 结论同时由 Legacy 与 Shadow 生成，先确定正式 Authority 与 SHA 绑定来源；不能因为影子 PASS 绕过正式 Review。
4. 候选退役必须有单独的配置变更 PR、明确回滚路径、回归和真实 Episode Canary；本轮只输出可核对清单。
5. 不移除多 Episode 共享 5 图片全局许可证、Revision/Attempt fencing、Review Authority、可恢复的 Receipt、正式 Gate。

## 安全边界

此轮刻意不更换 MySQL/Redis、不改动态生产开关、不清理现有 worktree、不迁移任何 Episode。原生 Codex 与 OpenCodex 禁用原则不变。
