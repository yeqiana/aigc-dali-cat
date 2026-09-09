# Story OS 模块化拆分方案 V1.0

更新时间：2026-09-09

项目：storyOS

## 一、当前结论

当前项目已经具备“分模块思想”，但还没有完全形成标准化平台架构。

现状更接近：

```
episodes/_system
    ↓
大量领域能力文件集合
    ↓
通过 workflow / runtime / gate 串联
```

已经存在的模块边界：

- Runtime
- Workflow
- PreImage Contract
- Image Execution
- Review
- Release
- Evidence

但是问题：

1. 模块以文件名分类为主，代码隔离不足。
2. Runtime、Workflow、Evidence、State 之间职责边界还需要进一步明确。
3. 部分历史模块和新架构混合存在。
4. trace 能力存在，但没有成为统一横切模块。

目标不是简单拆目录，而是形成 Story OS Platform 架构。

---

# 二、目标模块结构

建议未来演进为：

```
storyOS
│
├── core/                 # 核心协议层
│   ├── state              # 状态模型
│   ├── contract           # Contract协议
│   ├── artifact           # 资产模型
│   └── event              # 事件模型
│
├── runtime/              # 执行运行时
│   ├── router
│   ├── scheduler
│   ├── executor
│   ├── checkpoint
│   └── recovery
│
├── workflow/              # 工作流编排
│   ├── dag
│   ├── step
│   ├── transition
│   └── policy
│
├── trace/                 # 可观测性
│   ├── trace_event
│   ├── execution_log
│   ├── cost
│   └── lineage
│
├── production/            # 图片生产
│   ├── prompt
│   ├── image_worker
│   ├── batch
│   └── review
│
├── story/                 # 创作领域
│   ├── concept
│   ├── story_lock
│   ├── character
│   ├── frame
│   └── environment
│
├── release/               # 发布领域
│
├── governance/            # 规范和门禁
│   ├── evidence
│   ├── gate
│   └── validation
│
└── episodes/              # 用户内容实例
```

---

# 三、核心模块职责

## 1. Core 核心层

负责所有模块共享的数据协议。

包含：

- EpisodeState
- Contract
- Artifact
- Event
- Fingerprint

禁止：

- 调用图片模型
- 调用工作流
- 修改业务状态

作用：避免模块互相依赖。

---

# 2. Workflow 工作流模块

职责：回答“下一步做什么”。

例如：

```
Story Lock
 ↓
Visual Lock
 ↓
Production
 ↓
Review
 ↓
Release
```

负责：

- DAG
- Step定义
- 流程依赖
- 状态迁移请求

不负责：

- 真正执行图片
- 记录日志
- 保存状态

---

# 3. Runtime 运行时模块

职责：回答“怎么执行”。

例如：

```
Workflow Step
      ↓
Runtime
      ↓
Worker
```

负责：

- 调度
- 并发
- Retry
- Recovery
- Timeout
- Resource管理

当前已有：

- async_task_runtime.py
- image_scheduler.py
- batch_scheduler.py

属于该模块。

---

# 4. Trace 可观测模块

当前最应该补强的模块。

目标：任何动作都可追踪。

统一模型：

```
TraceEvent

id
trace_id
span_id
step
worker
input_sha
output_sha
status
cost
time
```

记录：

- Workflow执行
- 图片生成
- Review
- Repair
- Release

Trace不能决定成功失败，只记录事实。

---

# 5. Story Domain

负责创作逻辑。

包括：

- Concept
- Story
- Character Contract
- Environment Contract
- Frame Contract

不应该知道：

- Codex怎么调用
- 图片API怎么调用
- 队列怎么运行

---

# 6. Production 图片生产模块

负责：

```
Frame Contract
      ↓
Prompt Compiler
      ↓
Image Worker
      ↓
Normalize
      ↓
Review
```

当前：

- batch_scheduler
- image_worker
- provider_router

归入这里。

---

# 7. Governance 门禁模块

负责判断：

“是否允许进入下一阶段”。

例如：

- evidence_gate
- machine_gate
- validation

原则：

Gate读取事实，不生产事实。

---

# 四、当前代码映射

| 当前目录 | 未来模块 |
|-|-|
|episode_state.py|core/state|
|frame_contract.py|story/frame|
|character_contract.py|story/character|
|runtime_dag.py|workflow/dag|
|workflow_runner.py|workflow|
|async_task_runtime.py|runtime|
|image_scheduler.py|production/runtime|
|batch_scheduler.py|production|
|runtime_trace.py|trace|
|evidence_gate.py|governance|
|final_candidate_snapshot.py|release|

---

# 五、拆分优先级

## P0 不改目录，只明确边界

先做：

- Module Registry
- Dependency Rules
- Trace统一
- Workflow接口统一

风险最低。


## P1 新增模块入口

增加：

```
core/
workflow/
trace/
```

旧路径保留wrapper。


## P2 渐进迁移

按照调用频率迁移：

1. trace
2. runtime
3. workflow
4. production
5. story domain


## P3 最终平台化

形成：

```
Request
 ↓
Workflow DAG
 ↓
Runtime
 ↓
Worker
 ↓
Trace
 ↓
Evidence
 ↓
State
```

---

# 六、不建议现在做的事情

1. 不建议马上把 episodes/_system 全搬到 src。

原因：

- 大量历史路径依赖。
- AGENTS 已明确 canonical path。
- 容易破坏已有流程。

2. 不建议按 Python 文件拆包。

应该按领域拆。

3. 不建议 Workflow直接控制State。

必须通过状态服务。

---

# 七、最终目标

Story OS 最终应该从：

```
脚本集合
```

升级为：

```
AI内容生产操作系统

Core
 ├── Workflow Engine
 ├── Runtime Engine
 ├── Trace System
 ├── Production Engine
 ├── Governance Engine
 └── Domain Plugins
```

当前项目已经具备70%左右基础，只需要补齐边界和接口，而不是推倒重构。
