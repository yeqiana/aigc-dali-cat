# Story OS V3 Phase7-P7.2 Platform Service 模块骨架设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

---

# 一、目标

将 Phase 5 设计的平台能力真正映射到工程模块。

从：

```
Architecture
```

进入：

```
Code Module Structure
```

---

# 二、整体模块结构

推荐：

```
platform/

├── agent
│
├── workflow
│
├── memory
│
├── project
│
├── config
│
├── permission
│
├── observability
│
└── common
```

保持 Modular Monolith。

暂不拆微服务。

---

# 三、统一分层结构

每个模块保持：

```
module
 |
 ├── api
 |
 ├── application
 |
 ├── domain
 |
 ├── repository
 |
 └── infrastructure
```

---

# 四、各层职责

## api

负责：

- REST接口
- 请求参数
- 返回模型

禁止：

- 业务逻辑

---

## application

负责：

- 用例编排
- 事务管理
- Domain调用

例如：

```
CreateAgentUseCase
RunWorkflowUseCase
SearchMemoryUseCase
```

---

## domain

核心业务模型。

包含：

- Entity
- Value Object
- Domain Service

---

## repository

负责数据访问抽象。

例如：

```
AgentRepository
WorkflowRepository
MemoryRepository
```

---

## infrastructure

实现：

- MySQL
- Redis
- Vector Store
- MCP Client

---

# 五、核心模块职责

## Agent Module

负责：

```
Agent Registry
Agent Version
Agent Execution
```

---

## Workflow Module

负责：

```
Workflow Definition
Workflow Run
Workflow Step
```

---

## Memory Module

负责：

```
Memory Storage
Retrieval
Learning
```

---

## Project Module

负责：

```
Project
Member
Resource Scope
```

---

## Config Module

负责：

```
Config Definition
Config Version
Config Resolve
```

---

## Permission Module

负责：

```
User
Role
Permission
Authorization
```

---

# 六、模块依赖规则

允许：

```
api
 ↓
application
 ↓
domain
 ↓
repository
```

禁止：

```
Agent直接调用Memory数据库

Workflow直接调用MCP

Runtime修改Domain事实
```

---

# 七、Runtime关系

未来：

```
Workflow Service

      ↓

Agent Orchestrator

      ↓

Agent Service

      ↓

Agent Runtime

      ↓

Platform Modules
```

---

# 八、迁移策略

不影响当前生产。

采用：

```
新增platform模块

        ↓

接入测试链路

        ↓

Shadow运行

        ↓

逐步替换旧调用
```

---

# 九、Phase 7状态

```
Phase 7 Implementation

├── P7.1 数据库模型落地
│      ✅
│
└── P7.2 Platform Service模块骨架
       ✅
```

下一步：

```
Phase 7-P7.3
Platform API实现
```
