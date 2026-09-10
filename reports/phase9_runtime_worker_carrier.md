# Phase 9 - P9.28 常驻 Runtime Worker 载体

日期：2026-09-10
分支：story-platform-v3
代码基线：273c048（本批改动仍在工作树未提交）
验证方式：本机 Python 3.12.10 + redis-py 8.0.1 + pymysql 1.4.6；真实 Redis 127.0.0.1:6379（8.10.1 / AOF）；真实 MySQL 121.89.82.216:9000（8.0.46 / utf8mb4 / story_os_runtime）

凭据只从环境变量读取（STORYOS_REDIS_* / STORYOS_MYSQL_*），不写进仓库任何文件；下文与证据文件只记 host / port / database 与 password_present 布尔。

## 结论

本批补上 Phase9 Production Readiness Gate 第 4 节阻塞项 1「Real Runtime Environment —— 缺常驻 Runtime Worker 载体」的**命令载体**：新增 `scripts/phase9_runtime_worker.py`，把此前只存在于纯评估层的 `RuntimeHealthMonitor` / `RuntimeAlertManager` 与已就绪但无人周期性调用的 `WorkerHeartbeat` / `MySqlConnection` / `RedisConnection` / `RuntimeConsistencyScan` 串成一条可常驻运行的 tick 链路，并把每 tick 事实落成 Prometheus textfile + 告警 JSONL + tick JSONL + 运行证据 JSON。

真实实例取证：正例（Redis + MySQL 均可达）心跳生命周期 12 项 0 失败，单 tick 端到端 exit 0；负例（MySQL 指向不可达地址）1 tick 内产生 CRITICAL 告警与 OPEN 事件，exit 2。

边界先说清楚：交付的是**可常驻运行的命令载体**，不是已注册的系统服务 / 计划任务；metrics 只落盘为 Prometheus textfile，未接真实采集后端；告警通道是挂载点（`--alert-command`），默认未配置后端。

## 1. 载体设计：单 tick 链路

```
WorkerHeartbeat(TTL) --> Redis 探针 --> MySQL 探针 --> 每 N tick 一致性巡检
                                                    |
                                                    v
                              RuntimeHealthMonitor.evaluate --> RuntimeAlertManager.evaluate
                                                    |
                                                    v
                          Incident 生命周期(CRITICAL 开/关) --> 原子落盘 metrics / alerts / ticks / evidence
```

每 tick 固定顺序：

1. 写心跳：`WorkerHeartbeat.heartbeat(worker_id, status="ONLINE", ttl_seconds=...)`，键前缀 `storyos:worker:`；TTL = `max(1, round(interval_seconds * 3))`（`HEARTBEAT_TTL_FACTOR = 3`），即心跳至少能容忍两次 tick 抖动。
2. 依赖探针：Redis `ping()`；MySQL `ping()` + 三表行数（`event_log` / `trace_span` / `artifact_index`）。
3. 一致性巡检：默认每 `--consistency-every`（10）个 tick 调一次 `RuntimeConsistencyChecker` + `RuntimeConsistencyScan(ScanPolicy(compensating_write=False))`，只读取证，不自动改数据。
4. 健康评估：读 Legacy trace JSONL，按 `operation` 前缀分组算成功率，交给 `RuntimeHealthMonitor.evaluate`，再交 `RuntimeAlertManager.evaluate`。
5. 告警收敛 + Incident 生命周期：把心跳失败、健康等级、MySQL 不可达、数据不一致四类真实事实收敛为告警；CRITICAL 开事件（key = reason，重复出现只递增 occurrences），条件消失置 `RESOLVED`。
6. 落盘：Prometheus textfile 原子写（`*.tmp` 后 `os.replace`）、告警 JSONL、tick JSONL；进程退出写运行证据 JSON（含环境摘要，不含凭据）。

本载体明确不做的事：不注册系统服务 / 计划任务（需单独授权）；不写业务数据、不推进 episode stage；不接 `RuntimeRecoverySelfHealing` 做自动修复；不假设已部署 Prometheus server 或告警后端。

## 2. 健康输入口径

