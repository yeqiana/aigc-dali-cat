# Story OS V3 Phase 5 Platform Service 化架构设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、Phase 5目标

Phase 0-4完成：

- 数据基础
- Workflow中心化
- Agent平台化
- Memory系统

但当前仍偏向：

```
代码能力集合
```

Phase 5目标：

升级为：

```
AI Agent Platform Service
```

让内部能力服务化。

---

# 二、整体架构

```
                API Gateway
                     |
                     v
             Platform API Layer
                     |
 +-------------------+-------------------+
 |                   |                   |
 v                   v                   v
Agent Service   Workflow Service   Memory Service

 |                   |                   |
 v                   v                   v
Registry         Runtime          Retrieval

                     |
                     v
              Event / Trace / Artifact
```

---

# 三、服务拆分

## 1. Agent Service

负责：

- Agent注册
- Agent版本管理
- Agent查询
- Agent状态管理

对应：

```
agent
agent_version
agent_execution
```

---

## 2. Skill Service

负责：

- Skill注册
- Skill版本管理
- Skill能力查询

对应：

```
skill_definition
skill_version
skill_capability
```

---

## 3. MCP Service

负责：

- MCP Server管理
- Tool管理
- 权限管理

对应：

```
mcp_server
mcp_tool
tool_permission
```

---

## 4. Workflow Service

负责：

- Workflow定义
- Workflow运行
- Workflow查询

保持：

```
Workflow控制流程
```

不进入Agent逻辑。

---

## 5. Memory Service

负责：

- Memory写入
- Memory检索
- Memory评分
- Memory学习

对应：

```
memory_item
memory_embedding
memory_feedback
```

---

## 6. Runtime Service

负责：

- Agent执行
- Skill调用
- MCP调用
- Retry恢复

不是业务服务。

---

# 四、统一接口层

提供：

```
REST API

Event API

Internal RPC
```

例如：

```
POST /api/agents/run

GET /api/workflows/{id}

POST /api/memory/search
```

---

# 五、平台核心能力

## Registry中心

统一管理：

```
Agent
Skill
MCP
```

---

## Execution中心

统一记录：

```
Task
Agent Execution
Skill Execution
Tool Execution
```

---

## Observability中心

统一查看：

```
Trace
Event
Artifact
Cost
Failure
```

---

# 六、部署形态

初期不要拆微服务。

推荐：

```
Spring Boot / FastAPI Modular Monolith

        |

MySQL
Redis
Vector Store
```

原因：

- 降低运维成本
- 保持模块边界
- 后续可拆服务

---

# 七、演进路线

```
Phase 5.1
Platform API

↓

Phase 5.2
Registry Service

↓

Phase 5.3
Execution Service

↓

Phase 5.4
Memory Service

↓

Phase 5.5
Console Dashboard
```

---

# 八、约束

禁止：

- Platform Service替代Workflow
- Agent直接操作数据库
- Memory直接污染Runtime状态
- 服务拆分优先于能力稳定

原则：

```
先模块化
再服务化
最后微服务化
```
