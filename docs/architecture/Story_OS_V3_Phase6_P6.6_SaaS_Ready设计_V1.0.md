# Story OS V3 Phase6-P6.6 SaaS Ready 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

---

# 一、设计目标

Phase 6-P6.6 目标：

为 Story OS 从个人 AI Agent 平台演进到 SaaS 平台预留基础能力。

目标：

```
单用户系统

        ↓

多用户平台

        ↓

多租户 SaaS
```

---

# 二、SaaS 架构原则

当前阶段不直接实现商业化能力。

只建立：

- 租户隔离
- 资源隔离
- 配额治理
- 使用审计

保持：

```
业务能力

与

商业能力

解耦
```

---

# 三、核心模型

## 1. tenant

租户主体。

代表一个独立使用空间。

例如：

```
个人用户

工作室

企业团队
```

字段方向：

```
id bigint unsigned
tenant_code
name
status
created_time
updated_time
```

---

# 四、Tenant User

## tenant_member

管理：

```
Tenant

|

User
```

支持：

```
OWNER
ADMIN
MEMBER
VIEWER
```

---

# 五、资源隔离

所有核心资源增加租户维度：

```
Project

Workflow

Agent

Memory

Artifact

Execution
```

关联：

```
tenant_id
```

实现：

```
Tenant A

只能访问

Tenant A资源
```

---

# 六、Quota 配额体系

## quota_policy

定义限制：

例如：

```
每日图片生成次数

Agent执行次数

存储空间

Token额度
```

---

## quota_usage

记录使用情况：

例如：

```
IMAGE_GENERATION

count:100
```

用于：

- 限流
- 计费基础
- 成本分析

---

# 七、Billing 预留

当前不实现支付。

预留：

```
subscription

plan

billing_record
```

未来支持：

```
Free

Pro

Enterprise
```

---

# 八、Audit 审计

## audit_log

记录：

```
谁

什么时候

操作什么资源

结果如何
```

例如：

```
User A

调用 Visual Agent

生成图片
```

---

# 九、最终 SaaS 架构

```
Tenant
  |
  +-- User
  |
  +-- Project
  |
  +-- Agent
  |
  +-- Workflow
  |
  +-- Memory
  |
  +-- Artifact
```

统一进入：

```
Permission

Quota

Audit
```

---

# 十、Phase 6 完成状态

```
Phase 6 Productization

├── P6.1 Web Console
│      ✅
│
├── P6.2 Identity Permission
│      ✅
│
├── P6.3 Project Service
│      ✅
│
├── P6.4 Config Center
│      ✅
│
├── P6.5 Plugin Extension
│      ✅
│
└── P6.6 SaaS Ready
       ✅
```

---

# 十一、Story OS V3 总体完成状态

```
Phase 0 基础治理
✅

Phase 1 数据基础
✅

Phase 2 Workflow中心化
✅

Phase 3 Agent平台化
✅

Phase 4 Memory System
✅

Phase 5 Platform Service
✅

Phase 6 Productization
✅
```

Story OS 已具备：

```
Agent Native

Workflow Driven

Memory Enhanced

Platform Ready

SaaS Expandable
```
