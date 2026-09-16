# Phase 9 - P9.30 Runtime Worker 存活观察者（Liveness Watchdog）

日期：2026-09-10
分支：story-platform-v3
代码基线：273c048（本批改动仍在工作树未提交）
验证方式：本机 Python 3.12.10 + redis-py 8.0.1；真实 Redis 127.0.0.1:6379（8.10.1 / AOF）；真实 MySQL 121.89.82.216:9000（8.0.46 / utf8mb4 / story_os_runtime）

凭据只从环境变量读取（STORYOS_REDIS_* / STORYOS_MYSQL_*），不写进仓库任何文件；下文与证据文件只记 host / port / database 与 password_present 布尔。

## 结论

本批关闭 P9.29 演练暴露的 HIGH finding **worker_liveness_not_critical**。

此前 Worker 失联无法被现有信号表达：Worker 进程消失后不会再跑 tick，自证型心跳失败告警也就无从发出；RuntimeHealthMonitor 只看 trace 事实，进程不在时它仍可能判 HEALTHY。结果是「Worker 不在」不会产生 CRITICAL。

本批新增一个独立于 Worker 的外部观察者：

```
Runtime Worker (可能已消失)  --写心跳-->  Redis key storyos:worker:<id>:heartbeat (TTL)
                                              ^
                                              | SCAN + 读键
                              Liveness Watchdog (独立进程, 只报不修)
                                              |
                                              v
                              CRITICAL worker_liveness_lost  (名册内失联)
```

判定模块只做纯评估不做 I/O（platform/operations/runtime_worker_liveness.py）；SCAN / 读心跳 / 事件落盘由脚本（scripts/phase9_liveness_watchdog.py）负责，因此判定口径能离线单测。

真实实例取证：同一次 Recovery Drill（2026-09-10）第三场景，Worker 被硬杀、心跳过期后观察者退出码 2 并开 CRITICAL 事件；Worker 重启后观察者退出码 0 并把同一条事件置 RESOLVED。

## 1. 背景：P9.29 finding

| 项 | 内容 |
| --- | --- |
| id | worker_liveness_not_critical |
| severity | HIGH |
| 现象 | Worker 失联本身不会产生 CRITICAL |
| 根因 | 健康模型只看 trace 事实；失联不是 trace 事实 |
| 本批处置 | CLOSED（外部观察者把失联变成 CRITICAL） |

## 2. 判定契约：platform/operations/runtime_worker_liveness.py

纯函数式模块，不 import 任何 Redis / MySQL 客户端，不落盘。

常量：

| 常量 | 值 | 说明 |
| --- | --- | --- |
| DEFAULT_PREFIX | storyos:worker: | 与 WorkerHeartbeat.PREFIX 一致 |
| HEARTBEAT_KEY_SUFFIX | :heartbeat | 键 = PREFIX + worker_id + :heartbeat |
| LIVENESS_ALERT_SOURCE | liveness_watchdog | 告警来源标签 |
| LIVENESS_LOST_REASON | worker_liveness_lost | 事件 reason |
| LIVENESS_LEVEL | CRITICAL | 失联等级 |
| STATUS_ONLINE / STATUS_MISSING | ONLINE / MISSING | 单个 Worker 状态 |

函数：

| 函数 | 作用 |
| --- | --- |
| heartbeat_key(worker_id, prefix) | 组装心跳键 |
| worker_id_from_key(key, prefix) | 从键反解 worker_id（非心跳键返回 None） |
| seconds_since(value, now) | 心跳时间到 now 的秒数；无法解析返回 None，不猜测 |
| evaluate_liveness(*, expected, observed, read_heartbeat, now) | 产出记录 / missing 集合 / CRITICAL 告警 |

判定口径（关键）：

- expected = 名册里登记过的 Worker（曾经在线过）；observed = 本次扫描仍能读到心跳的 Worker。
- missing = expected - observed，每个 missing 产生一条 CRITICAL worker_liveness_lost。
- **以 read_heartbeat 的真实返回为准**：SCAN 到键但读到 None（键已过期 / 竞态）同样算失联，不把「看到过键」当作在线。
- 只判定名册内 Worker：未登记的 Worker 即使心跳存在也不纳入观察，避免首次运行把未知进程误报为失联。

