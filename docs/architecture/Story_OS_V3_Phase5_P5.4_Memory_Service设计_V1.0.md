# Story OS V3 Phase 5-P5.4 Memory Service 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 5-P5.4 目标：

将 Phase 4 Memory System 能力封装为平台服务。

从：

```
Memory模块能力
```

升级为：

```
Memory Service
```

为 Agent Runtime、Agent Orchestrator 提供统一记忆能力。

---

# 二、服务定位

Memory Service负责：

```
Memory存储

Memory检索

Memory评分

Memory生命周期管理

Memory学习闭环
```

不负责：

```
Agent决策

Workflow流程

Runtime执行
```

边界：

```
Agent
决定需要什么经验

Memory Service
提供什么经验

Runtime
负责执行
```

---

# 三、整体架构

```
Agent Runtime

      |
      v

Memory Gateway

      |
      +----------------+
      |                |
      v                v

Memory Retrieval   Memory Learning

      |                |
      v                v

Memory Store    Memory Evaluator

      |
      v

MySQL + Vector Store
```

---

# 四、核心模块

## 1. Memory Gateway

统一访问入口。

职责：

- 接收Agent查询
- 权限校验
- 返回Memory Context

禁止Agent直接访问底层存储。

---

# 2. Memory Query Service

负责检索请求处理。

输入：

```
agent_type
skill_type
task_context
query
```

输出：

```
Memory Context
```

---

# 3. Memory Retrieval Service

负责：

```
Metadata Filter

Semantic Search

Ranking

Context Assembly
```

流程：

```
Query

↓

Filter

↓

Vector Retrieval

↓

Score Ranking

↓

Context Builder
```

---

# 4. Memory Learning Service

负责经验沉淀。

流程：

```
Agent Execution

↓

Memory Extractor

↓

Memory Candidate

↓

Evaluator

↓

Memory Store
```

---

# 5. Memory Lifecycle Manager

管理：

```
CREATE

UPDATE

MERGE

DEPRECATE

ARCHIVE
```

避免Memory无限增长。

---

# 五、API设计

## Memory检索

```http
POST /api/v1/memory/search
```

请求：

```json
{
 "query":"visual generation experience",
 "memory_type":["EPISODIC"]
}
```

---

## Memory详情

```http
GET /api/v1/memory/{id}
```

---

## 写入Memory

```http
POST /api/v1/memory
```

来源：

```
Agent Execution
Review
Learning Loop
```

---

## Memory反馈

```http
POST /api/v1/memory/{id}/feedback
```

用于更新：

```
confidence
score
usage_count
```

---

# 六、数据关系

```
Memory Service

 |
 +---- memory_item
 |
 +---- memory_embedding
 |
 +---- memory_relation
 |
 +---- memory_feedback
 |
 +---- memory_learning_event
```

---

# 七、与平台服务关系

完整链路：

```
Workflow Service

        |
        v

Agent Service

        |
        v

Agent Orchestrator

        |
        +------------+
        |            |
        v            v

Runtime      Memory Service

        |
        v

Execution Record

        |
        v

Memory Learning
```

---

# 八、重要约束

禁止：

- Memory替代Workflow
- Memory修改历史事实
- Memory直接驱动流程跳转
- Vector数据库成为唯一事实源

原则：

```
Event / Trace / Artifact
是事实

Memory
是经验
```

---

# 九、Phase 5状态

```
Phase 5 Platform Service

├── P5.1 Platform API Layer
│      ✅
│
├── P5.2 Agent Service
│      ✅
│
├── P5.3 Workflow Service
│      ✅
│
└── P5.4 Memory Service
       ✅
```
