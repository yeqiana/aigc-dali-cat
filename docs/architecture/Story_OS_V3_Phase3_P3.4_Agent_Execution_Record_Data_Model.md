# Story OS V3 Phase 3-P3.4 Agent Execution Record 数据模型设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 3-P3.4 目标：

记录一次 Agent 运行事实。

解决问题：

> Agent 为什么执行？调用了什么能力？产生什么结果？消耗什么资源？

执行记录必须可追溯。

---

# 二、设计原则

遵循 Story OS V3 数据规范：

- bigint unsigned 主键
- snake_case命名
- datetime(3)
- status枚举
- JSON仅保存扩展配置

核心原则：

Agent Execution 是事实记录。

不是：

- Workflow状态
- Task状态替代品
- Runtime状态缓存

关系：

```
Workflow
   |
   v
Task
   |
   v
Agent Execution Record
   |
   +---- Skill Execution
   |
   +---- Tool Execution
   |
   +---- Trace
   |
   +---- Artifact
```

---

# 三、核心模型

## 1. agent_execution

作用：

记录一次Agent执行实例。

字段：

```sql
id bigint unsigned
execution_no varchar(64)
agent_id bigint unsigned
agent_version_id bigint unsigned
workflow_run_id bigint unsigned
task_id bigint unsigned
execution_type varchar(32)
status varchar(32)
input_context json
output_result json
started_time datetime(3)
finished_time datetime(3)
created_time datetime(3)
updated_time datetime(3)
```

说明：

execution_no全局唯一。

绑定具体Agent版本，保证历史可复现。

---

# 四、Agent Execution 状态

建议：

```
PENDING

RUNNING

SUCCESS

FAILED

CANCELLED

TIMEOUT
```

生命周期：

```
PENDING
   |
RUNNING
   |
+--+--+
|     |
SUCCESS FAILED
```

---

# 五、Skill执行记录

## 2. agent_skill_execution

作用：

记录Agent调用Skill过程。

字段：

```sql
id bigint unsigned
agent_execution_id bigint unsigned
skill_id bigint unsigned
skill_version_id bigint unsigned
status varchar(32)
input_data json
output_data json
started_time datetime(3)
finished_time datetime(3)
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
Visual Agent
    |
    |
image_prompt_compile
```

---

# 六、Tool执行记录

## 3. agent_tool_execution

作用：

记录MCP工具调用。

字段：

```sql
id bigint unsigned
agent_execution_id bigint unsigned
tool_id bigint unsigned
mcp_server_id bigint unsigned
status varchar(32)
request_data json
response_data json
error_message varchar(512)
started_time datetime(3)
finished_time datetime(3)
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
Image Agent
    |
    generate_image MCP Tool
```

---

# 七、Context Snapshot

## 4. agent_context_snapshot

作用：

保存Agent执行上下文快照。

用于：

- 调试
- 重放
- 失败恢复

字段：

```sql
id bigint unsigned
agent_execution_id bigint unsigned
context_type varchar(32)
context_data json
snapshot_version varchar(32)
created_time datetime(3)
```

例如：

```
Story Context
Character Context
Memory Context
```

---

# 八、Trace关联

Agent Execution 不重复保存Trace。

关联：

```
agent_execution
        |
        |
trace_span
```

来源：

Phase 0 Trace Contract。

---

# 九、Artifact关联

Agent输出结果不直接存文件。

通过：

```
agent_execution
        |
        |
artifact_index
```

关联产物。

例如：

```
Prompt Package
Review Report
Generated Image
```

---

# 十、完整执行链

最终：

```
Workflow Step
      |
      v
Agent Orchestrator
      |
      v
agent_execution
      |
 +------------+
 |            |
 v            v
Skill        MCP Tool
Execution    Execution
      |
      v
Trace/Event/Artifact
```

---

# 十一、与Runtime关系

Runtime负责：

```
执行
调度
重试
资源管理
```

Execution Record负责：

```
记录事实
审计
分析
复盘
```

两者分离。

---

# 十二、本阶段范围

完成：

✅ Agent执行记录

✅ Skill执行记录

✅ Tool执行记录

✅ Context快照

✅ Trace/Artifact关联设计

未实现：

❌ Agent Orchestrator

❌ Execution Service

❌ Runtime接入

❌ Memory调用

属于后续P3.5-P3.6。