## 3. 观察者设计：scripts/phase9_liveness_watchdog.py

外部观察者，不是 Worker 内环。关键设计：

- **独立进程**：与 scripts/phase9_runtime_worker.py 解耦；Worker 全部死掉后它仍能运行并报警。
- **名册持久化**：默认 .storyos/runtime/liveness-roster.json（本地运行产物，已 gitignore）。登记走 read-modify-write，用独立 .lock 文件 + O_EXCL 跨进程互斥，超时清理陈旧锁后再试一次。
- **事件生命周期**：状态存 .storyos/runtime/liveness-incidents.json，**key = worker_id**（多个 Worker 同时失联互不覆盖）；跨运行维护 OPEN -> RESOLVED，重复出现只递增 occurrences 与 last_seen_round。
- **只报不修**：不重启 Worker、不删心跳键、不改业务数据；指标与告警只是事实。
- **可注入**：LivenessWatchdog 的 client / store / heartbeat / clock / sleep 与 run_watchdog(...) 全部可注入，离线测试不碰真实 Redis。

## 4. CLI / 退出码 / 指标 / 落盘

登记与巡检命令（PowerShell）：

```
python scripts/phase9_liveness_watchdog.py --register runtime-worker-1234
python scripts/phase9_liveness_watchdog.py --rounds 30 --interval 15
```

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| --watchdog-id | liveness-watchdog | 指标标签与事件 id 前缀 |
| --prefix | storyos:worker: | 心跳键前缀 |
| --roster | .storyos/runtime/liveness-roster.json | 名册 |
| --incident-state | .storyos/runtime/liveness-incidents.json | 事件状态 |
| --alert-log | .storyos/runtime/liveness-alerts.jsonl | 告警 JSONL |
| --metrics-file | .storyos/runtime/liveness-metrics.prom | Prometheus textfile |
| --evidence-file | .storyos/runtime/liveness-evidence.json | 运行证据 |
| --rounds | 1 | 巡检轮数 |
| --interval | 0 | 轮次间隔秒 |
| --register | 无 | 把 Worker 登记进名册，可重复 |
| --quiet | 关闭 | 只落盘不打印 |

退出码：

| 码 | 含义 |
| --- | --- |
| 0 | 无失联（EXIT_OK） |
| 2 | 有失联或仍有未消解事件（EXIT_ALERTING） |
| 3 | 环境错误：名册锁超时 / Redis 连不上 / SCAN 失败（EXIT_ENV_ERROR） |

指标（原子写，先写 tmp 再 os.replace）：

| 指标 | 含义 |
| --- | --- |
| storyos_runtime_worker_liveness_expected | 名册登记过的 Worker 数 |
| storyos_runtime_worker_liveness_observed | 本次仍能读到心跳的 Worker 数 |
| storyos_runtime_worker_liveness_missing | 本次失联的 Worker 数 |
| storyos_runtime_worker_liveness_open_incidents | 未消解的失联事件数 |
| storyos_runtime_worker_liveness_rounds_total | 本进程累计巡检轮数 |
| storyos_runtime_worker_liveness_state{status=} | 本轮存活状态 one-hot（ONLINE / MISSING） |

## 5. 真实取证：Recovery Drill 第三场景 worker_liveness_lost

同一次真实演练（Recovery Drill，2026-09-10），真实 Redis + MySQL。三轮场景汇总：

```
steps=18 failed=0 退出码=0   span 15:18:24.153558 -> 15:18:49.265146（25.1s）
worker_crash 8/8   dependency_loss 5/5   worker_liveness_lost 5/5
findings=[(worker_liveness_not_critical, HIGH, CLOSED), (recovery_decision_has_no_executor, MEDIUM, OPEN)]
```

第三场景 5 步：

