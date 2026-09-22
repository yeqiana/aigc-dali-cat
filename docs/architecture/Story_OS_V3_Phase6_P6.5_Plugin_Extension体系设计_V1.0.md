# Story OS V3 Phase6-P6.5 Plugin / Extension 体系设计 V1.0

更新时间：
2026-09-09

项目：
Story OS

---

# 一、设计目标

Phase 6-P6.5目标：

建立 Story OS 扩展生态能力。

从：

```
平台内置能力
```

升级：

```
平台核心
+
可插拔扩展
```

支持：

- Agent Plugin
- Skill Plugin
- MCP Plugin
- Runtime Extension

---

# 二、设计原则

插件负责扩展能力。

插件不允许：

- 修改平台核心逻辑
- 绕过权限体系
- 直接修改Runtime状态
- 破坏Workflow约束

架构：

```
Plugin
  |
Extension API
  |
Platform Service
```

---

# 三、插件体系架构

```

Plugin Registry
        |
        v
Plugin Manager
        |
        +-------------+
        |             |
        v             v
 Agent Plugin   MCP Plugin

        |
        v

Runtime Extension
```

---

# 四、核心模型

## 1. plugin_definition

插件基础定义。

字段：

```sql
id bigint unsigned
plugin_code varchar(64)
plugin_name varchar(128)
plugin_type varchar(32)
description varchar(512)
status varchar(32)
config json
created_time datetime(3)
updated_time datetime(3)
```

类型：

```
AGENT
SKILL
MCP
RUNTIME
```

---

# 五、Plugin Version

## 2. plugin_version

解决插件升级和回滚。

字段：

```sql
id bigint unsigned
plugin_id bigint unsigned
version varchar(32)
release_status varchar(32)
package_info json
created_time datetime(3)
updated_time datetime(3)
```

生命周期：

```
DRAFT
TESTING
ACTIVE
DEPRECATED
```

---

# 六、Plugin Capability

## 3. plugin_capability

描述插件能力。

例如：

```
image_generation
video_generation
custom_review
```

用于：

```
Agent Orchestrator
        |
        v
Capability Discovery
```

---

# 七、Plugin Permission

## 4. plugin_permission

插件权限控制。

例如：

```
允许访问：

image MCP
artifact repository

禁止：
system config
```

与 Phase 6-P6.2 权限体系结合。

---

# 八、Plugin Lifecycle

生命周期：

```
Install
  |
Enable
  |
Running
  |
Disable
  |
Uninstall
```

---

# 九、插件执行边界

执行链：

```
User
 |
Permission Check
 |
Plugin Manager
 |
Plugin Runtime
 |
Platform API
 |
Execution Record
```

所有插件执行必须进入：

```
Trace
Event
Artifact
```

---

# 十、典型场景

## Agent Plugin

新增：

```
Video Agent

Music Agent
```

---

## Skill Plugin

新增：

```
video_caption_generate
style_transfer
```

---

## MCP Plugin

新增：

```
Video Generator MCP
Search MCP
```

---

# 十一、当前阶段范围

完成：

✅ Plugin模型

✅ Plugin版本

✅ Capability设计

✅ Permission设计

未实现：

❌ Plugin Marketplace

❌ 自动安装系统

❌ 沙箱执行

❌ 第三方插件审核

---

# 十二、Phase 6状态

```
Phase 6 Productization

P6.1 Web Console
✅

P6.2 Identity Permission
✅

P6.3 Project Service
✅

P6.4 Config Center
✅

P6.5 Plugin Extension
✅

P6.6 SaaS Ready
待开始
```
