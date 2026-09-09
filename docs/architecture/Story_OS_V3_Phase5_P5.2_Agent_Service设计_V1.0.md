# Story OS V3 Phase 5-P5.2 Agent Service 设计 V1.0

更新时间：
2026-09-09

项目：
Story OS

分支：
story-platform-v3

---

# 一、设计目标

Phase 5-P5.2 目标：

将 Phase 3 已完成的 Agent 能力模型，封装为平台服务。

从：

```
Agent Model + Registry 数据能力
```

升级为：

```
Agent Service

提供统一Agent管理、发现、执行入口
```

---

# 二、服务定位

Agent Service 负责：

```
Agent注册

Agent版本管理

Agent能力查询

Agent生命周期管理

Agent执行入口

Agent状态查询
```

不负责：

```
Workflow编排

Skill具体执行

MCP调用

Runtime调度
```

边界：

```
Workflow
决定什么时候调用Agent

Agent Service
提供哪个Agent可用

Agent Runtime
负责真正执行
```

---

# 三、整体架构

```
                 Platform API
                     |
                     v
              Agent Service
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
 Agent Registry  Version Mgmt  Execution Query
       |
       v
 Agent Model
       |
       v
 Agent Runtime
```

---

# 四、核心模块

## 1. Agent Registry

负责Agent注册。

能力：

- 创建Agent
- 查询Agent
- 修改状态
- 发布版本

例如：

```
STORY_AGENT
VISUAL_AGENT
REVIEW_AGENT
```

---

# 2. Agent Version Manager

负责版本生命周期。

流程：

```
DRAFT
 |
TESTING
 |
ACTIVE
 |
DEPRECATED
```

保证：

历史Execution永远绑定具体版本。

---

# 3. Agent Capability Resolver

提供能力查询。

例如：

请求：

```
需要 IMAGE_REVIEW 能力
```

返回：

```
Review Agent v2
```

数据来源：

```
Agent
+
Skill Capability
```

---

# 4. Agent Execution Gateway

提供执行入口。

调用链：

```
API
 |
 v
Agent Service
 |
 v
Agent Orchestrator
 |
 v
Agent Runtime
```

Agent Service 不直接执行任务。

---

# 五、核心接口设计

## Agent管理

```
POST /agents

GET /agents/{id}

PUT /agents/{id}/status
```

---

## Agent版本

```
POST /agents/{id}/versions

GET /agents/{id}/versions
```

---

## Agent发现

```
POST /agents/search
```

输入：

```
capability
skill_type
status
```

输出：

可用Agent列表。

---

## Agent执行查询

```
GET /agents/executions/{id}
```

返回：

```
Agent Execution Record
Skill Execution
Tool Execution
Trace
Artifact
```

---

# 六、数据依赖

Agent Service 使用：

```
agent

agent_version

agent_skill_relation

agent_execution
```

来自 Phase 3 数据模型。

---

# 七、与其他Service关系

```
Workflow Service
        |
        v
Agent Service
        |
        v
Skill Service
        |
        v
MCP Service
        |
        v
Runtime Service
```

---

# 八、部署策略

当前阶段：

推荐：

```
Modular Monolith
```

代码模块：

```
platform/agent
```

未来规模扩大后再拆：

```
agent-service
```

独立服务。

---

# 九、本阶段范围

完成：

✅ Agent Service职责定义

✅ 服务边界设计

✅ API设计

✅ 数据依赖设计

未实现：

❌ Agent Service代码

❌ REST Controller

❌ Agent Repository

❌ Runtime调用实现

属于后续工程落地阶段。
