# Story OS V3 Phase9 Runtime Bootstrap Manifest

更新时间：

2026-09-10

项目：

D:/workspace/YeQianWorkSpace/yeqian/storyOS

分支：

story-platform-v3

---

# 1. Purpose

本文件定义 Phase9 Runtime Staging 的可复现启动基线。

目标：

将 Runtime 从“开发机可运行”提升为“Staging 环境可准备”。

范围：

- Python Runtime
- Platform Runtime Module
- Configuration Loading
- Storage Backend
- Smoke Test Entry

---

# 2. Code Baseline

当前代码基线：

Commit:

273c048（story-platform-v3）

说明：

Phase8/Phase9 Code Acceptance 基线；P9.26/P9.27 与 Runtime Smoke 改动仍在工作树未提交。

运行时证据见：

reports/phase9_runtime_smoke_execution_evidence.md

---

# 3. Runtime Components

核心组件：

```
platform/
├── api
├── adapter
├── workflow
├── agent
├── state
├── repository
├── trace
├── event
├── artifact
├── observer
└── operations
```

---

# 4. Python Runtime

当前要求：

- Python 3.12+
- pytest 9.x（验证环境）

说明：

当前项目未提供根目录 requirements/pyproject，依赖由开发环境维护。

后续建议：

补充 Runtime 专用依赖清单。

---

# 5. Configuration

配置入口：

```
config/storyos.yaml
config/index.yaml
```

Runtime 配置域：

- agent runtime
- provider
- trace
- profile

---

# 6. Storage Mode

## Stage 1 Local Staging

默认：

```
JSONL Trace Store
JSONL Event Store
JSONL Artifact Store
```

用途：

验证 Runtime Execution 闭环。


## Stage 2 External Dependency

支持：

```
MySQL
Redis
```

对应模块：

```
platform/repository/mysql
platform/state/redis_runtime_state_store.py
```

---

# 7. Runtime Start Entry

当前阶段：

Synthetic Runtime Smoke。

入口：

```
AgentRuntime.execute()
```

执行链：

```
AgentExecutionPlan
        ↓
AgentRuntime
        ↓
ExecutionRecorder
        ↓
Trace
        ↓
Evidence
```

---

# 8. Smoke Test Command

目标命令：

```
python scripts/phase9_runtime_smoke.py
```

状态：

✅ 脚本已落地并真实执行（入口 scripts/phase9_runtime_smoke.py）。

覆盖分组：

- A 环境与配置
- B MySQL 连接与读写
- C Redis 连接与状态
- D Runtime 执行（真 skill + tool + 越权拒绝路径）
- E 事实落库（Trace/Event/Artifact → JSONL + MySQL）
- F Redis 运行态
- G 双写一致性巡检
- H Operations（Health / Alert / Control Plane / Observability / Recovery / Audit）
- I 探测数据清理

最近真实执行结果（2026-09-10）：

```
run_id     smoke_20260910T141515Z_60f827f4
结果       55 PASS / 0 FAIL / 0 SKIPPED，退出码 0
耗时       2122 ms（首次含建连 3163 ms，后续 141 / 153 ms）
```

离线路径（不依赖外部服务）：

```
python scripts/phase9_runtime_smoke.py --mode jsonl --no-redis
```

结果 19 PASS / 0 FAIL / 13 SKIPPED，退出码 0，91 ms；依赖外部服务的分组如实记为 SKIPPED，不假装通过。

边界：

本脚本以 in-process AgentRuntime 取证，证明执行链、落库与 Operations 代码路径可用；不证明常驻 Runtime Worker 已部署。

真实执行证据见：

reports/phase9_runtime_smoke_execution_evidence.md

---

# 9. External Dependencies

## Redis

用途：

- Runtime State
- Lock
- Worker Heartbeat

状态：

✅ 已接入并验证（127.0.0.1:6379，8.10.1，AOF aof_enabled=1）。

覆盖：

- 连接与 PING（C 组）
- Runtime State / Lock / Worker Heartbeat（F 组）
- 探测键清理：DBSIZE 0 → 0

已知风险：

- Redis 在本机、MySQL 在远端，实例物理割裂
- Episode 锁无 TTL，崩溃可能留死锁
- allkeys-lru 可能驱逐锁键


## MySQL

用途：

- Repository
- Trace/Event/Artifact Persistence

状态：

✅ 已接入并验证（121.89.82.216:9000 / story_os_runtime / 8.0.46 / utf8mb4）。

覆盖：

- 连接与版本、字符集探测（B 组）
- Event / Trace / Artifact 三仓储读写与事务回滚
- 落库与清理前后 baseline 0/0/0 → 0/0/0

已知风险：

- 账号仍是 root@%，权限未最小化
- 与 nacos_config 共用同一实例

---

# 10. Validation Flow

```
Environment Bootstrap
        ↓
Dependency Validation
        ↓
Runtime Smoke Test
        ↓
Observability Validation
        ↓
Recovery Drill
        ↓
Canary Simulation
```

---

# 11. Current Decision

Phase9 Runtime Staging:

状态：

🟡 Prepared + Runtime Smoke Executed

下一阶段：

P9-STAGING-4 Observability Validation

前置条件：

- ✅ Runtime Smoke 实际执行（55 PASS / 0 FAIL / 0 SKIPPED）
- ✅ Evidence 收集（reports/phase9_runtime_smoke_execution_evidence.md）
- ✅ Observability H 组真实触发 Health / Alert / Recovery / Audit
- ⏸ Metrics Backend 与 Alert Channel 真实接入
