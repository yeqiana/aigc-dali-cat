# Story OS V3 Phase9 Production Readiness Gate

更新时间：

2026-09-10

## 1. Gate Purpose

用于评估 Phase9 Runtime Operations 是否具备进入真实 Production Validation 的条件。

目标：

Code Acceptance → Runtime Validation → Production Readiness

## 2. Current Baseline

Code Baseline:

273c048（story-platform-v3，P9.26/P9.27、Runtime Smoke、常驻 Worker 载体与 Recovery / Canary 演练改动仍在工作树未提交）

Phase8/Phase9 Code Acceptance 已完成。

测试证据：

- tests/platform: 329 passed
- tests/system: 186 passed + 16 subtests
- Total: 515 passed + 16 subtests

2026-09-10 追加：本批交付常驻 Runtime Worker 命令载体，tests/platform 由 211 增至 234（+23）。

2026-09-10 追加：本批交付真实 Recovery / Canary 演练与离线回归，tests/platform 由 234 增至 261（+27：recovery drill 13 例 + canary drill 14 例）。

2026-09-10 追加：本批交付 Runtime Worker 存活观察者（P9.30），tests/platform 由 261 增至 280（+19：存活观察者离线 18 例 + recovery drill 场景回归）。

2026-09-10 追加：本批交付 Runtime Recovery 执行器（P9.31），tests/platform 由 280 增至 288（+8：执行器离线 7 例 + recovery drill 场景回归）。

2026-09-10 追加：本批交付真实告警通道（P9.32），tests/platform 由 288 增至 296（+8：告警通道离线 7 例 + worker webhook 集成 1 例）。

2026-09-10 追加：本批交付真实 Metrics 采集端点（P9.33），tests/platform 由 296 增至 300（+4：metrics exporter 离线 4 例）。

2026-09-10 追加：本批交付常驻 Runtime 编排入口（P9.34），tests/platform 由 300 增至 305（+5：launcher 离线 5 例）。

2026-09-10 追加：本批交付 schtasks 部署脚本（P9.34.1），tests/platform 由 305 增至 310（+5：deploy 离线 5 例）。

2026-09-10 追加：本批交付自愈自动触发接线（P9.34.2），tests/platform 由 310 增至 322（+12：编排离线 6 例 + Worker 接线离线 6 例）。

2026-09-10 追加：本批交付生产归属切换执行器（P9.34.3），tests/platform 由 322 增至 329（+7：switch 离线 7 例）。

## 3. Validation Status

### Runtime Bootstrap

状态：Complete

覆盖：

- Config Loading
- Dependency Initialization
- Runtime Startup Flow

### Runtime Execution

状态：✅ Executed（Real Evidence）

目标：

- Synthetic Execution
- Agent Runtime
- Trace
- Event
- Artifact

证据：

reports/phase9_runtime_smoke_execution_evidence.md

runtime smoke  55 PASS / 0 FAIL / 0 SKIPPED，退出码 0，2122 ms（真实 MySQL + Redis）

执行事实      execution_id exec_5e02eec2e62e4974b913d203804a7795 status=SUCCESS

              trace trace_3b2acb8bc90546f597170e292f1127ac / artifact artifact_2adde73cc4c54a7b95e620a7b1fdc318

边界：以 in-process AgentRuntime 取证，证明执行链、落库与 Operations 代码路径可用；常驻 Worker 本身另见下条。

### Observability

状态：Validation Ready

覆盖：

- Trace
- Metrics
- Health
- Alert

### Recovery

状态：✅ Executed（Real Drill，2026-09-10）

覆盖：

- Worker Failure（真实硬杀）
- Heartbeat Timeout（TTL 2.813s 过期）
- Recovery Action（CRITICAL + AGENT_RUNTIME -> RESTART_AGENT）
 - Recovery Execution（RESTART_AGENT 由 RecoveryExecutor 真实重启）
- State Restore（依赖恢复后 HEALTHY）

证据：

reports/phase9_runtime_recovery_real_validation.md

scripts/phase9_recovery_drill.py  一次真实执行 13/13 步 0 失败，退出码 0（真实 Redis + MySQL）

边界：执行器已交付并真机执行 RESTART_AGENT（P9.31 关闭 finding recovery_decision_has_no_executor）；执行器默认不接入 Worker tick 自愈，自动触发仍待 policy 决策；Worker 失联已由外部存活观察者转为 CRITICAL（P9.30，见 reports/phase9_runtime_worker_liveness_watchdog.md）。

### Runtime Worker Carrier

状态：🟡 已交付（命令载体；未部署为系统服务 / 计划任务）

覆盖：

- Heartbeat（WorkerHeartbeat + TTL 刷新与退出清理）
- Dependency Probe（Redis / MySQL + 三表行数）
- Consistency Scan 调度
- Health Evaluation + Incident 生命周期
- Prometheus textfile / 告警 JSONL / tick JSONL / 运行证据落盘

证据：reports/phase9_runtime_worker_carrier.md

心跳生命周期 12 项 0 失败（真实 Redis + MySQL）；负例 MySQL 不可达产生 CRITICAL 告警与 OPEN 事件，退出码 2。

边界：未注册系统服务 / 计划任务；metrics 文本已由 P9.33 端点暴露 /metrics（真实采集实例待接）；告警通道 --alert-command 默认未配置；新增 --alert-webhook（P9.32，json / dingtalk）。

### Canary

状态：✅ Executed（Real Drill，2026-09-10）

覆盖：

- Traffic Routing（真实 sha256 bucket，1/10/50/100 全阶段）
- Promotion Gate（4 阶段 PROMOTE）
- Rollback（真实故障注入 -> ROLLBACK_TO_V2 -> production_default）
- Production Switch Decision（100% -> SWITCH_TO_V3；50% -> KEEP_CANARY）

