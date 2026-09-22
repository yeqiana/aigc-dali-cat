# Story OS V3 Phase 6-P6.1 Web Console设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 6-P6.1目标：

为Story OS建立用户操作控制台。

从：

```
开发者通过代码调用平台能力
```

升级为：

```
用户通过Web Console管理AI Agent生产系统
```

---

# 二、整体架构

```

User
 |
 v
Web Console
 |
 v
Platform API Layer
 |
 +----------------+
 |                |
 v                v
Control Plane   Runtime View

Agent
Workflow
Memory
Trace
Artifact

```

---

# 三、技术定位

Web Console职责：

- 平台管理入口
- 状态展示入口
- 配置入口
- 分析入口

不负责：

- Agent执行逻辑
- Workflow推进逻辑
- Runtime调度

前端只调用API。

---

# 四、核心页面设计

## 1. Dashboard

首页总览。

展示：

```
项目数量
Workflow运行数
Agent执行数
成功率
失败任务
Memory增长
```

---

# 五、Project Console

项目管理。

功能：

- 创建项目
- 查看项目状态
- 项目资源管理

例如：

```
Story Project

Episode Production

Agent Resource
```

---

# 六、Agent Console

管理Agent。

页面：

```
Agent列表

Agent详情

Version管理

Capability查看

Execution历史
```

展示：

```
Story Agent v1.0
ACTIVE

Skills:
story_generate
story_optimize
```

---

# 七、Workflow Console

管理流程运行。

展示：

```
Workflow
 |
 Run
 |
 Step
 |
 Agent
```

能力：

- 创建运行
- 查看状态
- 查看执行链

---

# 八、Trace Explorer

链路分析。

展示：

```
Workflow
  |
 Agent
  |
 Skill
  |
 MCP Tool
  |
 Artifact
```

支持：

- 时间线
- 耗时分析
- 异常定位

---

# 九、Memory Console

展示Memory能力。

包含：

```
Memory数量
检索次数
成功率
评分变化
学习记录
```

---

# 十、Artifact Browser

统一查看产物。

支持：

- 图片
- 文档
- Prompt
- 生成结果

来源：

Artifact Repository

---

# 十一、前端模块结构

建议：

```
web-console

src
 ├── dashboard
 ├── project
 ├── agent
 ├── workflow
 ├── execution
 ├── trace
 ├── memory
 └── artifact
```

---

# 十二、权限预留

页面访问基于：

```
User
 |
Role
 |
Permission
 |
Resource
```

对应后续P6.2。

---

# 十三、Phase 6 当前状态

```
Phase 6 Productization

├── P6.1 Web Console
│      ✅
│
├── P6.2 Identity & Permission
│      待开始
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
