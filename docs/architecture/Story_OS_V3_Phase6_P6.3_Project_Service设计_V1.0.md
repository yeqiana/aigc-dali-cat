# Story OS V3 Phase 6-P6.3 Project Service 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

---

# 一、设计目标

Phase 6-P6.3 目标：

将 Story OS 从单 Episode 生产系统升级为多项目 AI Agent 平台。

当前：

```
Story OS
    |
 Episode
```

演进：

```
Tenant
   |
Project
   |
Episode
   |
Workflow / Agent / Artifact
```

---

# 二、Project Service 定位

Project Service 负责：

- 项目生命周期管理
- 项目成员管理
- 项目资源隔离
- 项目配置管理
- 项目运行上下文管理

不负责：

- Workflow执行
- Agent调度
- Runtime执行
- Memory推理

边界：

```
Project Service
负责资源归属

Workflow Service
负责流程

Agent Service
负责能力

Runtime
负责执行
```

---

# 三、核心模型

## 1. project

项目主实体。

例如：

```
AI短视频故事生产
小说视觉化项目
```

字段：

```sql
id bigint unsigned
project_code varchar(64)
project_name varchar(128)
project_type varchar(32)
status varchar(32)
config_data json
created_time datetime(3)
updated_time datetime(3)
```

---

# 四、Episode关系

Project作为Episode上层容器。

关系：

```
Project
   |
   +---- Episode
```

Episode继续保持现有状态模型：

```
episode-state.json
```

Project不替代Episode状态。

---

# 五、项目成员模型

## project_member

管理：

```
用户
 |
项目
 |
角色
```

字段：

```sql
id bigint unsigned
project_id bigint unsigned
user_id bigint unsigned
role_code varchar(32)
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

角色示例：

```
OWNER
EDITOR
OPERATOR
VIEWER
```

---

# 六、项目资源绑定

## project_resource_binding

管理项目可使用资源。

例如：

```
Project A
 |
 +-- Story Agent
 +-- Visual Agent
 +-- Image MCP
 +-- Memory Scope
```

字段：

```sql
id bigint unsigned
project_id bigint unsigned
resource_type varchar(64)
resource_id bigint unsigned
permission varchar(32)
created_time datetime(3)
```

---

# 七、项目配置

## project_config

保存项目级配置。

例如：

```json
{
 "image_style":"M00",
 "default_model":"gpt-image-2",
 "runtime_mode":"WORK"
}
```

规则：

- 配置属于项目
- 不覆盖全局配置
- 运行时读取生成Context

---

# 八、运行上下文

## project_context

提供：

```
Project
  |
  Runtime Context
  |
  Agent Context
```

例如：

- 项目风格
- 默认Agent
- Memory范围
- 权限范围

---

# 九、执行链路

完整链路：

```
User
 |
Project
 |
Workflow
 |
Agent
 |
Runtime
 |
Artifact
```

---

# 十、Phase 6 当前状态

```
Phase 6 Productization

├── P6.1 Web Console
│      ✅
│
├── P6.2 Identity & Permission
│      ✅
│
└── P6.3 Project Service
       ✅
```

下一步：

```
Phase 6-P6.4

Config Center 设计
```

目标：

统一管理：

- Model配置
- Provider配置
- Runtime配置
- Agent配置
- Skill配置
