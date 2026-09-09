# Story OS V3 Phase 3-P3.1 Agent Model 数据模型设计 V1.0

更新时间：
2026-09-09

分支：
story-platform-v3

---

# 一、设计目标

Phase 3 目标：

将 Story OS 从：

```
Workflow驱动生产系统
```

演进为：

```
Agent驱动内容生产操作系统
```

但保持职责边界：

```
Workflow
负责流程约束

Agent
负责智能决策

Runtime
负责执行
```

P3.1 只建设 Agent 数据模型，不实现 Agent 自动调度。

---

# 二、设计原则

数据库规范：

- bigint unsigned 主键
- snake_case 命名
- datetime(3)
- created_time / updated_time 公共字段
- status 使用枚举字符串
- JSON 仅保存扩展配置

禁止：

- Agent 表保存完整Prompt
- Agent表替代Workflow
- Agent表直接保存运行状态事实
- 一个JSON保存完整Agent DAG

---

# 三、核心模型关系

```text
agent
  |
  | 1:N
  |
agent_version
  |
  | 1:N
  |
agent_execution

agent
  |
  | N:M
  |
agent_skill_relation
```

---

# 四、agent

## 作用

Agent定义。

表示一个具备特定职责的智能角色。

例如：

```
STORY_AGENT
VISUAL_AGENT
REVIEW_AGENT
```

## 表结构

```sql
CREATE TABLE agent (
    id bigint unsigned PRIMARY KEY,
    agent_code varchar(64) NOT NULL,
    agent_name varchar(128) NOT NULL,
    agent_type varchar(32) NOT NULL,
    description varchar(512),
    status varchar(32) NOT NULL,
    config_data json,
    created_time datetime(3) NOT NULL,
    updated_time datetime(3) NOT NULL
);
```

## 字段说明

|字段|说明|
|-|-|
|agent_code|唯一编码|
|agent_name|展示名称|
|agent_type|类型，如 STORY/VISUAL/REVIEW|
|config_data|扩展配置|
|status|ACTIVE/DISABLED|

---

# 五、agent_version

## 作用

Agent版本管理。

原因：

Agent能力会持续优化，历史执行必须知道使用哪个版本。

## 表结构

```sql
CREATE TABLE agent_version (
    id bigint unsigned PRIMARY KEY,
    agent_id bigint unsigned NOT NULL,
    version varchar(32) NOT NULL,
    system_prompt text,
    model_config json,
    skill_config json,
    status varchar(32) NOT NULL,
    created_time datetime(3) NOT NULL,
    updated_time datetime(3) NOT NULL
);
```

## 说明

保存：

```
Agent版本
模型配置
Skill绑定快照
```

不保存：

```
运行日志
Trace
Event
```

---

# 六、agent_execution

## 作用

记录一次Agent执行事实。

对应：

```
一次Agent调用
```

## 表结构

```sql
CREATE TABLE agent_execution (
    id bigint unsigned PRIMARY KEY,
    agent_id bigint unsigned NOT NULL,
    agent_version_id bigint unsigned NOT NULL,
    workflow_run_id bigint unsigned,
    workflow_step_id bigint unsigned,
    execution_status varchar(32) NOT NULL,
    input_context json,
    output_result json,
    started_time datetime(3),
    finished_time datetime(3),
    created_time datetime(3) NOT NULL,
    updated_time datetime(3) NOT NULL
);
```

## 状态

```
CREATED
RUNNING
SUCCESS
FAILED
CANCELLED
```

---

# 七、agent_skill_relation

## 作用

Agent与Skill关联。

例如：

```
Visual Agent
 |
 +-- image_prompt_compile
 +-- visual_review
```

## 表结构

```sql
CREATE TABLE agent_skill_relation (
    id bigint unsigned PRIMARY KEY,
    agent_id bigint unsigned NOT NULL,
    skill_id bigint unsigned NOT NULL,
    priority int NOT NULL DEFAULT 0,
    status varchar(32) NOT NULL,
    created_time datetime(3) NOT NULL,
    updated_time datetime(3) NOT NULL
);
```

---

# 八、与已有模块关系

## Workflow

关系：

```
workflow_step
        |
        |
agent_execution
```

Workflow决定：

```
什么时候调用Agent
```

Agent决定：

```
如何完成任务
```

---

## Trace

Agent执行产生：

```
Trace Span
Event
Artifact
```

但Agent表不保存这些历史。

---

## Runtime

Runtime负责：

```
真正运行Agent
```

Agent Model只描述：

```
是谁
什么版本
执行记录
拥有能力
```

---

# 九、后续扩展

Phase 3 后续增加：

```
Skill Registry

MCP Registry

Agent Orchestrator

Agent Context
```

本阶段不提前设计Memory。

---

# 十、验收标准

完成：

- Agent基础模型明确
- Agent版本可追踪
- Agent执行可审计
- Workflow与Agent职责分离
- 支持后续Orchestrator建设

---

# 结论

P3.1 建立 Agent 平台的数据基础。

它不是替代 Workflow，而是在 Workflow 约束下提供智能执行能力。