证据：

reports/phase9_runtime_canary_simulation_report.md

scripts/phase9_canary_drill.py  一次真实执行 47/47 步 0 失败，退出码 0

边界：请求流是确定性粘性 key，不是真实用户流量；平台当前没有生产流量入口；未执行 V2 -> V3 归属切换。

## 4. Production Blocking Items

当前阻塞项：

✅ 2. Python Runtime Execution —— 已真实执行（Runtime Smoke 2026-09-10）
✅ 3. Redis Instance Validation —— 已接入验证（127.0.0.1:6379，8.10.1，AOF aof_enabled=1）
✅ 4. MySQL Repository Validation —— 已接入验证（121.89.82.216:9000 / story_os_runtime / 8.0.46 / utf8mb4）
🟡 1. Real Runtime Environment —— 部署脚本已交付（scripts/phase9_runtime_deploy.py，2026-09-10，dry-run 验证），注册计划任务仍待授权
🟡 5. Real Metrics Pipeline —— /metrics 采集端点已交付并真机 E2E 验证（P9.33）；真实 Prometheus / Grafana 采集实例待接
🟡 6. Real Alert Channel —— WebhookAlertChannel + 本地接收器已交付并真机 E2E 验证（P9.32）；真实外部端点待操作者提供 URL 接入
🟡 7. Production Ownership Switch —— 切换执行器已交付（P9.34.3，dry-run 验证），执行切换待授权
🟡 8. Recovery 自动执行 —— 自动触发已接线（--auto-recover 默认关闭，P9.34.2），开启待授权

## 5. Decision

当前：

Phase9 Code Accepted

Phase9 Runtime Validation Executed（Code Path Green；常驻 Worker 载体已交付；Recovery 与 Canary 已真实演练取证；Metrics 采集后端与 Alert Channel 仍待接入）

Production Ownership Switch: Pending

2026-09-10 更新（Worker 载体）：常驻 Runtime Worker 命令载体已交付并真机取证（reports/phase9_runtime_worker_carrier.md）。第 1 项由「缺载体」收敛为「载体已交付、未部署」。

2026-09-10 更新（演练）：新增真实 Recovery Drill 与 Canary Drill，两项从 Validation Ready 变为 Executed。第 5 / 6 项（真实 Metrics 后端、真实 Alert 通道）仍待接入；新增第 7 / 8 项为演练暴露的诚实边界。

Phase10 Enterprise Runtime Platform 暂缓，等待 Production Readiness Gate 通过。

2026-09-10 更新（存活观察者）：新增外部 Worker 存活观察者（P9.30），把名册内 Worker 失联转为 CRITICAL worker_liveness_lost；Recovery finding worker_liveness_not_critical（HIGH）已 CLOSED。第 8 项（Recovery 自动执行）仍 OPEN。

2026-09-10 更新（恢复执行器）：新增 RecoveryExecutor（P9.31），RESTART_AGENT 由执行器真实执行（Recovery Drill S4，old_pid 26584 -> new_pid 39248）；finding recovery_decision_has_no_executor（MEDIUM）已 CLOSED。执行器默认不接入 Worker tick 自愈，自动触发仍待 policy 决策。

2026-09-10 更新（真实告警通道）：新增 WebhookAlertChannel（json / dingtalk）与本地接收器，Worker 挂载 --alert-webhook；真机 E2E 证明 CRITICAL mysql_unreachable 经 webhook 送达本地接收器。第 6 项由「缺通道」收敛为「通道已交付并本地端到端验证，真实外部端点待接」。

2026-09-10 更新（真实 Metrics 端点）：新增标准库 Metrics 采集端点（P9.33），把 Worker textfile 以 Prometheus exposition 暴露在 /metrics 并提供 /healthz；真机 E2E 证明 HEALTHY Worker 的 60 行指标可经 HTTP 拉取。第 5 项由「缺 metrics 后端」收敛为「采集端点已交付，真实 Prometheus 采集实例待接」。

2026-09-10 更新（常驻编排入口）：新增 RuntimeLauncher（P9.34），把常驻 Worker + Metrics 端点作为单一可部署单元统一启动、统一优雅退出，fail-fast 不自动重启；真机 E2E 证明 /metrics 200（60 行）+ /healthz 200，launcher 优雅退出码 0。第 1 项由「载体已交付、未部署」收敛为「可部署单元已交付，系统服务注册仍待授权」。

2026-09-10 更新（部署脚本）：新增 schtasks 部署脚本（P9.34.1），install / uninstall / status 默认 dry-run 只打印命令，--apply 才执行；dry-run 命令构造正确，status --apply 只读查询确认任务当前未注册。第 1 项由「可部署单元已交付、注册待授权」收敛为「部署脚本已交付，授权后一条命令即可注册」。

2026-09-10 更新（自愈自动触发）：新增自愈编排 runtime_auto_recovery（P9.34.2），Worker 挂 --auto-recover 与 --restart-agent-command（默认关闭）；真机 E2E 在真实 Redis 下注入 agent/workflow 失败触发 CRITICAL runtime_unhealthy，自动执行 RESTART_AGENT 且 auto_recovery_result 落盘 EXECUTED。第 8 项由「tick 内自动触发未开启」收敛为「自动触发已接线（默认关闭），开启待授权」。

2026-09-10 更新（生产归属切换）：新增 runtime_primary_persistence + phase9_production_switch（P9.34.3），status / switch 默认 dry-run，--apply 才落盘 meta/runtime/runtime-primary.json；dry-run 确认当前 V2_RUNTIME，切换动作正确但未执行。第 7 项由「未执行归属切换」收敛为「切换执行器已交付，执行切换待授权」。
