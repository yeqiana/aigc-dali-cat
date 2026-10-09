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

## 在线 Runner 受控切换及端到端验收（2026-10-09）

**新代码已实际部署，不再是待重启状态。** 先修复 `scripts/start_codex_user_runner.ps1`：启动后只接受与 **新进程 PID** 严格相等、loopback host 为 127.0.0.1、port 有效的 `endpoint.json`，不把旧端点文件误当新 Runner 启动证明。主 checkout 与安全集成分支均通过 PowerShell Parser（0 syntax errors）和 Git whitespace 检查。

部署时先经带认证的现有 Runner 健康接口复核 `inflight_request_ids=[]`，确保交互用户会话 Active、正式生图进程 0、200 份执行回执备份清单存在，然后只停止属于该交互用户 Session 1 的旧 `codex_user_runner.py serve` 进程 PID **18716**；使用原 `StoryOS-Codex-User-Runner` Windows 交互登录计划任务启动新进程。新 PID **40460**，仍属于 Session 1。启动脚本已经正确验证新进程 endpoint。

新进程经正式 `runner_health` 实测：`status=ok`、`codex_auth_present=true`、`interactive_user=true`、`inflight=0`，且 `features` **同时包含** `append_only_task_results` 和 `atomic_task_result_publish`。没有移动/覆盖 Codex 登录凭证。

进一步通过**真实 User Runner（非模拟）**派发只读 `smoke` 任务 `codex --version`（不调用模型），新请求返回 `returncode=0`。按同一 Request ID 读回新增的持久化回执，完成 Base64/字节数/SHA256 核对；从 **200 → 201** 个真实回执，确认原 200 个文件全部仍存在且字节长度不变，新回执持久化成功。新增真实任务不属于 image Generation、Review 或 Episode Stage Authority，不能拿版本查询结果代替原生图片工具 PRIMARY 能力验收。

本次切换包含两次**执行前失败、未停止原进程**的守卫：一次 PowerShell 到 Python 的引用参数解析错误，一次活跃 Runner 输出日志被锁导致无法校验日志副本。后续使用经认证的本地健康接口完成执行前检查，并保留先前复制的日志；不声称其是完整字节快照。真正的 200 份执行回执备份独立完成哈希校验。

**仍需独立推进**：TEST_ONLY Phase5A Epoch 2 已准备 0/2，但原生生图工具的实际 Capability 尚无 PRIMARY 成功证据。正式《五十亩山地之后》Frame 06/24 的旧 OpenCodex `OUTCOME_UNKNOWN` 不可因本次 Runner 切换而退款或重派。用户不需要重新登录。

## 测试与上线约束

隔离分支已有四槽位回归 36 + 19 + 27 + 29 = **111 passed**，其中另有 8 subtests；修复 3 条测试因 direct/bridge 假环境混淆的失败后通过。增强的 `health.features` 回归会再次执行。

**已按上线门禁完成受控重启和实测。** 更新磁盘源码并不自动热加载旧 Python 进程；本次先确认 `inflight_request_ids=[]`、正式图片任务为 0，再通过原交互用户计划任务重启，并从在线 `runner_health` 验证新增两个 features。随后真实 `codex --version` 只读 smoke 使回执数从 200 增至 201，历史 200 份仍在。因此**Runner 回执保留代码现已在线生效**；这与图片工具 Capability 是否可用、旧 Attempt 是否可核销是不同门禁。

正式《五十亩山地之后》仍是 **2/25 帧**；Frame 06/24 的旧 OpenCodex `OUTCOME_UNKNOWN` 不能直接改终态、退款或重派。TEST_ONLY Phase5A Epoch2 虽 READY/0/2，但 native image capability 仍未实际 PASS。
