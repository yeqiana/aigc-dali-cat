# Story OS V3 Phase6-P6.2 Identity & Permission 权限体系设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 6-P6.2 目标：

建立 Story OS 平台身份认证与权限控制体系。

从：

```
单用户工具系统
```

升级：

```
多用户
多项目
多资源隔离
AI Agent权限治理平台
```

---

# 二、设计原则

遵循：

- 用户身份与业务资源分离
- 权限控制资源访问，不控制业务流程
- RBAC为基础模型
- 支持未来ABAC扩展
- 不影响已有Runtime执行模型

禁止：

- Permission替代Workflow规则
- Role硬编码业务逻辑
- Agent自行绕过权限校验

---

# 三、整体模型

```
User
 |
 v
Role
 |
 v
Permission
 |
 v
Resource
```

多项目扩展：

```
User
 |
Project Member
 |
Project Role
 |
Resource Permission
```

---

# 四、核心模型

## 1. user_identity

用户身份。

字段：

```sql
id bigint unsigned
username varchar(128)
email varchar(128)
password_hash varchar(256)
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

职责：

- 登录身份
- 基础账户状态

---

# 2. role_definition

角色定义。

例如：

```
ADMIN
PROJECT_OWNER
OPERATOR
VIEWER
```

字段：

```sql
id bigint unsigned
role_code varchar(64)
role_name varchar(128)
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

---

# 3. permission_definition

权限定义。

例如：

```
agent.read
agent.execute
workflow.run
memory.read
mcp.invoke
```

字段：

```sql
id bigint unsigned
permission_code varchar(128)
permission_name varchar(128)
resource_type varchar(64)
action varchar(64)
created_time datetime(3)
updated_time datetime(3)
```

---

# 4. user_role_relation

用户角色关系。

```sql
id bigint unsigned
user_id bigint unsigned
role_id bigint unsigned
created_time datetime(3)
```

---

# 5. role_permission_relation

角色权限关系。

```sql
id bigint unsigned
role_id bigint unsigned
permission_id bigint unsigned
created_time datetime(3)
```

---

# 五、项目级权限

## project_member

支持多人协作。

字段：

```sql
id bigint unsigned
project_id bigint unsigned
user_id bigint unsigned
role_id bigint unsigned
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
项目A

张三 OWNER
李四 OPERATOR
王五 VIEWER
```

---

# 六、资源权限模型

统一资源：

```
Agent
Workflow
Skill
MCP
Memory
Artifact
Project
```

权限判断：

```
User
 |
Role
 |
Permission
 |
Resource
```

---

# 七、AI Agent权限特殊设计

Agent调用链：

```
User Request

|

Permission Check

|

Agent Orchestrator

|

Skill Permission

|

MCP Permission

|

Runtime Execute
```

例如：

Visual Agent：

允许：

```
image_generation
image_review
```

禁止：

```
memory_admin
system_config
```

---

# 八、与已有模块关系

```
Web Console

|

Permission Service

|

Agent Service
Workflow Service
Memory Service
Runtime Service
```

所有平台服务统一经过权限校验。

---

# 九、后续扩展

预留：

```
Tenant

Organization

Quota

Audit Log

ABAC Policy
```

用于未来 SaaS 化。

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
├── P6.3 Project Service
│      待开始
│
├── P6.4 Config Center
│      待开始
│
├── P6.5 Plugin Extension
│      待开始
│
└── P6.6 SaaS Ready
       待开始
```
