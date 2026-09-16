# Phase 9 - P9-STAGING-3 Runtime Staging Smoke 执行证据

日期：2026-09-10
分支：story-platform-v3
代码基线：273c048（本批改动尚未提交）
范围：把 phase9_runtime_bootstrap_manifest.md 第 8 节承诺的
      python scripts/phase9_runtime_smoke.py 真正实现并执行一次，留下可复核证据
验证方式：本机 Python 3.12.10 + pymysql 1.4.6 + redis-py 8.0.1；
          真实 MySQL 121.89.82.216:9000（8.0.46 / utf8mb4 / story_os_runtime）、
          真实 Redis 127.0.0.1:6379（AOF 已开启）

---

## 结论

P9-STAGING-3 的缺口已补齐：manifest 里只有名字没有实现的
python scripts/phase9_runtime_smoke.py 现在是真脚本，并已完成一次真实执行。

- 真实 MySQL + Redis 下共 55 项检查，0 失败、0 跳过，退出码 0。
- 一轮冒烟真的走了 Request/Plan -> AgentRuntime -> Trace/Event/Artifact ->
  一致性巡检 -> Runtime Operations 全链路，不是只构造对象后打印 PASS。
- 清理闭环成立：MySQL 探测行全部删除（三表回到 0/0/0）、Redis DBSIZE 回到 0、
  探测目录整棵删除。
- 边界照旧：这是 in-process AgentRuntime 的执行证据，不代表"常驻 Runtime Worker
  已部署"；仓库当前没有 Worker 进程载体，本批也没有引入进程管理基础设施。

---

## 1. 执行命令

凭据只从环境变量读取，不写入仓库任何文件：

    $env:STORYOS_MYSQL_HOST / _PORT / _USER / _PWD / _DB
    $env:STORYOS_REDIS_HOST / _PORT
    python scripts/phase9_runtime_smoke.py

本次真实执行：

    run_id       smoke_20260910T141515Z_60f827f4
    开始         2026-09-10T14:15:15.207Z
    结束         2026-09-10T14:15:17.330Z
    总耗时       2122 ms
    mode         dual（Legacy JSONL + MySQL 双写）
    git          273c048eab8d907dbe9c5e652a507077bce452db @ story-platform-v3

证据文件（未跟踪，位于 .gitignore 覆盖的目录）：

    .storyos/smoke/phase9_runtime_smoke_evidence.json
    （逐项 checks、环境摘要、实体 ID、metrics、operations 全在里面）

环境摘要记录为 host / port / database + "是否提供了密码"，**不记录密码本身**：

    mysql   host=121.89.82.216 port=9000 database=story_os_runtime password_present=true
    redis   host=127.0.0.1 port=6379 db=0 password_present=false

---

## 2. 覆盖分组

| 分组 | 覆盖 | 结果 |
| --- | --- | --- |
| A 环境与配置 | python 版本、config/storyos.yaml 与 agent_runtime/trace.json 可解析、存储模式解析、MySQL 环境变量齐备 | 5/5 |
| B MySQL 真实连接 | health_check（8.0.46）、库名与 utf8mb4、apply_schema 幂等重建四步、基线行数 | 4/4 |
| C Redis 真实连接 | ping（8.10.1）、AOF aof_enabled=1 且 last_write=ok、基线 DBSIZE | 2/2 |
| D Runtime 装配与执行 | 三类 observer 绑定 repository、skill/tool 注册、主路径 SUCCESS、recorder 关联 trace、真实 tool 调用、未授权 tool 被拒 | 6/6 |
| E 事实落库 | 5 条 event、真实文件 sha256 的 artifact、JSONL 覆盖后读到最后写入、MySQL trace/event/artifact 行、无时区墙钟时间 | 13/13 |
| F Redis 运行时状态 | WorkerHeartbeat 带 TTL、Episode 锁 SET NX 首个成功/第二个被拒、锁归属、release 清键、TaskStateManager 读写 | 7/7 |
| G 双写一致性 | 单条 Event/Trace/Artifact MATCH、全量巡检无 mismatch/单边缺失、命中本轮探测数据、覆盖写被识别为已知重复键 | 6/6 |
| H Operations 证据链 | 健康度/告警/控制面/Observability 视图、全量统计降级、故障注入 CRITICAL、自愈决策、审计 | 10/10 |
| I 清理 | MySQL 探测行删除并回基线、Redis DBSIZE 回基线 | 2/2 |

合计 55 项 PASS、0 FAIL、0 SKIPPED。

---

## 3. 实测关键行

    execution_id      exec_5e02eec2e62e4974b913d203804a7795      status=SUCCESS
    trace/span        trace_3b2acb8bc90546f597170e292f1127ac / span_494c40e551d94a23a50952b8b943420a
    trace.duration    153 ms（同一次 RUNNING 行被终态同主键覆盖为单行）
    artifact_id       artifact_2adde73cc4c54a7b95e620a7b1fdc318
    artifact.sha256   2dd03db0975f106e5855c6b00d9e8e4c6620e715d6efc41ef75107e4fdde4017
    event_id × 5      evt_c386b4ef… evt_a074bced… evt_5135e8d7… evt_68869eb5… evt_3f07e4a1…
    事件类型            WORKFLOW_STARTED / TASK_STARTED / TASK_COMPLETED / TASK_FAILED / ARTIFACT_CREATED
    落库时间            started_at=2026-09-10 14:14:35.673984 tzinfo=None（无时区墙钟值）

---

## 4. 策略路径与故障路径

