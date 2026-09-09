# Story OS V3 Phase5-P5.5 Observability Console 设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、设计目标

Phase 5-P5.5 目标：

建立 Story OS 平台观测控制台。

将：

```
Agent执行
Workflow运行
Runtime任务
Memory学习
Artifact生产
```

统一展示。

目标：

从：

```
系统黑盒运行
```

升级：

```
可观察
可追踪
可分析
可优化
```

---

# 二、定位

Observability Console 是平台观测层。

负责：

- 状态查看
- 链路追踪
- 性能分析
- 异常定位
- 经验分析

不负责：

- 修改Workflow
- 调度Agent
- 执行Runtime
- 修改Memory事实

---

# 三、整体架构

```

                 Console UI

                     |

                     v

             Observability API

                     |

 +-------------------+-------------------+

 |                   |                   |

 v                   v                   v

Trace Query    Runtime Monitor    Analytics

 |                   |                   |

 v                   v                   v

Trace Store    Event Store       Metric Store

```

---

# 四、核心模块

## 1. Workflow Dashboard

展示：

- Workflow运行状态
- 当前Step
- 成功率
- 执行耗时

例如：

```
EP002 Production

Workflow RUNNING

Current Step:
IMAGE_GENERATION
```

---

# 2. Agent Execution Explorer

查看：

一次Agent执行全过程。

链路：

```
Agent Execution

|

Skill Execution

|

Tool Execution

|

Trace

|

Artifact
```

用于定位：

- Agent选择错误
- Skill失败
- MCP失败

---

# 3. Trace Viewer

展示分布式执行链。

类似：

```
Workflow
  |
  +-- Agent
       |
       +-- Skill
            |
            +-- MCP Tool
```

支持：

- 时间线
- Span耗时
- Error定位

---

# 4. Runtime Monitor

监控：

- Worker状态
- Queue状态
- Retry次数
- Task耗时

数据来源：

```
Redis Runtime State

Event Log

Trace
```

---

# 5. Memory Analytics

展示：

- Memory数量
- Memory类型分布
- 使用次数
- 成功率
- 评分变化

例如：

```
Visual Prompt Memory

Usage: 120
Success Rate: 86%
Score: +12
```

---

# 五、核心API

## Trace查询

```
GET /api/v1/observability/traces/{id}
```

---

## Agent执行查询

```
GET /api/v1/observability/agents/executions/{id}
```

---

## Workflow监控

```
GET /api/v1/observability/workflows/runs/{id}
```

---

## Runtime指标

```
GET /api/v1/observability/runtime/metrics
```

---

## Memory分析

```
GET /api/v1/observability/memory/statistics
```

---

# 六、数据来源

```
Event Store

Trace Store

Artifact Index

Runtime State

Memory Store
```

Observability只读消费。

---

# 七、与其他模块关系

```
Workflow Service
        |
        v
Agent Service
        |
        v
Runtime Service
        |
        v
Trace/Event
        |
        v
Observability Console
```

---

# 八、Phase 5完成状态

```
Phase 5 Platform Service

P5.1 Platform API Layer
✅

P5.2 Agent Service
✅

P5.3 Workflow Service
✅

P5.4 Memory Service
✅

P5.5 Observability Console
✅
```

---

# 九、下一阶段

Phase 5 后，Story OS 已具备平台化基础。

后续进入：

```
Phase 6 Productization
```

重点：

- Web Console
- 权限体系
- 多项目管理
- 多租户能力
- 配置中心
- 插件生态
