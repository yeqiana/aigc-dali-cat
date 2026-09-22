# Story OS V3 Phase4-P4.4 Memory Learning Loop 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 4-P4.4 目标：

建立 Memory 从产生、评价、沉淀到优化的闭环。

Memory 不应该只是保存历史数据，而应该能够让 Agent 越来越好。

整体：

```
Agent Execution
        |
        v
Result Analysis
        |
        v
Memory Extraction
        |
        v
Memory Evaluation
        |
        v
Memory Update
        |
        v
Future Agent Improvement
```

---

# 二、设计原则

## 1. Memory来自事实

来源：

```
Trace
Event
Artifact
Agent Execution Record
Review Result
```

禁止：

- Agent自行生成虚假经验
- 未执行结果直接进入Memory

---

## 2. Memory不是状态机

Runtime状态：

```
Redis
```

历史事实：

```
MySQL Event / Trace / Artifact
```

经验：

```
Memory System
```

三者分离。

---

# 三、Learning Loop架构

```
             Agent Runtime
                   |
                   v
          Agent Execution Record
                   |
                   v
          Memory Extractor
                   |
                   v
          Memory Evaluator
                   |
                   v
          Memory Store
                   |
                   v
          Memory Retrieval
                   |
                   v
              Agent Context
```

---

# 四、核心模块

## 1. Memory Extractor

作用：

从执行结果中提取候选经验。

输入：

```
execution_result
trace
artifact
review
```

输出：

```
memory_candidate
```

例如：

```
某类视觉Prompt导致人物一致性提升
```

---

## 2. Memory Evaluator

判断经验是否值得保存。

评价维度：

```
confidence
importance
reusability
```

例如：

一次成功：

低权重。

多次验证：

提高权重。

---

## 3. Memory Consolidator

负责经验合并。

例如：

多个类似经验：

```
雨天摄影Prompt有效

雨夜摄影Prompt有效

低光雨景Prompt有效
```

合并：

```
低光环境视觉生成策略
```

---

## 4. Memory Feedback Processor

接收未来使用反馈。

例如：

Memory被召回：

```
Prompt策略A
```

执行结果：

```
成功
```

提升Memory评分。

失败：

降低可信度。

---

# 五、核心数据模型扩展

## 1. memory_candidate

候选记忆。

字段：

```sql
id bigint unsigned
source_execution_id bigint unsigned
memory_type varchar(32)
content json
confidence decimal(5,2)
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

状态：

```
PENDING
APPROVED
REJECTED
```

---

## 2. memory_learning_event

记录学习过程。

字段：

```sql
id bigint unsigned
memory_id bigint unsigned
event_type varchar(64)
source_id bigint unsigned
result json
created_time datetime(3)
```

例如：

```
CREATE
UPDATE
MERGE
DEGRADE
```

---

## 3. memory_score_history

记录Memory变化。

字段：

```sql
id bigint unsigned
memory_id bigint unsigned
score_type varchar(64)
score_value decimal(5,2)
reason varchar(512)
created_time datetime(3)
```

---

# 六、Memory生命周期

```
Candidate
    |
    v
Evaluating
    |
    v
Active Memory
    |
    +---------+
    |         |
    v         v
Updated   Deprecated
```

---

# 七、与Agent Runtime关系

完整闭环：

```
Workflow
   |
Agent Orchestrator
   |
Agent Runtime
   |
Execution Record
   |
Memory Learning Loop
   |
Memory Store
   |
Retrieval
   |
Agent Context
```

---

# 八、本阶段范围

完成：

✅ Memory学习闭环设计

✅ Memory提取机制

✅ Memory评价机制

✅ Memory反馈机制

未实现：

❌ Memory Extractor代码

❌ 自动学习Pipeline

❌ 向量数据库接入

❌ 在线强化学习

这些属于后续工程阶段。
