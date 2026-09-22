# Story OS 实施路线图 V1.0

更新时间：2026-09-09

项目：Story OS

---

# 一、目标

将 Story OS 从：

> AI 内容生产脚本系统

升级为：

> AI Agent 内容生产操作系统

总体原则：

- 不推翻现有系统
- 增量演进
- 保持现有 Episode 流程可运行
- 先建立平台能力，再迁移业务能力

---

# 二、总体实施路线

```
Phase 0
架构基础治理

↓

Phase 1
数据与任务中心

↓

Phase 2
Workflow 平台化

↓

Phase 3
Agent + MCP + Skill

↓

Phase 4
Memory 智能闭环

↓

Phase 5
平台化运营
```

---

# Phase 0：架构基础治理

目标：

不改变现有生产流程，建立未来扩展边界。

任务：

## 文档治理

完成：

- 总体架构蓝图
- 模块拆分方案
- 数据模型方案
- MCP/Skill方案
- Runtime方案

## 代码治理

增加：

- core接口
- event接口
- trace接口
- artifact接口

原则：

只增加抽象，不迁移旧代码。

验收：

现有 EP002 流程不受影响。

---

# Phase 1：数据与任务中心

目标：

让 Story OS 有统一运行记录。

技术：

- MySQL
- Redis

新增：

## MySQL

核心表：

- project
- episode
- workflow_instance
- workflow_task
- event_log
- trace_span
- artifact

## Redis

负责：

- task queue
- distributed lock
- worker heartbeat
- runtime cache

验收：

可以查询：

- 当前任务
- 执行状态
- 失败原因
- 历史记录

---

# Phase 2：Workflow 平台化

目标：

Episode 不再控制流程。

由 Workflow Engine 控制。

改造：

当前：

```
episode_state.json
控制流程
```

升级：

```
Workflow Engine

↓

Task

↓

Agent
```

新增：

- DAG Engine
- Node定义
- Checkpoint
- Resume
- Validator

验收：

一个 Episode 可以通过 Workflow 自动运行。

---

# Phase 3：Agent + MCP + Skill

目标：

能力插件化。

新增：

## Agent Registry

管理：

- Story Agent
- Image Agent
- Review Agent
- Release Agent

## Skill Registry

管理：

- story-writing
- image-prompt
- visual-review
- subtitle

## MCP Gateway

统一访问：

- 图片模型
- 搜索工具
- 文件工具
- 外部服务

验收：

Agent 不直接依赖具体工具。

---

# Phase 4：Memory 智能闭环

目标：

让 Story OS 越生产越聪明。

接入：

- TencentDB-Agent-Memory
- Mem0
- Letta（候选）

保存：

## 用户偏好

例如：

- 喜欢真实摄影
- 不喜欢解释异常

## 创作经验

例如：

- 哪些故事结构成功
- 哪些镜头容易失败

## Agent经验

例如：

- 图片失败原因
- 修复策略

验收：

新故事生成前可以自动召回历史经验。

---

# Phase 5：平台化运营

目标：

支持长期生产。

能力：

## 多项目

支持：

- 多Episode
- 多账号

## 多Agent

支持：

- 并行执行
- Agent协作

## 运营分析

增加：

- 成本分析
- 成功率分析
- 模型效果分析
- 内容传播分析

---

# 三、推荐优先级

最高优先：

```
1. MySQL + Redis
2. Workflow中心化
3. Event + Trace
```

第二阶段：

```
4. MCP
5. Skill Registry
6. Agent Registry
```

第三阶段：

```
7. Memory
8. Analytics
9. 多租户
```

---

# 四、最终目标架构

```
用户
 ↓
React Console
 ↓
Spring Boot Control Plane
 ↓
Workflow Engine
 ↓
Python Agent Runtime
 ↓
MCP + Skill
 ↓
Model / Tool

旁路：

MySQL
Redis
Event
Trace
Artifact
Memory
```

---

# 五、实施原则

1. 不大重构。
2. 不一次迁移所有代码。
3. 每阶段保持生产能力。
4. 所有新能力先通过接口接入。
5. 旧 Episode 资产必须可继续使用。

---

# 结论

Story OS 的演进路线：

从：

脚本集合

到：

Workflow系统

再到：

Agent生产平台。
