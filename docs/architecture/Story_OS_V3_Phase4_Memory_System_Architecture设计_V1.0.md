# Story OS V3 Phase 4 Memory System Architecture设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、Phase 4目标

Phase 4 建设 Story OS Memory System。

目标：

让 Agent 不只是执行任务，而能够基于历史经验持续优化。

从：

```
Agent
 ↓
执行
 ↓
结束
```

升级：

```
Agent
 ↓
执行
 ↓
产生经验
 ↓
Memory沉淀
 ↓
未来任务检索复用
```

---

# 二、设计原则

Memory不是简单聊天记录。

不是：

```
Vector DB = Memory
```

正确：

```
Memory
=
事实
+
经验
+
规则
+
偏好
+
反馈
```

---

# 三、Memory层次设计

## 1. Working Memory

短期上下文。

来源：

```
Agent Context
Task Context
Workflow Context
```

生命周期：

一次Execution。

存储：

Redis Runtime State

---

## 2. Episodic Memory

事件记忆。

记录：

```
发生过什么

结果如何

为什么失败
```

来源：

```
Agent Execution Record
Trace
Event
Review
```

存储：

MySQL + Vector Index

---

## 3. Semantic Memory

知识记忆。

例如：

```
什么样的故事容易成功

什么视觉风格适合账号

哪些Prompt有效
```

来源：

复盘结果。

---

## 4. Procedural Memory

流程经验。

例如：

```
生产图片最佳步骤

审核规则

失败恢复策略
```

---

# 四、整体架构

```
                 Agent Runtime
                       |
                       v
              Memory Gateway
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
 Working Memory  Episodic Memory Semantic Memory
        |
        v
 Redis          MySQL + Vector
```

---

# 五、核心模型

## memory_item

统一Memory实体。

字段：

```sql
id bigint unsigned
memory_type varchar(32)
content text
summary varchar(512)
source_type varchar(64)
source_id bigint unsigned
importance_score decimal(5,2)
status varchar(32)
metadata json
created_time datetime(3)
updated_time datetime(3)
```

---

## memory_embedding

向量检索索引。

字段：

```sql
id bigint unsigned
memory_id bigint unsigned
embedding_model varchar(64)
vector_data json
created_time datetime(3)
```

说明：

向量只是检索能力，不是事实来源。

---

## memory_feedback

记录Memory有效性。

字段：

```sql
id bigint unsigned
memory_id bigint unsigned
feedback_type varchar(32)
feedback_result json
created_time datetime(3)
```

---

# 六、Memory生命周期

```
Execution

 ↓

Extraction

 ↓

Evaluation

 ↓

Store

 ↓

Retrieve

 ↓

Feedback

 ↓

Update
```

---

# 七、与Agent关系

未来：

```
Agent Orchestrator
        |
        v
Memory Retrieval
        |
        v
Agent Context
        |
        v
Agent Runtime
```

Agent不能直接修改Memory。

必须经过Memory Gateway。

---

# 八、与现有系统关系

保持边界：

```
Workflow
负责流程

Agent
负责智能

Memory
负责经验

Runtime
负责执行
```

---

# 九、Phase 4拆分

## P4.1 Memory Architecture

当前阶段。

完成：

- Memory分类
- 生命周期
- 数据边界

---

## P4.2 Memory Model

设计：

```
memory_item
memory_relation
memory_embedding
```

---

## P4.3 Memory Retrieval

设计：

```
semantic search
context ranking
memory injection
```

---

## P4.4 Memory Learning Loop

设计：

```
执行
 ↓
反馈
 ↓
学习
 ↓
优化Agent
```

---

# 十、禁止事项

禁止：

- 使用Memory替代Workflow
- 使用Memory保存Runtime状态
- 所有内容直接向量化
- Agent无限读取全部历史

---

# 十一、阶段结论

Phase 4目标不是增加一个数据库。

而是建立：

```
Story OS Experience System
```

让Agent具备：

```
执行能力
+
历史经验
+
持续优化能力
```
