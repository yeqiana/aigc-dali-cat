# Story OS V3 Phase9 Runtime Recovery Real Validation

更新时间：

2026-09-10

项目：

D:/workspace/YeQianWorkSpace/yeqian/storyOS

分支：

story-platform-v3

---

## 1. Validation Goal

验证 Runtime Recovery 从代码能力进入真实运行验证。

目标链路：

    Worker Failure
        |
    Heartbeat Timeout
        |
    Health Detection
        |
    Incident Creation
        |
    Recovery Action
        |
    State Restore
        |
    Evidence Collection

---

## 2. Recovery Components

### Worker Heartbeat

入口：

- platform/state/worker_heartbeat.py
- platform/state/redis_runtime_state_store.py

验证：

- worker registration
- heartbeat refresh（TTL = interval x 3）
- timeout detection
- 硬杀（无优雅退出）后键按 TTL 过期

### Runtime Recovery

入口：

- platform/operations/runtime_recovery_self_healing.py
 - platform/operations/runtime_recovery_executor.py（P9.31 执行层）

验证：

- failure detection
- recovery decision
 - recovery execution（RESTART_AGENT 由执行器真实落地）
- state restoration

### Incident Management

入口：

- platform/operations/runtime_alert_incident_management.py
- platform/operations/runtime_health_monitoring.py

验证：

- incident creation
- severity tracking
- recovery association

### Liveness Watchdog（P9.30 新增）

入口：

- platform/operations/runtime_worker_liveness.py（纯评估判定，无 I/O）
- scripts/phase9_liveness_watchdog.py（外部观察者，独立进程）

验证：

- Worker 失联 -> CRITICAL worker_liveness_lost
- 失联事件 OPEN -> 恢复后 RESOLVED（事件状态跨运行持久化）

### Drill Driver

入口：

- scripts/phase9_recovery_drill.py（2026-09-10 新增）
- scripts/phase9_runtime_worker.py（P9.28 常驻 Worker 载体）

---

## 3. Drill Scenario（真实执行）

环境：

    Redis   127.0.0.1:6379（8.10.1，AOF，无密码）
    MySQL   121.89.82.216:9000 / story_os_runtime（8.0.46 / utf8mb4）
    Worker  scripts/phase9_runtime_worker.py，interval=1.0s，心跳 TTL=3s

命令：

    python scripts/phase9_recovery_drill.py

场景：

    S1 worker_crash        真实子进程 -> 硬杀 proc.kill（无优雅退出）-> 观察心跳键按 TTL 过期
    S2 dependency_loss     真实子进程且 MySQL 指向被拒绝端口 127.0.0.1:1 -> 真实 CRITICAL 告警与 OPEN 事件
    S3 worker_liveness_lost 真实子进程 -> 硬杀 -> 独立观察者判失联 -> CRITICAL + OPEN -> 重启 -> RESOLVED
    S4 recovery_execution 真实子进程 -> 硬杀 -> CRITICAL RESTART_AGENT 决策 -> RecoveryExecutor 真实重启 -> ONLINE

---

## 4. 实际采集证据

一次真实执行（2026-09-10，四个场景）：

    started_at   2026-09-10T15:30:13.946261
    finished_at  2026-09-10T15:30:46.378070（约 32.4s）
    steps=24  failed=0  退出码=0
    worker_crash 8/8   dependency_loss 5/5   worker_liveness_lost 5/5   recovery_execution 6/6

### S1 worker_crash（8/8）

