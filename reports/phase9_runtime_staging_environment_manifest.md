# Story OS V3 Phase9 Runtime Staging Environment Manifest

更新时间：2026-09-10

项目：

D:/workspace/YeQianWorkSpace/yeqian/storyOS

分支：

story-platform-v3

---

# 1. Purpose

本文件定义 Phase9 Runtime Staging Validation 的环境基线。

目标：

在不影响 story 生产分支的前提下，建立接近生产运行方式的 Runtime Staging 验证入口。

验证范围：

```
Request
 ↓
Workflow
 ↓
Agent Runtime
 ↓
State Store
 ↓
Trace/Event
 ↓
Artifact
 ↓
Operations
```

---

# 2. Code Baseline

当前冻结版本：

Commit:

```
f4cbed8ec433c53fe60936f3319eb6a5e0493dfd
```

说明：

Phase8 Production Migration 与 Phase9 Runtime Operations 已完成代码验收。

基线推进（2026-09-10）：

工作树已推进至 273c048，并叠加 P9.26 Data Foundation / P9.27 Persistence 与
Runtime Smoke 未提交改动；tests/platform 现为 199 passed，tests/system 186 passed + 16 subtests。
本节 Commit 为代码验收冻结时点记录。

---

# 3. Runtime Components

## Platform API

路径：

```
platform/api
```

职责：

- Runtime 请求入口
- Service Contract
- API 路由

状态：

✅ Ready

---

## Workflow Runtime

路径：

```
platform/workflow
```

职责：

- Workflow 执行
- 状态流转
- 编排

状态：

✅ Ready

---

## Agent Runtime

路径：

```
platform/agent
```

职责：

- Agent 执行
- Skill/MCP 扩展入口

状态：

✅ Ready

---

## Runtime State

路径：

```
platform/state
```

组件：

- runtime_state_store
- redis_runtime_state_store
- episode_lock_manager
- worker_heartbeat
- task_state_manager

状态：

✅ Ready

---

## Repository

路径：

```
platform/repository
```

组件：

- migration_repository
- dual_write_repository
- event_repository
- consistency_checker

状态：

✅ Ready

---

## Observability

路径：

```
platform/trace
platform/event
platform/observer
```

能力：

- Trace
- Event
- Artifact Observation

状态：

✅ Ready

---

# 4. Storage Strategy

## Stage 1 Local Runtime

默认：

```
Local JSONL Store
```

用于验证：

- Runtime execution
- Trace generation
- Artifact persistence

---

## Stage 2 External Dependency

后续接入：

```
MySQL
Redis
Monitoring
Alert System
```

用于生产接近验证。

---

# 5. Configuration Entry

配置入口：

```
config/storyos.yaml
config/index.yaml
config/agent_runtime/
```

原则：

Runtime 配置集中管理，不新增第二套配置源。

---

# 6. Validation Roadmap

## P9-STAGING-1 Environment Bootstrap

当前：

✅ Manifest Ready


## P9-STAGING-2 Dependency Validation

待执行：

- Python Runtime
- Storage
- Redis
- MySQL


## P9-STAGING-3 Runtime Smoke Test

验证：

Synthetic Workflow 完整执行。


## P9-STAGING-4 Observability Validation

验证：

- Metrics
- Trace
- Event


## P9-STAGING-5 Recovery Drill

验证：

- Worker Failure
- State Recovery
- Retry


## P9-STAGING-6 Canary Simulation

验证：

- Traffic Routing
- Rollback

---

# 7. Boundary

当前阶段不代表：

- Production Switch
- Production Ownership Transfer
- Real User Traffic Migration

Runtime Staging 通过后，才进入 Production Canary Drill。

---

# 8. Next Step

进入：

```
P9-STAGING-2 Dependency Validation
```
