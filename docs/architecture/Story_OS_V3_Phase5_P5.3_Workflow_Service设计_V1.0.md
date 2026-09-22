# Story OS V3 Phase 5-P5.3 Workflow Service 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 5-P5.3 目标：

将 Phase 2 Workflow 中心化能力封装为平台服务。

从：

```
Workflow Model
        |
Runtime内部调用
```

升级：

```
Workflow Service
        |
Agent Orchestrator
        |
Runtime Service
```

Workflow Service 负责流程管理，不负责智能决策。

---

# 二、职责边界

## Workflow Service负责

- Workflow定义管理
- Workflow版本管理
- Workflow运行创建
- Workflow状态查询
- Workflow Step管理
- Workflow Projection


## 不负责

禁止：

- Agent选择
- Skill选择
- MCP调用
- 任务实际执行

边界：

```
Workflow
决定做什么

Agent
决定怎么做

Runtime
负责执行
```

---

# 三、整体架构

```
             API Layer
                 |
                 v
          Workflow Service
                 |
       +---------+---------+
       |                   |
       v                   v
 Workflow Model     Workflow Runtime
       |
       v
 Projection
       |
       v
 Agent Orchestrator
```

---

# 四、核心模块

## 1. Workflow Definition Manager

管理Workflow模板。

例如：

```
AI_STORY_PRODUCTION

IMAGE_PRODUCTION

REVIEW_PIPELINE
```

能力：

- 创建
- 发布
- 禁用
- 版本管理

---

## 2. Workflow Run Manager

管理一次Workflow执行。

例如：

```
EP002 Production Run
```

记录：

- workflow实例
- 当前状态
- 开始结束时间
- 执行结果

---

## 3. Workflow Step Engine

管理步骤。

例如：

```
Story Lock

Visual Lock

Production

Review

Release
```

Step完成后：

触发下一节点。

---

## 4. Workflow Projection Service

负责：

```
Event
 |
 v
Projection
 |
 v
Workflow View
```

用途：

- 查询
- Dashboard
- 状态展示

不替代episode-state.json。

---

# 五、核心API设计

## Workflow管理

```
POST /api/v1/workflows

GET /api/v1/workflows/{id}
```

---

## 创建运行

```
POST /api/v1/workflows/{code}/runs
```

返回：

```
workflow_run_id
```

---

## 查询运行状态

```
GET /api/v1/workflows/runs/{id}
```

返回：

- 当前Step
- 已完成Step
- 下一Step

---

## Step查询

```
GET /api/v1/workflows/runs/{id}/steps
```

---

# 六、与Agent体系关系

完整链路：

```
Workflow Service

      |
      v

Workflow Step

      |
      v

Agent Orchestrator

      |
      v

Agent Service

      |
      v

Runtime Service
```

---

# 七、数据来源

继续遵循V3原则：

事实：

```
Event
Trace
Runtime Result
```

投影：

```
Workflow Projection
```

禁止：

Workflow Service直接篡改Runtime状态。

---

# 八、Phase 5 当前进度

```
Phase 5 Platform Service

├── P5.1 Platform API Layer
│      ✅
│
├── P5.2 Agent Service
│      ✅
│
└── P5.3 Workflow Service
       ✅
```

下一步：

```
Phase 5-P5.4

Memory Service 设计
```

将 Phase 4 Memory 能力封装为平台服务。