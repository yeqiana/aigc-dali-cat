# Story OS V3 Phase 5-P5.1 Platform API Layer 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 5-P5.1 目标：

建立 Story OS Platform API Layer。

将内部能力统一通过平台接口暴露。

从：

```
内部模块调用
```

升级：

```
Application
      |
      v
Platform API
      |
      v
Agent / Workflow / Memory / Runtime
```

---

# 二、设计原则

## 1. API只负责能力编排

不负责：

- Agent决策
- Workflow状态推进
- Runtime执行细节

---

## 2. 保持模块边界

API Layer作为入口：

```
Controller
    |
Application Service
    |
Domain Service
```

禁止：

Controller直接访问数据库。

---

# 三、整体API结构

```
/api/v1

 ├── /agents
 │
 ├── /skills
 │
 ├── /mcp
 │
 ├── /workflows
 │
 ├── /executions
 │
 ├── /memory
 │
 └── /trace
```

---

# 四、Agent API

## Agent注册

```
POST /api/v1/agents
```

能力：

创建Agent定义。

---

## Agent查询

```
GET /api/v1/agents/{id}
```

返回：

- Agent信息
- Version
- Skill绑定

---

## Agent执行查询

```
GET /api/v1/agents/{id}/executions
```

---

# 五、Workflow API

## 创建Workflow运行

```
POST /api/v1/workflows/{code}/runs
```

---

## 查询Workflow状态

```
GET /api/v1/workflows/runs/{id}
```

返回：

- 当前步骤
- 执行状态
- Evidence

---

# 六、Execution API

负责查询Agent执行事实。

## 查询执行记录

```
GET /api/v1/executions/{id}
```

返回：

```
Agent Execution
Skill Execution
Tool Execution
Trace
Artifact
```

---

# 七、Memory API

## Memory检索

```
POST /api/v1/memory/search
```

输入：

```
query
agent_type
memory_type
limit
```

---

## Memory详情

```
GET /api/v1/memory/{id}
```

---

# 八、Registry API

统一管理能力。

## Skill

```
GET /api/v1/skills
```

## MCP Tool

```
GET /api/v1/mcp/tools
```

用于：

Agent Orchestrator能力发现。

---

# 九、Trace API

提供平台观察能力。

```
GET /api/v1/traces/{id}
```

查询：

- Agent链路
- Tool调用
- Error

---

# 十、统一响应模型

```
{
  code,
  message,
  data,
  trace_id,
  timestamp
}
```

所有请求必须生成trace_id。

---

# 十一、认证与权限

预留：

```
API Gateway

Authentication

Authorization

Rate Limit
```

内部阶段：

可先使用内部Token。

---

# 十二、与现有架构关系

```
Client
 |
 v
Platform API Layer
 |
 +---- Agent Service
 |
 +---- Workflow Service
 |
 +---- Memory Service
 |
 +---- Runtime Service
 |
 +---- Trace Service
```

---

# 十三、本阶段范围

完成：

✅ API边界设计

✅ 核心接口规划

✅ 服务调用关系

未实现：

❌ Controller代码

❌ API Gateway

❌ Authentication

❌ OpenAPI文档生成

属于后续实现阶段。
