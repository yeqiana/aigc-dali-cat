# Story OS 前端控制台设计方案 V1.0

更新时间：

2026-09-09

项目：

Story OS

---

# 一、定位

Story OS 前端不是传统后台管理系统。

定位：

> AI 内容生产操作控制台。

核心目标：

让用户能够观察、管理、干预 AI 生产流程。

---

# 二、整体架构

```

Web Console

    |
    |

Spring Boot Control Plane

    |

Workflow / Agent Runtime

```

前端只负责：

- 展示状态
- 人工决策
- 配置管理
- 生产监控

不负责：

- Agent执行
- 图片生成
- Workflow计算

---

# 三、核心页面

## 1. 首页 Dashboard

展示：

- 当前项目数量
- 运行中的Workflow
- Agent状态
- 失败任务
- 今日成本
- 生产趋势

例如：

```
EP002
Production
12/20 Frames
Running
```

---

# 四、Episode管理

功能：

- 创建Episode
- 查看状态
- 查看资产
- 查看生产历史

展示：

```
Episode
 |
 Story
 |
 Workflow
 |
 Frames
 |
 Release
```

---

# 五、Workflow监控

核心页面。

展示DAG：

```
Story Lock
    |
Character
    |
Visual Lock
    |
Production
    |
Review
    |
Release
```

显示：

- 当前节点
- 完成节点
- 失败节点
- 重试次数
- 执行时间

---

# 六、Agent管理

展示：

Agent列表：

```
Story Agent
Image Agent
Review Agent
Release Agent
```

状态：

- Online
- Running
- Failed
- Disabled

---

# 七、Task中心

类似生产任务队列。

展示：

- 待执行任务
- 执行中任务
- 失败任务
- 重试任务

支持：

- Retry
- Cancel
- Resume

---

# 八、Trace查看

提供三层视图。

## Execution Trace

查看：

- Worker
- Model
- 时间
- 状态


## Decision Trace

查看：

为什么：

```
Frame05 retry
reason:
identity score low
```


## Artifact Trace

查看资产来源。

---

# 九、Skill / MCP管理

管理：

## Skill Registry

例如：

```
image-prompt
visual-review
subtitle
```


## MCP Registry

例如：

```
image provider
search tool
storage tool
```

支持：

- 启用
- 禁用
- 版本管理

---

# 十、Memory管理

查看AI经验。

包括：

- 用户偏好
- 创作经验
- 失败案例
- Agent经验

支持：

- 查询
- 删除
- 调整权重

---

# 十一、技术建议

前端：

```
React + TypeScript

+

Ant Design / Arco Design

+

Graph Visualization
```

用于展示：

- Workflow DAG
- Agent关系
- Artifact血缘

---

# 十二、最终目标

形成：

```

用户
 |
Web Console
 |
Control Plane
 |
Workflow
 |
Agent Runtime
 |
Skill/MCP
 |
Model

```

前端成为 Story OS 的生产驾驶舱。

---

# 结论

Story OS 前端不是简单后台。

它是：

> AI Agent 生产操作系统的控制中心。

负责让复杂AI流程变得可见、可控、可恢复。
