# StoryOS 多 Episode 正式图片并发：本机共享硬上限（2026-10-09）

## 为什么需要

StoryOS 原有 `production.max_inflight_images=5` 只约束**单个** Episode Scheduler。直接并发启动两个 Episode，之前有可能形成 5+5=10 个同时在途的真实图片任务。

本轮代码在主图片 Worker、原生批量 Worker 和最终 Provider Dispatch Gateway 三层实行同一个**本机 Git 仓库级别、跨进程与跨 Worktree 共享**的 5 图片名额硬上限。每部 Episode 的队列锁、状态、MySQL Attempt 与 Review Authority 仍然分别管理，不改变历史账本，不自动重试 `OUTCOME_UNKNOWN`。

## 现在支持什么

- 不同 Episode 的独立 Scheduler/Driver 可以同时运行；它们在发图片前竞争同一个总容量池，而非各自拥有 5 个名额。
- 单帧占 1 个名额；原生 n 图片批量占 n 个名额；Codex 逻辑批量通过每个单帧 Worker 分别占位。
- Gateway 也会校验名额；Worker 内再进入 Gateway 时重用先前持有的容量，不会双重计数。
- 没有可用名额时，等待在任何图片 Generation Attempt 预约之前；若超过等待上限，阻止本次派发，并以 `GLOBAL_IMAGE_CAPACITY_BUSY` 报错（没有把它当成 Provider 终态）。
- 锁用 Windows/POSIX 原生文件锁；进程退出/崩溃后由系统释放，不根据过期时间擅自解锁仍在运行的图片任务。
- 不接触模型凭据，不需要启动 OpenCodex，不产生视频。

只读容量快照：

```powershell
python episodes/_system/global_image_capacity.py status
```

报告的占用数字是诊断快照，不是 MySQL Attempt Authority。

## 安全边界及下一阶段

1. **当前只是同一台机器、同一个 Git Common Directory 下的各 Worktree。** 不保证多个互不相关的 Git 克隆、不同电脑、不同 MySQL 服务可安全共享；需要跨主机时另做 MySQL/Redis 原子租约和 fencing，未验收前禁止多主机并发调度。
2. **共享硬上限不是公平调度器。** 两个 Episode 可同时生产且合计最多 5 个图片，但先启动的 Episode 可能暂时占满全部名额。正式做到跨 Episode 轮询、优先级、每 Episode 配额及统一控制台，还需要后续的中心多 Episode 编排与公平队列。
3. `GLOBAL_IMAGE_CAPACITY_BUSY` 是调度容量问题，不是图片失败/允许消费新的 Attempt 的依据；不能以此绕过原有 Provider Receipt、Review Authority、失败恢复和预算保护。
4. 不得用多个 Worktree 各自启动相同的 Episode 来绕过 Episode Owner Lock；同一 Episode 仍必须只有一个正式 Writer/Driver。
5. 本轮是代码与 hermetic 回归，**未开启真实双 Episode 生图、未修改 MySQL、未部署或热替换生产服务**。正式启用前需要全量回归、CI、服务停机窗口/重启与真实双 Episode Canary。
6. 《五十亩山地之后》本身仍被 PREIMAGE、逐帧 Frame Contract、Visual Lock 和旧 UNKNOWN Attempt 的生产门禁限制；多 Episode 资源层不能给它解锁。《未交的答卷》已经人工完成，不参与任何新的生产。

## 验收矩阵

- 两个真实 OS 进程分别占 2 与 3 个名额，第三方第六帧拒绝，释放后可再次领取。
- 一个占满 5 个名额的进程崩溃/被终止后，其他 Episode 仍能重新领取全部 5 个名额。
- 原生 batch=2 在其他 Episode 已持有 4 时拒绝，且 Provider 不调用。
- Gateway 无论从独立入口还是 Worker 嵌套进入，都执行容量校验。
- 历史 Attempt Authority 回归不能因容量变化而改变终态、退款或伪造成功。

**不能据此宣布多 Episode 生产服务已正式上线。**

## 正式多 Episode 入口

新的 `scripts/storyos_multi_episode.py` 复用 StoryOS 原生 `runtime_driver.launch/status`，不会为任何 Episode 制造新 Authority；不同 Episode 各持有自己的 Driver Owner Lock、队列和恢复记录。启动一个已经运行的 Episode 会跳过，不会双开；任何 Episode Owner 状态不明都会阻断整组新启动。

只读计划/状态示例（请替换第二部作品为实际 Episode 路径）：

```powershell
python scripts/storyos_production_env.py scripts/storyos_multi_episode.py plan --episode "episodes/00_独立篇/05_五十亩山地之后" --episode "episodes/00_独立篇/06_第二部作品"
python scripts/storyos_production_env.py scripts/storyos_multi_episode.py status --episode "episodes/00_独立篇/05_五十亩山地之后" --episode "episodes/00_独立篇/06_第二部作品"
```

只有在两个 Episode 各自全部通过正式生产门禁、最新多 Episode 代码完成部署后，才允许操作者执行真实启动命令，且必须带明确授权：

```powershell
python scripts/storyos_production_env.py scripts/storyos_multi_episode.py start --episode "episodes/00_独立篇/05_五十亩山地之后" --episode "episodes/00_独立篇/06_第二部作品" --ack-real-production
```

这是未来使用说明，**不是授权现在运行命令**。当前两个 Episode 路径中第二个只是示例，不存在时必须拒绝执行。该命令会分别启动正式 Driver，不能撤销已经成功启动的其他 Episode；失败必须保留各 Episode 的真实状态并报告部分成功。

公平性仍待加强：跨 Episode 独立 Driver 共享硬上限，不代表有严格先来先服务或动态配额。正式多作品生产上线必须完成 CI、停机部署、双 Episode Canary 和运维监控验收。
