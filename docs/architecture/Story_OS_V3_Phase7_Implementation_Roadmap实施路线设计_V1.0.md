# Story OS V3 Phase 7 Implementation Roadmap 实施路线设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3

---

# 一、Phase 7目标

Phase 0-6 已完成架构设计：

```
治理
数据
Workflow
Agent
Memory
Platform Service
Productization
```

Phase 7目标：

将架构真正落地为可运行系统。

从：

```
Architecture Design
```

进入：

```
Production Implementation
```

---

# 二、实施原则

## 不影响现有生产链

禁止：

```
直接替换V2.7 Runtime
直接修改EP002生产流程
```

采用：

```
新增平台层

兼容旧Runtime

逐步迁移
```

---

# 三、Phase 7整体路线

```
P7.1 数据模型落地
        |
        v
P7.2 Platform Service模块骨架
        |
        v
P7.3 Platform API实现
        |
        v
P7.4 Agent Runtime接入
        |
        v
P7.5 Web Console实现
        |
        v
P7.6 EP002迁移验证
```

---

# 四、P7.1 数据模型落地

目标：

将设计模型转换为数据库。

范围：

## Agent

```
agent
agent_version
agent_execution
```

## Skill

```
skill_definition
skill_version
skill_capability
```

## Workflow

```
workflow_definition
workflow_run
workflow_step
```

## Memory

```
memory_item
memory_embedding
memory_feedback
```

## Platform

```
project
user
role
permission
config
```

---

# 五、P7.2 Platform Service模块骨架

目标：

建立代码边界。

建议结构：

```
platform/

 agent/
 workflow/
 memory/
 project/
 config/
 permission/
 observability/
```

保持：

```
Domain
Application
Repository
Infrastructure
```

分层。

---

# 六、P7.3 Platform API实现

实现：

```
Agent API
Workflow API
Memory API
Project API
Config API
Trace API
```

目标：

Web Console和外部系统统一入口。

---

# 七、P7.4 Agent Runtime接入

当前：

```
Task Runner
```

升级：

```
Agent Runtime
```

接入：

```
Agent Context
Skill Context
Tool Context
Memory Context
Execution Record
```

---

# 八、P7.5 Web Console实现

建设：

```
Dashboard

Project Console

Agent Console

Workflow Console

Trace Explorer

Memory Console
```

---

# 九、P7.6 EP002迁移验证

目标：

验证新平台不会破坏真实生产。

迁移方式：

```
Shadow Mode

        |
        v

Dual Run

        |
        v

Production Switch
```

指标：

```
Workflow一致性
Agent执行成功率
Runtime稳定性
Artifact完整性
Memory收益
```

---

# 十、最终目标架构

```
User
 |
Web Console
 |
Platform API
 |
Workflow Service
 |
Agent Orchestrator
 |
Agent Service
 |
Skill Registry
 |
MCP Registry
 |
Agent Runtime
 |
Trace/Event/Artifact
 |
Memory Learning
```

---

# 十一、当前状态

```
Phase 0
✅

Phase 1
✅

Phase 2
✅

Phase 3
✅

Phase 4
✅

Phase 5
✅

Phase 6
✅

Phase 7
✅ 完成

Phase 8
🟢 Code Accepted（Canary Migration；生产切换未闭环）

Phase 9
🟢 Code Accepted / Runtime Smoke Executed / 常驻 Runtime Worker 载体已交付（未部署为系统服务）/ 真实 Recovery 与 Canary 演练已执行（2026-09-10）/ Worker 存活观察者已交付（P9.30，名册内失联转 CRITICAL）/ 恢复决策执行器已交付（P9.31，RESTART_AGENT 真实执行）/ 真实告警通道已交付（P9.32，CRITICAL 告警经 WebhookAlertChannel 真机送达本地接收器）/ 真实 Metrics 采集端点已交付（P9.33，/metrics + /healthz 真机 E2E）/ 常驻 Runtime 编排入口已交付（P9.34，Worker + Metrics 统一编排，真机 E2E）/ schtasks 部署脚本已交付（P9.34.1，dry-run 验证）/ 自愈自动触发已接线（P9.34.2，--auto-recover 默认关闭，真机 E2E）

Phase 10
⏸ 未启动
```

下一阶段：

```
Phase 8 / Phase 9 生产化收尾
常驻 Runtime 可部署单元注册为系统服务（编排入口 P9.34 与部署脚本 P9.34.1 已交付，注册待授权）、真实 Metrics 采集后端与 Alert Channel、Canary 生产归属切换决策（演练与决策证据已完成；归属切换未执行）
Worker 失联告警已闭环（P9.30 存活观察者）；恢复决策执行器已交付并真机执行 RESTART_AGENT（P9.31，finding recovery_decision_has_no_executor 已 CLOSED）；真实告警通道已交付（P9.32，WebhookAlertChannel 真机 E2E 送达）；真实 Metrics 采集端点已交付（P9.33，/metrics + /healthz 真机 E2E）；常驻 Runtime 编排入口已交付（P9.34，Worker + Metrics 统一编排真机 E2E）；schtasks 部署脚本已交付（P9.34.1，dry-run 验证）；自愈自动触发已接线（P9.34.2，--auto-recover 默认关闭，开启待授权）；真实 Prometheus / Grafana 采集实例与告警外部端点仍待接入。
```
