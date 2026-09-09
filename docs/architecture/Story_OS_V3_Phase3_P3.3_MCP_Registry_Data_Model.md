# Story OS V3 Phase 3-P3.3 MCP Registry 数据模型设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 3-P3.3 目标：

建立 MCP Registry 数据模型。

MCP Registry 负责管理 Agent 可访问的外部工具能力。

整体能力链：

```
Agent
  |
  v
Skill
  |
  v
MCP Registry
  |
  v
Tool
  |
  v
Runtime Execution
```

---

# 二、职责边界

## Workflow

负责：

```
什么时候执行
```

---

## Agent

负责：

```
选择能力
```

---

## Skill

负责：

```
完成什么类型任务
```

---

## MCP Tool

负责：

```
调用什么外部能力
```

---

# 三、设计原则

遵循 Story OS V3 数据规范：

- bigint unsigned 主键
- snake_case命名
- datetime(3)
- status枚举
- JSON只保存扩展配置

禁止：

- MCP表保存业务流程
- Tool直接绑定Episode
- Tool调用结果作为状态机
- JSON保存完整工具链路

---

# 四、核心模型

## 1. mcp_server

作用：

定义一个 MCP 服务实例。

例如：

```
image_generation_server
memory_search_server
file_operation_server
```

字段：

```sql
id bigint unsigned
server_code varchar(64)
server_name varchar(128)
server_type varchar(32)
endpoint varchar(512)
status varchar(32)
config_data json
created_time datetime(3)
updated_time datetime(3)
```

说明：

server代表工具提供方。

例如：

```
OpenAI MCP Server
内部图片服务
Memory MCP Server
```

---

# 五、MCP Tool模型

## 2. mcp_tool

作用：

定义具体可调用工具。

字段：

```sql
id bigint unsigned
server_id bigint unsigned
tool_code varchar(64)
tool_name varchar(128)
description varchar(512)
tool_type varchar(32)
status varchar(32)
input_schema json
output_schema json
config_data json
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
generate_image

review_image

search_memory
```

---

# 六、Tool Permission

## 3. tool_permission

作用：

控制谁可以调用Tool。

字段：

```sql
id bigint unsigned
tool_id bigint unsigned
permission_type varchar(32)
permission_config json
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
IMAGE_AGENT
允许调用

generate_image
```

---

# 七、Agent Tool Binding

## 4. agent_tool_binding

作用：

建立Agent到MCP Tool访问关系。

关系：

```
Agent
 |
绑定
 |
Tool
```

字段：

```sql
id bigint unsigned
agent_id bigint unsigned
tool_id bigint unsigned
binding_type varchar(32)
status varchar(32)
config_data json
created_time datetime(3)
updated_time datetime(3)
```

---

# 八、Tool Execution Record预留

## 5. tool_execution

说明：

实际执行记录不属于Registry核心。

属于后续：

P3.4 Agent Execution Record

模型预留：

```sql
id bigint unsigned
tool_id bigint unsigned
agent_execution_id bigint unsigned
request_data json
response_data json
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

---

# 九、实体关系

整体关系：

```
mcp_server
     |
     | 1:N
     v
mcp_tool
     |
     +-------------+
     |             |
     v             v
permission   agent_binding

agent
     |
     v
agent_execution
     |
     v
mcp_tool_execution
```

---

# 十、Tool生命周期

状态：

```
DRAFT

TESTING

ACTIVE

DEPRECATED

DISABLED
```

流程：

```
DRAFT
  |
TESTING
  |
ACTIVE
  |
DEPRECATED
  |
DISABLED
```

---

# 十一、与Skill关系

Skill不直接保存Tool。

正确：

```
Agent
 |
Skill
 |
MCP Tool
```

原因：

同一个Skill未来可能：

- 使用不同模型
- 使用不同MCP服务
- 根据环境切换Tool

---

# 十二、与Runtime关系

未来执行链：

```
Workflow Step
      |
      v
Agent Orchestrator
      |
      v
Skill Registry
      |
      v
MCP Registry
      |
      v
Agent Runtime
      |
      v
Trace/Event/Artifact
```

---

# 十三、本阶段范围

完成：

✅ MCP Server模型

✅ MCP Tool模型

✅ 权限模型

✅ Agent Tool绑定模型

未实现：

❌ MCP Gateway

❌ Tool调用协议实现

❌ Runtime Tool Adapter

❌ 权限校验服务

以上属于后续 P3.4-P3.6。