| 步骤 | 观测事实 |
| --- | --- |
| worker_started_heartbeat_online | pid 24276，1.016s 见到 ONLINE 心跳，TTL=3 |
| heartbeat_refreshing_before_kill | TTL 刷新到 3（满足 >=2） |
| worker_killed_without_graceful_shutdown | pid 24276，present_after_kill=true，ttl_after_kill=3（硬杀不清键） |
| heartbeat_expired_after_ttl | 3.016s 后键消失，采样 16 次 |
| liveness_signal_absent_after_expiry | heartbeat_get=null，key_ttl=-2 |
| health_alert_incident_evaluated_from_real_facts | trace_records=0 -> HEALTHY(100.0) / alert INFO(runtime_healthy) / incident RESOLVED / recovery NO_ACTION(incident_not_critical) |
| worker_restarted_heartbeat_online | 新 pid 8664，1.0s 见到 ONLINE 心跳 |
| restored_runtime_reports_healthy | exit 0，ticks 3，HEALTHY，alert_counts 全 0，heartbeat_removed=true |

### S2 dependency_loss（5/5）

| 步骤 | 观测事实 |
| --- | --- |
| dependency_failure_detected | redis OK；mysql ERROR OperationalError(2003, WinError 10061)；alert reason=mysql_unreachable |
| critical_incident_opened | inc_drill-recovery-worker_1_mysql_unreachable，status=OPEN，CRITICAL |
| worker_reports_alerting_exit_code | exit 2 |
| recovery_decision_for_critical_incident | component AGENT_RUNTIME -> RESTART_AGENT / agent_runtime_failure_recovery |
| dependency_restored_runtime_healthy | exit 0，HEALTHY；mysql OK，event_log / trace_span / artifact_index 行数全 0；alert_counts 全 0；open_incidents 空 |

### S3 worker_liveness_lost（5/5，P9.30 新增）

| 步骤 | 观测事实 |
| --- | --- |
| liveness_worker_started_heartbeat_online | pid 20644，1.0s 见到 ONLINE 心跳 |
| liveness_worker_killed_heartbeat_gone | 硬杀 pid 20644，ttl_at_kill=3，3.0s 后心跳消失，采样 16 次 |
| liveness_watchdog_raises_critical_for_missing_worker | 独立观察者进程退出码 2；status=MISSING；missing=[drill-recovery-worker]；1 条 CRITICAL(worker_liveness_lost)；事件 inc_drill-recovery-worker-watchdog_1_drill-recovery-worker status=OPEN |
| liveness_worker_restarted_heartbeat_online | 新 pid 30588，1.016s 见到 ONLINE 心跳 |
| liveness_watchdog_confirms_recovery_and_resolves_incident | 退出码 0；status=ONLINE；同一事件 status=RESOLVED；open_incidents 空 |

组件映射说明：operations 层没有 WORKER 取值，载体进程显式映射为 AGENT_RUNTIME。这是显式映射，不是隐式假设。

S3 说明：观察者是独立进程（scripts/phase9_liveness_watchdog.py），不依赖 Worker 自身 tick。Worker 在名册中登记后被纳入观察：失联即 CRITICAL，恢复即 RESOLVED。观察者只报不修，重启仍由操作者执行。

### S4 recovery_execution（6/6，P9.31 新增）

| 步骤 | 观测事实 |
| --- | --- |
| recovery_execution_worker_online | pid 26584，1.0s 见到 ONLINE 心跳 |
| recovery_execution_worker_killed | 硬杀 pid 26584，ttl_at_kill=3，3.016s 后心跳消失 |
| recovery_execution_decision_restart_agent | CRITICAL + AGENT_RUNTIME -> RESTART_AGENT / agent_runtime_failure_recovery |
| recovery_execution_executor_restarts_agent | RecoveryExecutor 状态 EXECUTED，重启出 new_pid 39248 |
| recovery_execution_heartbeat_online_after_restart | 心跳 ONLINE，old_pid 26584 -> new_pid 39248（不同进程） |
| recovery_execution_runtime_reports_healthy | 重启 Worker exit 0 |

S4 说明：RESTART_AGENT 由 RecoveryExecutor（platform/operations/runtime_recovery_executor.py）真实执行，不是操作者手动重启；执行器默认无 handler 时返回 FAILED，只有注入真实 handler 才执行。

---

## 5. Findings（如实记录）