allowed_tools 策略不是摆设——脚本故意跑了一次越权调用：

    skill   staging.smoke.denied_skill（allowed_tools=()）
    结果    AgentExecutionResult.status=FAILED
    error   skill staging.smoke.denied_skill is not allowed to invoke tool staging.smoke.tool
    落库    trace_span 保留一条 status=FAILED 且 error 非空的行（与主路径 SUCCESS 行共存）

健康度/告警链路分成三种输入，避免"用假数据证明链路通"：

| 用例 | 输入 | 真实输出 |
| --- | --- | --- |
| 主路径 | success_rate=1.0、trace/memory 健康 | HEALTHY(100) → INFO 告警 → 控制面 HEALTHY → 视图 HEALTHY |
| 全量统计 | 2 次执行 1 次成功（真实含越权拒绝那次） | DEGRADED(50) → WARNING → 事故 RESOLVED（WARNING 不开 OPEN 事故） |
| 故障注入 | memory_health=False（显式注入，已在输出里标注） | UNHEALTHY(25) → CRITICAL → 事故 OPEN → 自愈决策 RESTART_AGENT |

其中 reliability / performance / cost 三个状态来自真实模块调用：reliability 用本轮
真实成功率，performance 用真实 trace 耗时，cost 因为冒烟没有成本遥测而按 0 传入
（只验证聚合链路能消费该模块，不代表真实成本水平）。

---

## 5. 双写一致性

    单条比对    event=MATCH        trace=MATCH        artifact=MATCH
    全量巡检    event match=5      trace match=2      artifact match=1
                mismatch=0         legacy_only=0      mysql_only=0
    重复键      trace 两个主键各一条（RUNNING 先落、终态覆盖）

重复键是 Legacy JSONL 追加写语义的必然结果（MySQL 侧同主键仍是单行），脚本把它
断言成"已知重复键"而不是当作异常，避免把正常覆盖写误报成数据问题。

---

## 6. 清理结果

    MySQL   deleted={event_log:5, trace_span:2, artifact_index:1}
            baseline=0/0/0  now=0/0/0
    Redis   baseline DBSIZE=0  now=0
    目录    .storyos/smoke/<run_id> 整棵删除

新增安全护栏：只有位于 .storyos/smoke/ 之下或系统临时目录之下的探测目录才允许
自动删除。传 --jsonl-root .storyos 这种危险目标时脚本会保留目录并记 INFO，
不会把整个 .storyos 删掉。

---

## 7. 离线模式（无外部依赖机器）

    python scripts/phase9_runtime_smoke.py --mode jsonl --no-redis

结果：PASS=19、FAIL=0、SKIPPED=13、退出码 0、91 ms。
jsonl / no-redis 下 MySQL、Redis、一致性分组明确记为 SKIPPED（而不是假装通过），
Operations 分组里依赖 memory_health 的四项健康路径也记为 SKIPPED，只保留不依赖
外部状态的断言。这条路径被 tests/platform 当成回归用（离线、不连真实实例）。

---

## 8. 本批发现并修掉的脚本缺陷

两次真实运行各暴露一个脚本自身的问题，都不是平台缺陷：

1. 第一次运行（54 PASS / 1 FAIL）：重复键断言只写了一个 trace 主键，而真实情况是
   两次执行各留一个（越权那次也走 RUNNING -> FAILED 覆盖）。断言改成比对两个
   主键的集合。
2. 第二次运行（G 组后中断，退出码 2）：一致性分组的重复键断言引用了未绑定的
   denied，触发 NameError。异常被捕获成 FAIL 而不是静默通过，退出码 2 也如实返回。

这两次恰好验证了两件事：脚本存在 FAIL 时不会伪装成功；中途异常会被记录成失败项
并仍然执行清理（两次都成功回到基线）。

---

## 9. 仍未完成 / 已知边界

- Runtime Worker 仍无常驻进程载体：manifest 假设的"Worker 部署"没有实现，本脚本用
  in-process AgentRuntime 取证，不声称 Worker 已上线。
- ExecutionRecorder 仍是进程内存记录器（源码注释写明 until the MySQL repository is
  wired in）；durable 证据只有 trace / event / artifact 三类。
- 巡检未调度化、无告警通道：mysql_only / legacy_only / MISMATCH / 悬停 RUNNING 目前
  只能在人工执行时被发现。
- 冒烟耗时不能当稳态延迟：首个真实执行 3163 ms（含首次建连），后续 141 / 153 ms。
- Redis 本机、MySQL 远端，实例割裂；Episode 锁无 TTL，崩溃会留死锁。
- MySQL 账号仍是 root@% 且与 nacos_config 共用实例。
- 真实生产流量未接入：本批全部是探测数据。

---

## 10. 测试

tests/platform 全量：199 passed / 0 failed（本批新增 6 个离线回归）。
tests/system 全量：186 passed + 16 subtests。

新增测试文件：tests/platform/test_phase9_runtime_smoke_script.py

| 用例 | 覆盖 |
| --- | --- |
| offline_jsonl_run_passes_and_stays_offline | 环境变量指向真实/不可达实例时 jsonl 模式仍只走本地，B/C/F/G 必须 SKIPPED |
| offline_run_writes_legacy_jsonl_facts | JSONL 实际落盘行数（event 5 / trace 4 / artifact 1）与状态分布 |
| evidence_never_contains_credentials | 证据文件、stdout/stderr、JSONL 中都不出现密码明文 |
| unknown_mode_is_rejected | 非法 --mode 退出码 2 |
| probe_dir_safety_guard | 危险根目录（仓库根、.storyos）拒绝自动删除 |
| summarize_counts_by_status_and_group | 汇总计数口径 |
