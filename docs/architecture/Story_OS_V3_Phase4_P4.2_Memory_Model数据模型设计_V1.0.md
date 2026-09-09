# Story OS V3 Phase 4-P4.2 Memory Model 数据模型设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 4-P4.2 目标：

建立 Story OS Memory 数据模型。

Memory 不作为普通知识库，而作为 Agent 的经验系统。

核心链路：

```
Agent Runtime
      |
      v
Execution Record
      |
      v
Memory Extractor
      |
      v
Memory Store
      |
      v
Future Agent Context
```

---

# 二、设计原则

遵循 V3 数据规范：

- bigint unsigned 主键
- snake_case命名
- datetime(3)
- status枚举
- JSON只保存扩展数据
- 向量数据作为检索索引，不作为事实来源

禁止：

- Memory替代Workflow
- Memory保存Runtime实时状态
- 一个JSON保存全部历史经验
- 直接把Embedding作为唯一数据

---

# 三、Memory类型模型

Memory分为：

```
WORKING

EPISODIC

SEMANTIC

PROCEDURAL
```

说明：

## Working Memory

短期上下文。

来源：

```
Redis Runtime State
```

生命周期：

一次执行。

---

## Episodic Memory

事件经验。

来源：

```
Agent Execution
Trace
Event
Review
```

例如：

```
某次图片生成失败
某次故事发布效果优秀
```

---

## Semantic Memory

长期知识。

例如：

```
优秀故事结构规律
视觉风格经验
Prompt经验
```

---

## Procedural Memory

流程经验。

例如：

```
最佳生产步骤
失败恢复策略
```

---

# 四、核心数据模型

## 1. memory_item

核心记忆实体。

字段：

```sql
id bigint unsigned
memory_type varchar(32)
memory_key varchar(128)
title varchar(256)
content text
source_type varchar(64)
source_id bigint unsigned
importance_score decimal(5,2)
confidence_score decimal(5,2)
status varchar(32)
ext_config json
created_time datetime(3)
updated_time datetime(3)
```

说明：

source_id关联产生该Memory的事实来源。

例如：

```
agent_execution_id
trace_id
artifact_id
```

---

# 五、Memory关系模型

## 2. memory_relation

作用：

建立Memory之间关联。

字段：

```sql
id bigint unsigned
source_memory_id bigint unsigned
target_memory_id bigint unsigned
relation_type varchar(64)
relation_score decimal(5,2)
created_time datetime(3)
```

例如：

```
失败案例
 |
导致
 |
修复策略
```

---

# 六、向量索引模型

## 3. memory_embedding

作用：

语义检索。

字段：

```sql
id bigint unsigned
memory_id bigint unsigned
embedding_model varchar(64)
vector_dimension int
vector_reference varchar(256)
status varchar(32)
created_time datetime(3)
```

说明：

不直接保存完整向量。

可支持：

```
pgvector
Milvus
其他向量数据库
```

---

# 七、反馈模型

## 4. memory_feedback

作用：

判断Memory是否有效。

字段：

```sql
id bigint unsigned
memory_id bigint unsigned
feedback_type varchar(64)
feedback_score decimal(5,2)
execution_id bigint unsigned
feedback_data json
created_time datetime(3)
```

例如：

```
Memory推荐Prompt

执行成功

评分提升
```

---

# 八、访问控制模型

## 5. memory_access_policy

作用：

控制Agent可访问Memory范围。

字段：

```sql
id bigint unsigned
memory_type varchar(32)
agent_id bigint unsigned
access_level varchar(32)
policy_config json
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
Review Agent

只能读取视觉审核经验
```

---

# 九、实体关系

整体：

```
memory_item
      |
      +-------- memory_embedding
      |
      +-------- memory_relation
      |
      +-------- memory_feedback
      |
      +-------- memory_access_policy
```

---

# 十、与Agent系统关系

完整链路：

```
Workflow
   |
Agent Orchestrator
   |
Agent Runtime
   |
Agent Execution Record
   |
Memory Extractor
   |
memory_item
   |
Memory Retrieval
   |
Agent Context
```

---

# 十一、本阶段范围

完成：

✅ Memory核心模型

✅ Memory分类体系

✅ Memory关系模型

✅ Embedding索引设计

✅ Feedback闭环

✅ Access Policy

未实现：

❌ Memory Retrieval Service

❌ Memory Extractor

❌ Vector Database接入

❌ Agent自动学习

以上属于后续 P4.3/P4.4。