`derive_health_inputs(trace_records, memory_health, now, stuck_seconds)` 把 trace 事实折算成健康模型需要的四个输入：

| 输入 | 口径 |
| --- | --- |
| `agent_success_rate` | `agent.*` 终结 span（SUCCESS / FAILED）的成功率 |
| `workflow_success_rate` | `workflow.*` 终结 span 的成功率 |
| `trace_health` | 是否存在超过 `--stuck-minutes`（默认 30）未终结的 span |
| `memory_health` | 平台当前无独立 memory 子系统，用 Redis 状态层可达性作代理 |

两个口径说明：

- 某分组当 tick 没有任何终结 span 时取 1.0，并把 `terminal=0` 记进 `counts`，不因为「没数据」判 DEGRADED；`counts` 同时记录 `total / success / failed / running / stuck`。
- Redis 探针不 OK 时健康直接返回 `{"status": "UNKNOWN", "reason": "memory_signal_unavailable"}`，**不猜等级**，避免把「信号取不到」误报成 DEGRADED 引发假告警；该 tick 仍照常检测心跳写失败与 MySQL 不可达这两个不依赖 Redis 的 CRITICAL 事实。
- 「memory_health 用 Redis 可达性代理」是显式标注的取舍，随 tick 证据的 `health_mapping` 字段一并落盘，不隐藏为隐式假设。

## 3. 告警与 Incident 生命周期

| 来源 | 触发 | 等级 | reason |
| --- | --- | --- | --- |
| heartbeat | 心跳写入失败 | CRITICAL | `heartbeat_write_failed` |
| health_model | 健康等级 ∈ {WARNING, CRITICAL} | 原等级 | 健康模型给的原因 |
| dependency_probe | MySQL 探针 ERROR | CRITICAL | `mysql_unreachable` |
| consistency_scan | 巡检判不一致 | WARNING | `data_inconsistent` |

Redis 故障只由健康模型报一次（此时健康为 UNKNOWN、不擅自定义等级），避免同一次故障重复告警。只有 CRITICAL 创建 Incident；WARNING 只落告警日志不建事件。

## 4. CLI / 退出码 / 输出文件

```powershell
$env:STORYOS_REDIS_HOST="127.0.0.1"; $env:STORYOS_REDIS_PORT="6379"
$env:STORYOS_MYSQL_HOST="..."; $env:STORYOS_MYSQL_PORT="..."
$env:STORYOS_MYSQL_USER="..."; $env:STORYOS_MYSQL_PWD="..."; $env:STORYOS_MYSQL_DB="story_os_runtime"
python scripts/phase9_runtime_worker.py --interval 30 --consistency-every 10
```

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--worker-id` | `STORYOS_WORKER_ID` 或 `runtime-worker-<pid>` | 心跳键与标签用 |
| `--runtime` | `V3_RUNTIME` | 健康评估的 runtime 名 |
| `--interval` | 30 | tick 间隔秒 |
| `--consistency-every` | 10 | 每 N tick 跑一次一致性巡检 |
| `--stuck-minutes` | 30 | 判定 span 卡住的阈值 |
| `--once` / `--max-ticks` / `--max-seconds` | 无 | 受限运行（CI / 验收用） |
| `--no-redis` / `--no-mysql` | 关闭 | 离线运行，不碰外部依赖 |
| `--jsonl-root` | `STORYOS_RUNTIME_JSONL_ROOT` 或 `.storyos` | Legacy JSONL 根目录 |
| `--metrics-file` / `--alert-log` / `--tick-log` / `--evidence-file` | `.storyos/runtime/` 下同名文件 | 落盘位置 |
| `--alert-command` | 无 | 告警通道挂载点：CRITICAL 时把告警 JSON 从 stdin 交给外部命令，超时 15s |
| `--quiet` | 关闭 | 只留汇总 |

退出码：`0` 正常；`2` 仍有告警（WARNING / CRITICAL 或未消解事件）；`3` 参数或环境错误（含启动时 Redis 连不上）。信号 `SIGINT / SIGTERM / SIGBREAK` 触发优雅退出：删心跳键、关连接、写证据。

## 5. 真实实例取证

### 5.1 正例：心跳生命周期 12 项 0 失败

`--max-ticks 6 --interval 1 --consistency-every 3`，外部进程每 0.2s 采样真实 Redis 心跳键：

| 步骤 | 结果 |
| --- | --- |
| worker_exit_0 | exit 0 |
| heartbeat_key_seen_during_run | 采样 30 次可见，TTL ∈ {2, 3} |
| heartbeat_payload_online | payload `status=ONLINE`，含 worker_id 与 heartbeat_time |
| ttl_refreshed_and_expiring | TTL 有刷新且在衰减（非永久键） |
| heartbeat_removed_after_exit | 退出后键不存在（exists=0） |
| evidence_ticks | ticks=6 |
| consistency_scan_on_schedule | consistency_every=3 生效 |
| evidence_clean_of_credentials | 证据 JSON 全文无密码字符串 |
| heartbeat_removed_flag | shutdown.heartbeat_removed=true，closed=[redis, mysql] |
| metrics_file_present | metrics.prom 含 `storyos_runtime_worker_ticks_total`（5309 bytes） |
| metrics_counter_reached_6 | 计数到达 6 |
| tick_log_lines | tick JSONL 恰 6 行 |

单次 tick 手工取证（Redis + MySQL 均可达）关键字段：

```
heartbeat  : status=OK ttl_seconds=6
probes     : redis=OK / mysql=OK ping=true rows={event_log:0, trace_span:0, artifact_index:0}
consistency: consistent=true policy={compensating_write:false}
health     : HEALTHY / health_score=100.0 / level=INFO / reason=runtime_healthy
             inputs={agent_success_rate:1.0, workflow_success_rate:1.0, trace_health:true,
                     memory_health:true, counts 全 0, stuck_seconds:1800.0}
