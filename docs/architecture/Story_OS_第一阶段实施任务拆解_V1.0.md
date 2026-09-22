# Story OS 第一阶段实施任务拆解 V1.0

更新时间：

2026-09-09

项目：

Story OS


---

# 一、目标

本阶段目标：

在不破坏现有 Story OS 生产流程的前提下，引入平台化基础能力。

原则：

> 增量改造，不推倒重来。

当前已有能力继续运行：

- episodes/_system
- Runtime DAG
- Image Scheduler
- Batch Production
- Evidence Gate

新增能力作为外围增强。


---

# 二、Phase 0：基础治理

目标：建立平台化基础边界。

## 任务

### 1. 模块目录规划

新增：

```
platform/

core/

workflow/

trace/

event/

artifact/
```

暂不迁移旧代码。


### 2. 定义接口

新增基础接口：

- Task
- Workflow
- Event
- Artifact
- Agent


验收：

- 新模块可以独立引用
- 不影响现有 Episode 执行


---

# 三、Phase 1：数据基础建设

目标：引入 MySQL + Redis。


## MySQL 第一批表

### episode

记录剧集基础信息。


### workflow_instance

记录工作流运行实例。


### workflow_task

记录任务节点。


### event_log

记录系统事件。


### trace_span

记录执行链路。


---

## Redis

第一阶段用途：

- 任务锁
- Worker状态
- 实时进度
- 缓存


验收：

可以查询：

- 当前运行任务
- 失败任务
- Worker状态


---

# 四、Phase 2：Workflow中心化

目标：

从：

```
episode_state.json 控制流程
```

升级为：

```
Workflow Engine 控制流程
```


任务：

- Workflow定义
- Node模型
- Task执行器
- Checkpoint
- Resume


验收：

EP002 可以通过 Workflow 驱动执行。


---

# 五、Phase 3：Agent平台化

目标：

标准化 Agent 能力。


新增：

## Agent Registry

管理：

- Agent名称
- 版本
- 状态


## Skill Registry

管理：

- Skill定义
- Skill版本
- Skill权限


## MCP Registry

管理：

- Tool
- Provider
- 调用权限


验收：

Agent 可以动态发现能力。


---

# 六、Phase 4：Memory接入

目标：让 Story OS 越生产越聪明。

保存：

- 用户偏好
- 成功案例
- 失败案例
- Agent经验


候选：

- TencentDB-Agent-Memory
- Mem0
- Letta


验收：

新故事生成可以召回历史经验。


---

# 七、Phase 5：平台化运营

目标：形成完整产品。

增加：

- Web Console
- 权限体系
- 成本统计
- 数据分析
- 多项目管理


---

# 八、开发顺序建议

严格按照：

```
接口
 ↓
数据
 ↓
Workflow
 ↓
Agent
 ↓
Memory
 ↓
平台化
```

禁止：

- 先重构目录
- 先迁移全部代码
- 先替换Runtime


---

# 九、第一阶段完成标准

完成后：

Story OS 具备：

- 任务可查询
- 状态可追踪
- 失败可恢复
- 执行可观测
- 后续可接入Agent平台


结论：

第一阶段不是重写 Story OS，而是给现有系统增加平台骨架。
