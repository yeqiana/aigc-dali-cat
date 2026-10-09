# StoryOS 原生 Codex User Runner 执行证据永久保留与校验修复（2026-10-09）

## 真实发现

在用户已登录 Codex 的交互用户 User Runner 上，`runner_health` 成功，原生 CLI 版本 `0.153.4`，已登录，允许 image/critic/scoped_step；`codex debug models` 经真正的 User Runner 返回 56 个账号目录条目，冻结的 Controller `gpt-6-luna/high` 是目录成员。但 `image_generation` 的**正式 PRIMARY 工具能力仍 UNKNOWN**，不能由登录与模型目录证明。

旧 `RunnerState.persist_result()` 保存 `task-results/<request_id>.json` 后，按 mtime 只保留 200 份，并静默删除更旧的回执；真实 Runner 此时**恰好存在 200 份**。该逻辑会让合法执行的历史证据随着新执行而消失，进而引发 `OUTCOME_UNKNOWN` 或 `FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`。

另一个错误在 `scoped_codex_worker._safe_runner_diagnostics`：`isinstance(read_task_result(id), dict)` 对空 `{}` 也返回 True，导致缺失持久化结果被报告为 `durable_result_present=true`。

## 本次代码修复

- User Runner 回执**不再按 200 文件上限自动删除**；原有 200 份不自动修复、更不变更业务 Authority。
- 使用临时文件完整 JSON 写入并 fsync，再对最终 Request ID 路径执行 atomic/no-replace hard-link；拒绝覆盖旧回执。失败明确返回 `CODEX_USER_RUNNER_DURABLE_RESULT_WRITE_FAILED` / duplicate 错误，而不是吞掉异常并返回 HTTP 200。
- `RunnerState.begin_task` 在真实模型调用前拒绝格式非法、已在执行、或已经存在持久化结果的 Request ID。Runner 持续持有 inflight ID，直到结果被安全持久化；失败不会冒充完成，也不允许自动重试 UNKNOWN。
- `_safe_runner_diagnostics` 需要完整的 `schema_version`、Request ID、returncode、输出长度以及 SHA-256 对实际 Base64 输出校验一致。空 JSON、错 ID、错 SHA、错长度、坏 Base64 均不得报告持久化存在。
- 新进程的 `health.features` 增加 `append_only_task_results` 与 `atomic_task_result_publish`，用于观察**实际生效状态**，不能把源码已更新说成旧进程已经加载。
- 运行日志、完整模型输出只作为本地证据存储，不写入文档，不上传 Git。StoryOS 不引入 OpenCodex 和视频。

## 真实历史回执备份

在原生 Runner **没有执行中任务**时，已对本地 `runtime/codex-user-runner/task-results` 的 200 个现有 JSON 完成复制和字节 SHA256 校验：
`runtime/codex-user-runner/evidence-archive/pre-retention-fix-20261009`

- 200/200 文件复制并逐个校验；共 92,933,756 bytes
- 源文件不删除、未被覆盖；备份位于同一 Runner 的本地运行目录
- `_manifest.json` 记录逐文件 SHA，不包含登录 token
- 这是**灾备副本**，不自动成为任何 Review 或 Generation Attempt 的终态 Authority；不能据此补造历史 SUCCESS

## 测试与上线约束

隔离分支已有四槽位回归 36 + 19 + 27 + 29 = **111 passed**，其中另有 8 subtests；修复 3 条测试因 direct/bridge 假环境混淆的失败后通过。增强的 `health.features` 回归会再次执行。

**关键：原生 User Runner 是已经在运行的 Python 进程，更新磁盘上的源代码不代表在线进程自动热加载。** 必须在确认 `inflight_request_ids=[]`、无真实调度生产，且确保可以恢复同一登录用户 Runner 后受控重启。重启后再次调用 `runner_health` 确认新增两个 features，才可宣布在线进程已应用防删除功能。在此之前，旧在线进程可能继续淘汰最早回执；保留上述快照并禁止高风险连续派发。

正式《五十亩山地之后》仍是 **2/25 帧**；Frame 06/24 的旧 OpenCodex `OUTCOME_UNKNOWN` 不能直接改终态、退款或重派。TEST_ONLY Phase5A Epoch2 虽 READY/0/2，但 native image capability 仍未实际 PASS。