| 步骤 | 结果 |
| --- | --- |
| liveness_worker_started_heartbeat_online | pid 20644，心跳 ONLINE |
| liveness_worker_killed_heartbeat_gone | 硬杀；ttl_at_kill=3；3.0s 后读不到心跳 |
| liveness_watchdog_raises_critical_for_missing_worker | 观察者退出码 2，status=MISSING，missing=[drill-recovery-worker]，CRITICAL=1，事件 OPEN |
| liveness_worker_restarted_heartbeat_online | 重启 pid 30588，心跳 ONLINE |
| liveness_watchdog_confirms_recovery_and_resolves_incident | 观察者退出码 0，status=ONLINE，同事件 RESOLVED，open_incidents=[] |

失联时指标片段（watch/missing）：

```
storyos_runtime_worker_liveness_expected{watchdog_id="drill-recovery-worker-watchdog"} 1
storyos_runtime_worker_liveness_observed{watchdog_id="drill-recovery-worker-watchdog"} 0
storyos_runtime_worker_liveness_missing{watchdog_id="drill-recovery-worker-watchdog"} 1
storyos_runtime_worker_liveness_open_incidents{watchdog_id="drill-recovery-worker-watchdog"} 1
storyos_runtime_worker_liveness_state{watchdog_id="drill-recovery-worker-watchdog",status="ONLINE"} 0
storyos_runtime_worker_liveness_state{watchdog_id="drill-recovery-worker-watchdog",status="MISSING"} 1
```

落盘证据（本地运行产物，已 gitignore，不入 Git）：

| 文件 | 内容 |
| --- | --- |
| .storyos/drill/recovery/worker_liveness_lost/watch/missing/liveness-evidence.json | MISSING，CRITICAL=1，事件 OPEN |
| .storyos/drill/recovery/worker_liveness_lost/watch/missing/liveness-metrics.prom | 失联指标（上文片段） |
| .storyos/drill/recovery/worker_liveness_lost/watch/missing/liveness-alerts.jsonl | CRITICAL 告警行 |
| .storyos/drill/recovery/worker_liveness_lost/watch/recovered/liveness-evidence.json | ONLINE，resolved=1，open=[] |
| .storyos/drill/recovery/worker_liveness_lost/liveness-incidents.json | open=[]，resolved=[RESOLVED] |
| .storyos/drill/recovery/worker_liveness_lost/liveness-roster.json | 名册 [drill-recovery-worker] |
| .storyos/drill/recovery-drill-evidence.json | 全场景 18 步证据与 findings 状态 |

## 6. 代码与测试

新增：

- platform/operations/runtime_worker_liveness.py（纯判定，无 I/O）
- scripts/phase9_liveness_watchdog.py（外部观察者 CLI）
- tests/platform/test_phase9_worker_liveness.py（18 例，全离线假 Redis + 假时钟）

修改：

- scripts/phase9_recovery_drill.py（新增 worker_liveness_lost 场景、观察者真实 subprocess 调用、跨运行证据清理、finding 状态字段）
- tests/platform/test_phase9_recovery_drill.py（覆盖第三场景，断言 18 步与 finding1 CLOSED / finding2 OPEN）

离线覆盖：命名空间往返、失联判定、SCAN 到但读不到、名册加锁合并、事件跨运行 OPEN -> RESOLVED、退出码契约、证据无凭据、main() 环境错误。

测试基线：tests/platform 由 261 增至 280（+19）；tests/system 186 passed + 16 subtests。

## 7. 边界 / 仍未完成

- **只报不修**：观察者不自动重启 Worker，不接 RuntimeRecoverySelfHealing；恢复仍由操作者执行。
- **名册是本地状态**：首次登记前不观察任何 Worker（避免误报），意味着「新部署但未登记」不告警，属显式取舍。
- **未接后端**：metrics 只落 Prometheus textfile，未接真实采集器 / 仪表盘；告警只落 JSONL，未接真实告警通道。
- **未注册服务**：观察者未注册为系统服务 / 计划任务，当前靠人工或外部调度启动。
- **单实例名册**：名册与事件状态是本机文件，没有跨主机汇总；多台主机各自维护自己的名册。
- **finding 2 未处理**：recovery_decision_has_no_executor（MEDIUM）本批不处理，保持 OPEN。
