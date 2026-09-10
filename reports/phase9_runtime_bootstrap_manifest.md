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

f4cbed8ec433c53fe60936f3319eb6a5e0493dfd

说明：

Phase8/Phase9 Code Acceptance 基线。

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

当前状态：

待补充实际执行脚本。

---

# 9. External Dependencies

## Redis

用途：

- Runtime State
- Lock
- Worker Heartbeat

状态：

代码支持，Staging 未接入。


## MySQL

用途：

- Repository
- Trace/Event/Artifact Persistence

状态：

代码支持，Staging 未接入。

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

🟡 Preparation Complete

下一阶段：

P9-STAGING-4 Observability Validation

前置条件：

- Runtime Smoke 实际执行
- Evidence 收集
- Metrics 接入