| id | severity | 状态 | 事实 |
| --- | --- | --- | --- |
| worker_liveness_not_critical | HIGH | ✅ CLOSED（P9.30） | Worker 失联本身不产生 CRITICAL：健康模型只看 trace 事实，进程消失后 trace_records=0 反而判 HEALTHY/INFO。已由独立外部观察者关闭：失联 -> CRITICAL worker_liveness_lost + OPEN 事件，恢复 -> RESOLVED（见 S3 与 reports/phase9_runtime_worker_liveness_watchdog.md） |
| recovery_decision_has_no_executor | MEDIUM | ✅ CLOSED（P9.31） | RuntimeRecoverySelfHealing 是决策层，没有执行器。已由 RecoveryExecutor 执行层关闭：RESTART_AGENT 由执行器真实执行（S4 中 old_pid 26584 -> new_pid 39248） |

说明：worker_liveness_not_critical 记录的是「健康模型单独表达不了 Worker 失联」这一事实；该缺口已由 P9.30 观察者补齐并把 finding 置 CLOSED，但健康模型本身仍不覆盖进程层 / 依赖层。

---

## 6. Current Result

Code Validation：

PASS

Runtime Execution Evidence：

Executed（真实 Redis + 真实 MySQL，24/24 步 0 失败，退出码 0；四个场景 8/8 + 5/5 + 5/5 + 6/6）

证据落盘（.storyos/ 不入 Git）：

    .storyos/drill/recovery-drill-evidence.json
    .storyos/drill/recovery/<scenario>/run|restart|broken|restored|executed/（metrics.prom / alerts.jsonl / ticks.jsonl / evidence.json）
    .storyos/drill/recovery/worker_liveness_lost/watch/missing|recovered/（liveness-evidence.json / liveness-alerts.jsonl / liveness-metrics.prom）
    .storyos/drill/recovery/worker_liveness_lost/liveness-roster.json | liveness-incidents.json

离线回归：

    tests/platform/test_phase9_recovery_drill.py  14 例（spawn / client / heartbeat / clock / sleep / watchdog_runner 全注入）
    tests/platform/test_phase9_worker_liveness.py 18 例（假 Redis + 假时钟，不碰真实依赖）
    tests/platform/test_runtime_recovery_executor.py 7 例（执行层分派 / 异常 / 时钟，不碰真实依赖）

---

## 7. Boundary

本报告证明（真实）：

- Worker 进程硬杀后，心跳键按 TTL 过期，Redis 侧的失联可被真实观测
- Worker 失联会被独立观察者判成 CRITICAL 告警与 OPEN 事件（退出码 2），恢复后置 RESOLVED（退出码 0）
- Worker 依赖故障会通过真实探针产生 CRITICAL 告警与 OPEN 事件，退出码 2
 - 恢复决策在 CRITICAL + AGENT_RUNTIME 下给出 RESTART_AGENT
 - RESTART_AGENT 由 RecoveryExecutor 真实执行（重启 Worker 并恢复 ONLINE）
- 依赖恢复后运行期健康回到 HEALTHY，告警计数归零

本报告不证明：

- 自动执行恢复：执行器已交付并真机执行 RESTART_AGENT（finding recovery_decision_has_no_executor 已 CLOSED）；但执行器默认不接入 Worker tick 自愈，自动触发仍需 policy 决策
- 观察者自动重启 Worker：liveness watchdog 只报不修
- 名册之外 Worker 的失联：名册是本地登记表，未经 --register 的 Worker 不纳入观察（显式取舍，不是静默漏报）
- 部署形态：未注册系统服务 / 计划任务
- Metrics / Alert 后端接入：观察者与载体都只落盘，未接真实采集器与告警通道
- 依赖恢复后是否有遗留脏数据：本次只读探针不写业务数据，三表行数均为 0

---

## 8. Next Step

 - 两个演练 finding 均已关闭：Worker 失联告警（P9.30 观察者）与恢复决策无执行器（P9.31 执行器）。
 - 剩余边界是执行器自动触发（tick 内自愈）与真实 metrics / alert 后端接入，均需 policy / 环境决策。
