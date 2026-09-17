# Story OS V3 Phase7-P7.1 数据库模型落地设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

---

# 一、目标

将 Phase 0-6 的架构设计转换为真实数据库模型。

目标：

```
Architecture

        ↓

Database Schema

        ↓

Repository

        ↓

Service
```

---

# 二、数据库选型

主数据库：

MySQL

职责：

- 业务事实数据
- Agent定义
- Workflow状态
- Execution记录
- Memory元数据
- 权限数据

Redis继续负责：

- Runtime状态
- Lock
- Queue
- Worker Heartbeat

向量存储后续独立：

- pgvector
- Milvus

---

# 三、核心表设计

## Agent领域

```text
agent
agent_version
agent_execution
agent_skill_relation
```

作用：

保存Agent身份、版本和执行事实。

---

## Skill领域

```text
skill_definition
skill_version
skill_capability
skill_policy
```

作用：

保存能力定义。

---

## MCP领域

```text
mcp_server
mcp_tool
tool_permission
agent_tool_binding
```

作用：

保存工具注册与权限。

---

## Workflow领域

```text
workflow_definition
workflow_version
workflow_run
workflow_step
workflow_transition
```

作用：

保存流程定义和运行事实。

---

## Memory领域

```text
memory_item
memory_embedding
memory_relation
memory_feedback
memory_learning_event
```

作用：

保存Agent经验。

---

## Platform领域

```text
project
project_member
config_item
config_version
user_identity
role_definition
permission_definition
```

作用：

支撑平台化。

---

# 四、统一字段规范

所有表：

```sql
id bigint unsigned primary key

created_time datetime(3)

updated_time datetime(3)

status varchar(32)
```

约束：

- snake_case
- 不使用物理删除
- JSON只保存扩展配置

---

# 五、迁移策略

不直接替换现有V2.7。

采用：

```
New Schema

↓

Dual Write

↓

Consistency Check

↓

Read Switch

↓

Old Data Archive
```

---

# 六、优先落地顺序

## 第一批

基础平台：

```
project
user_identity
role_definition
permission_definition
config_item
```

---

## 第二批

核心执行：

```
workflow_definition
workflow_run
workflow_step
agent_execution
```

---

## 第三批

Agent生态：

```
agent
agent_version
skill_definition
mcp_tool
```

---

## 第四批

学习系统：

```
memory_item
memory_feedback
memory_learning_event
```

---

# 七、完成标准

P7.1完成后：

- Schema存在
- Migration可执行
- Repository可访问
- 新旧数据可双写

下一阶段：

P7.2 Platform Service模块骨架。