metrics    : written=true bytes=5823
errors     : []
shutdown   : heartbeat_removed=true closed=[redis, mysql]
```

### 5.2 负例：MySQL 不可达

把 MySQL 指向不可达地址（保留真实 Redis），`--max-ticks 1 --consistency-every 1`，实测 21.7s（探针超时 10s + 巡检超时 10s）后退出：

```
ticks=1 alert_counts={"INFO":0,"WARNING":0,"CRITICAL":1} open_incidents=1 退出码=2
alerts  : source=dependency_probe level=CRITICAL reason=mysql_unreachable
          detail.error=OperationalError: (2003, "Can't connect to MySQL server on '203.0.113.10' (timed out)")
incident: inc_neg-probe_1_mysql_unreachable status=OPEN occurrences=1
probes  : mysql status=ERROR / redis status=OK
errors  : mysql 与 consistency 两条 OperationalError
shutdown: heartbeat_removed=true closed=[redis, mysql]
```

即：依赖不可达这一真实事实被转成了告警 + 事件 + 非零退出码，而不是静默降级。

## 6. Metrics Exporter 载体

`render_metrics` 输出标准 Prometheus textfile，family 去重（HELP / TYPE 各一次），写入原子替换：

`storyos_runtime_worker_up`、`storyos_runtime_worker_ticks_total`、`storyos_runtime_worker_alerts_total`、`storyos_runtime_worker_open_incidents`、`storyos_runtime_worker_consistency_scans_total`、`storyos_runtime_worker_last_tick_timestamp_seconds`、`storyos_runtime_worker_heartbeat_ok`、`storyos_runtime_probe_ok{dependency=}`、`storyos_runtime_store_rows{table=}`、`storyos_runtime_health_score`、`storyos_runtime_alert_level{level=}`（one-hot）、`storyos_runtime_health_state{status=}`（HEALTHY / DEGRADED / UNHEALTHY / UNKNOWN one-hot）、`storyos_runtime_traces_total|success_total|failed_total|running|stuck`、`storyos_runtime_agent_success_rate`、`storyos_runtime_workflow_success_rate`、`storyos_runtime_consistency_entities{entity=}`。

这是「可被采集的导出载体」：textfile 可被 node_exporter textfile collector 或任意采集器读取，本批不含也已部署的采集后端。

## 7. 代码与测试

新增：

- scripts/phase9_runtime_worker.py
- tests/platform/test_phase9_runtime_worker.py（23 例，全离线：假 HeartbeatStore / Redis / MySQL 连接，覆盖健康推导分组与卡住判定、TTL 系数、心跳失败告警、Incident 开与消解、巡检调度、render_metrics family 去重、告警命令只对 CRITICAL、CLI 退出码 0 / 3、证据不含凭据、`--no-redis --no-mysql` 不触碰外部依赖、worker_id 标签净化）

修改：

- .gitignore（新增本地运行产物忽略项，与既有 .storyos/smoke、.storyos/tmp 一致）

测试：tests/platform 全量 234 passed / 0 failed（原 211 + 本批 23）；tests/system 186 passed + 16 subtests；合计 420 passed + 16 subtests。

## 8. 仍未完成 / 边界

- **载体未部署**：本批只交付命令；注册成 Windows 服务 / 计划任务需要单独授权，当前常驻能力靠人工启动。
- **Metrics 只落盘**：textfile 已生成，但没有已部署的 Prometheus / 采集器与仪表盘；也没有抓取存活告警。
- **Alert 通道是挂载点**：`--alert-command` 默认未配置，接 Slack / 邮件 / webhook 需要真实后端。
- **无自动修复**：`RuntimeRecoverySelfHealing` 未接入 tick 链路，本载体只报不修。
- **进程内状态**：`worker_ticks_total` / `alerts_total` 随进程重启归零，不是持久计数器。
- **健康模型不覆盖依赖层**：MySQL 不可达时健康模型仍可能是 HEALTHY（它只看 trace 事实），该故障由 `alerts_total` / `open_incidents` / `probe_ok` 暴露；`storyos_runtime_alert_level` 反映的是健康模型等级，与依赖层 CRITICAL 不是同一个信号，读仪表盘时需要区分。
- **本地/远端割裂**：Redis 在本机（127.0.0.1:6379），MySQL 在远端，二者不在同一实例域。
- **数据库账号**：仍是 `root@%` + GRANT OPTION，且与 nacos_config 等库共用同一实例。

---

## 9. P9.29 关联：真实 Recovery / Canary 演练

本载体是 P9.29 两项真实演练的运行前提：

- 恢复演练：scripts/phase9_recovery_drill.py（reports/phase9_runtime_recovery_real_validation.md）
- 灰度演练：scripts/phase9_canary_drill.py（reports/phase9_runtime_canary_simulation_report.md）

两项演练各产生独立证据，退出码契约一致（0 通过 / 2 断言失败 / 3 环境错误）。
演练证据落 .storyos/drill/（本地运行产物，已加入 .gitignore，不入 Git）。

测试基线更新：tests/platform 234 -> 261 passed（演练离线回归 +27）；tests/system 186 passed + 16 subtests。

---

## 10. P9.30 关联：Worker 存活观察者

本批补上 P9.29 finding worker_liveness_not_critical（HIGH）。关键点：观察者是**独立进程**（scripts/phase9_liveness_watchdog.py），不是本载体的 Worker 内环。

- 本载体（scripts/phase9_runtime_worker.py）的 tick 只在进程存活时运行，Worker 整体消失后它无法自证失联；观察者独立运行，专门判定「名册登记过但读不到心跳」。
- 判定口径（platform/operations/runtime_worker_liveness.py）：missing = expected - observed -> CRITICAL worker_liveness_lost；以真实读到心跳为准，SCAN 到键但读不到也算失联。
- 默认名册 / 事件 / 指标落 .storyos/runtime/（本地运行产物，已 gitignore）；退出码 0 无失联 / 2 有失联 / 3 环境错误。
- 观察者只报不修，不接 RuntimeRecoverySelfHealing。

专门报告：reports/phase9_runtime_worker_liveness_watchdog.md

测试基线更新：tests/platform 261 -> 280 passed（存活观察者 +19）；tests/system 186 passed + 16 subtests。
