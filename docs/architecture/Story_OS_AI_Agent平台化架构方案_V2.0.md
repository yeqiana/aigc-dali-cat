# Story OS AI Agent 平台化架构方案 V2.0

更新时间：2026-09-09

## 一、目标

Story OS 当前已经从 AI 图片生成脚本演进为 AI 内容生产系统。

下一阶段目标：

> 从 AI 内容生产工具升级为 AI Agent 内容生产操作系统。

核心方向：

- Spring Boot：Control Plane（平台控制面）
- Python Runtime：Execution Plane（智能执行面）
- MCP：能力连接协议
- Skill：可复用能力插件
- Memory：AI经验层
- Database：系统事实层

---

# 二、总体架构

```
用户
 |
Web Console
 |
Spring Boot Control Plane
 |
Workflow Engine
 |
+----------------------+
|                      |
Agent Center           Data Layer
|                      |
MCP Gateway            MySQL
|                      |
Skills                 Redis
|
Python Agent Runtime
|
Models / Tools
|
Memory Layer
```

---

# 三、模块职责

## 1. Spring Boot Control Plane

负责：

- 用户
- 项目
- Episode
- Workflow
- Agent管理
- 权限
- 配置

不负责：

- Prompt生成
- 图片生成
- Agent推理

---

## 2. Python Agent Runtime

负责：

- Agent执行
- Prompt编译
- 模型调用
- 图片处理
- 内容生成

例如：

- Story Agent
- Image Agent
- Review Agent
- Release Agent

---

## 3. MCP Gateway

作用：

让 Agent 通过统一协议调用外部能力。

例如：

```
generate_image
search_reference
review_image
```

映射到：

- OpenAI
- Codex
- 本地工具
- 外部服务

---

## 4. Skill系统

定位：

可复用能力插件。

例如：

```
story-writing
image-prompt
visual-review
subtitle-generation
publish-analysis
```

---

# 四、数据架构

## MySQL

负责系统事实。

保存：

- Project
- Episode
- Workflow
- Task
- Event
- Trace
- Artifact索引

回答：

> 现在系统发生了什么？

---

## Redis

负责实时状态。

保存：

- 队列
- 分布式锁
- Worker状态
- 缓存
- 实时进度

回答：

> 当前正在发生什么？

---

## 文件系统/对象存储

保存：

- 图片
- 视频
- Prompt
- Story
- Evidence
- Release

---

# 五、Memory Layer

定位：AI经验系统。

保存：

## 用户偏好

例如：

- 喜欢真实摄影感
- 不喜欢解释异常
- 喜欢第一视角

## 创作经验

例如：

- 哪些故事结构成功
- 哪些Prompt容易失败
- 哪些镜头效果好

候选：

- TencentDB-Agent-Memory
- Mem0
- Letta

---

# 六、Workflow演进

当前：Episode控制流程。

未来：Workflow Engine控制流程。

```
Workflow
 |
Node
 |
Task
 |
Agent
```

---

# 七、Event与Trace

## Event

支持：

- 自动恢复
- Agent协作
- 状态同步

事件：

- TASK_STARTED
- TASK_FAILED
- TASK_COMPLETED
- REPAIR_REQUIRED
- RELEASE_READY

## Trace

三层：

### Execution Trace

谁执行。

### Decision Trace

为什么这样决定。

### Artifact Trace

资产来源关系。

---

# 八、技术栈建议

```
React/Vue
 |
Spring Boot
 |
MySQL + Redis
 |
Python Agent Runtime
 |
MCP Gateway
 |
Skills
 |
Models
 |
Memory System
```

---

# 九、迁移路线

## Phase 0

增加：

- MySQL设计
- Redis设计
- MCP接口规范

不改变现有流程。

## Phase 1

Workflow中心化。

## Phase 2

Agent标准化：

- Agent Registry
- Skill Registry
- MCP Registry

## Phase 3

接入Memory：

- 历史经验召回
- Prompt优化
- 失败案例学习

## Phase 4

平台化：

- 多项目
- 多用户
- 多Agent
- 多媒体类型

---

# 十、最终目标

```
用户需求
 ↓
Runtime Request
 ↓
Workflow
 ↓
Agent协作
 ↓
MCP
 ↓
Skill
 ↓
Runtime执行
 ↓
Memory学习
 ↓
Artifact沉淀
 ↓
Release发布
```

最终：

Story OS 不再是一组脚本，而是一套 AI 内容生产操作系统。
