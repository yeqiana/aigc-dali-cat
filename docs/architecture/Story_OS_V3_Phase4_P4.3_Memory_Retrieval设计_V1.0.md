# Story OS V3 Phase4-P4.3 Memory Retrieval 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 4-P4.3 目标：

建立 Memory 检索能力，让 Agent 在执行任务时能够主动获取历史经验。

从：

```
Agent

执行一次任务
```

升级：

```
Agent

↓

检索历史经验

↓

结合当前上下文

↓

生成更优执行策略
```

---

# 二、设计原则

Memory Retrieval 不负责：

- 修改Workflow
- 替代Agent决策
- 直接执行任务

职责：

```
找到相关经验

提供上下文

辅助Agent决策
```

核心原则：

> Retrieval 提供参考，不直接决定答案。

---

# 三、整体架构

```
                 Agent Runtime

                       |
                       v

              Memory Gateway

                       |

        +--------------+--------------+
        |                             |
        v                             v

 Semantic Retrieval             Metadata Filter

        |                             |
        +--------------+--------------+
                       |
                       v

              Memory Ranking

                       |
                       v

              Context Builder

                       |
                       v

              Agent Context
```

---

# 四、核心模块设计

## 1. Memory Gateway

统一Memory访问入口。

职责：

- 接收Agent检索请求
- 校验访问权限
- 调用检索流程
- 返回Memory Context

禁止：

Agent直接访问数据库。

---

# 五、Retrieval Pipeline

## Step 1 Query Builder

将当前任务转换为检索请求。

输入：

```
task_context
agent_type
skill_type
current_goal
```

输出：

```json
{
 "query":"image prompt generation failure",
 "memory_type":["EPISODIC","PROCEDURAL"]
}
```

---

## Step 2 Metadata Filter

第一层过滤。

条件：

```
memory_type
agent_scope
skill_scope
status
```

作用：

减少无效召回。

---

## Step 3 Semantic Retrieval

基于Embedding检索。

来源：

```
memory_embedding
```

支持：

- 向量搜索
- 相似度匹配
- 语义召回

---

## Step 4 Ranking

对候选Memory排序。

评分因素：

```
semantic_score

importance_score

confidence_score

recent_usage_score

feedback_score
```

综合形成：

```
retrieval_score
```

---

## Step 5 Context Builder

将Memory转换为Agent可消费上下文。

例如：

```
历史成功案例：
某类视觉Prompt在雨天场景表现更好。

历史失败案例：
人物一致性不足导致返修。
```

---

# 六、核心数据模型

## 1. memory_retrieval_request

记录一次检索请求。

字段：

```sql
id bigint unsigned
agent_id bigint unsigned
task_id bigint unsigned
query_text varchar(1024)
request_context json
status varchar(32)
created_time datetime(3)
```

---

## 2. memory_retrieval_result

记录召回结果。

字段：

```sql
id bigint unsigned
request_id bigint unsigned
memory_id bigint unsigned
retrieval_score decimal(10,6)
rank_no int
created_time datetime(3)
```

---

## 3. memory_context_snapshot

保存注入Agent的最终Memory上下文。

字段：

```sql
id bigint unsigned
request_id bigint unsigned
agent_execution_id bigint unsigned
context_data json
created_time datetime(3)
```

---

# 七、与Agent Runtime集成

执行链：

```
Agent Runtime启动

↓

Memory Gateway

↓

Retrieval Pipeline

↓

Context Builder

↓

Agent Context

↓

Agent执行
```

---

# 八、与现有模块关系

## Agent Execution Record

记录：

```
发生了一次执行
```

Memory Retrieval Record记录：

```
执行前参考了什么经验
```

---

## Trace

Trace记录：

```
运行过程
```

Memory记录：

```
可复用经验
```

---

# 九、本阶段范围

完成：

✅ Memory Gateway设计

✅ Retrieval Pipeline设计

✅ Ranking机制设计

✅ Context Injection设计

未实现：

❌ 向量数据库接入

❌ Embedding生成服务

❌ 自动Memory提取

❌ Learning Loop

以上进入P4.4。
