# Story OS V3 Phase6-P6.4 Config Center 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

---

# 一、设计目标

Config Center 目标：

将分散在代码、环境变量、JSON配置中的运行参数统一平台化管理。

从：

```
代码配置
环境配置
Agent配置
Runtime配置
```

升级为：

```
Config Center
        |
        +---- Agent
        +---- Skill
        +---- MCP
        +---- Workflow
        +---- Runtime
        +---- Project
```

---

# 二、设计原则

遵循：

- 配置与代码分离
- 配置版本化
- 配置可追踪
- 配置可回滚
- 项目级覆盖全局配置

禁止：

- 将业务事实存入配置
- 使用配置替代数据库模型
- 无版本直接修改生产配置

---

# 三、配置层级

采用多级覆盖：

```
System Default
      |
      v
Platform Config
      |
      v
Project Config
      |
      v
Runtime Override
```

优先级：

```
Runtime Override
>
Project
>
Platform
>
Default
```

---

# 四、核心模型

## 1. config_item

配置主体。

字段：

```sql
id bigint unsigned
config_key varchar(128)
config_group varchar(64)
config_scope varchar(32)
status varchar(32)
created_time datetime(3)
updated_time datetime(3)
```

例如：

```
agent.visual.model
runtime.max_retry
workflow.timeout
```

---

# 五、配置版本

## 2. config_version

原因：

生产环境配置必须可回滚。

字段：

```sql
id bigint unsigned
config_id bigint unsigned
version varchar(32)
config_value json
version_status varchar(32)
created_by bigint unsigned
created_time datetime(3)
```

---

# 六、配置绑定

## 3. config_binding

关联资源。

例如：

```
Visual Agent
    |
    使用
    |
image.model.config
```

字段：

```sql
id bigint unsigned
config_id bigint unsigned
resource_type varchar(64)
resource_id bigint unsigned
created_time datetime(3)
```

---

# 七、配置发布

## 4. config_release

记录配置发布过程。

例如：

```
Draft
 |
Review
 |
Published
 |
Rollback
```

---

# 八、配置类型

## Model Config

例如：

```
model provider
model name
temperature
```

---

## Agent Config

例如：

```
prompt template
context limit
behavior config
```

---

## Runtime Config

例如：

```
retry count
worker count
timeout
```

---

## MCP Config

例如：

```
endpoint
permission
quota
```

---

# 九、访问流程

```
Agent Runtime
      |
      v
Config Service
      |
      v
Config Resolver
      |
      v
Effective Config
```

---

# 十、与现有平台关系

完整链路：

```
Project
  |
  v
Config Center
  |
  +---- Agent Service
  +---- Workflow Service
  +---- Runtime Service
  +---- Memory Service
```

---

# 十一、Phase 6 状态

```
Phase 6 Productization

├── P6.1 Web Console
│      ✅
│
├── P6.2 Identity & Permission
│      ✅
│
├── P6.3 Project Service
│      ✅
│
└── P6.4 Config Center
       ✅
```
