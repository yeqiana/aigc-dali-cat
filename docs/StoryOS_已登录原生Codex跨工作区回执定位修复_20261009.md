# StoryOS 已登录原生 Codex User Runner 跨工作区回执闭环（2026-10-09）

## 生产事实（现场实测）

用户本机原生 Codex 已登录，不需重新登录或使用 OpenCodex/API 代理。

通过正式 `codex_user_runner.bridge_required()/runner_health()` 在安全集成工作区实测：

- `bridge_required=true`，`transport=user_runner`，`status=ok`
- 交互用户为 `RENRP\\yeqian`，`interactive_user=true`
- 交互用户 `codex_home_accessible=true`、`codex_auth_present=true`、`codex_config_present=true`
- CLI 版本 `codex-cli 0.153.4`，Runner 实际 PID 可用，允许 `image`、`critic`、`scoped_step` 等任务
- 已登录 Runner 的历史 `task-results` **200 个文件按真实 ID 读取匹配 200 个**，全程只读；检查只输出计数/返回码分布，不读出模型文本、不打印 token、不发生 Provider 调用
- 这些历史任务完成或失败的执行结果不等同于任何 StoryOS 图片 / Final Semantic 业务验收通过。不存在授权把其它历史 Request ID 赋给旧未知 Attempt 的途径

## 精确问题

在 Git worktree `.worktrees/storyos-main-integration-20261009` 中，`endpoint_path()` 已根据可信的 `.git/worktrees` 指针正确定位主仓库的**同一个交互用户** Runner endpoint。

但旧 `read_task_result(request_id)` 固定从本 worktree 自己的 `runtime_dir()/task-results` 读取，与真正执行任务的 Runner 持久化存储不一致。造成：

- 已成功完成的 native Codex/Final Semantic 结果从隔离 worktree 查询仍显示缺失
- 下游可能把真实已调用的 Review 误判为 `FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`
- 再次执行的恢复策略因查不到真实结果而永久停滞，不能安全重试也不能合法完成 Review

## 实现

保留 `task_result_path()` 作为该进程/direct server 自身写入路径；仅修正**读回**：

1. 当 `bridge_required()` 为真时，以已信任且已证实属于**同一 Git 仓库**的 `endpoint_path().parent` 为唯一真实 Runner 持久化目录；
2. 若 endpoint 不存在或 Runner 结果不存在，返回空证据，**不回落读取本地 worktree 的假结果**；
3. 只有 `request_id` 和结果文件内部 ID 完全一致才返回结果；
4. direct 模式继续使用本 worktree 的原有路径；拒绝目录穿越与其他仓库的 endpoint；
5. 不复制 `auth.json`、Runner token，也不修改已有 Request ID、Review Authority、图片 Generation Attempt。

## 四槽位回归

| 槽位 | 测试 | 结果 |
|---|---|---|
| A | worktree 可信回执、排除伪本地结果、Runner 路由 | 36 passed |
| B | durable Final Semantic 执行证据、Review 身份绑定 | 21 passed, 2 subtests |
| C | native image only、原生 Controller/Phase5A 合同 | 36 passed |
| D | 正式 UNKNOWN、Provider 回执、Scheduler 安全 | 24 passed |
| **合计** | | **117 passed + 2 subtests** |

## 生产边界

- TEST_ONLY Epoch 2 仍是 `READY`、0/2 Attempt，实际 image tool capability 仍 `UNKNOWN`。不因为本地 `codex_auth_present=true` 就伪造图片工具通过。
- 《五十亩山地之后》仍是 `STORYBOARD_LOCKED`、2/25 正式图片；Frame 06/24 的旧 `OUTCOME_UNKNOWN` 必须依原始 Provider 证据核销，不新建重复调用。
- 正式 MySQL 不写入、历史回执不改写、无新模型调用、无 OpenCodex、无视频。
- 主 checkout 未经重置和强制合并，采用备份 + 精确差异同步。隔离分支三个外来 dirty 文件继续保护。
