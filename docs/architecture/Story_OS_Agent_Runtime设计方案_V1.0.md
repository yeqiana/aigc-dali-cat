# Story OS Agent Runtime设计方案 V1.0

更新时间：

2026-09-09

项目：

Story OS


---

# 一、定位

Agent Runtime 是 Story OS 的执行层。

负责：

- Agent生命周期管理
- Task执行
- Context管理
- Tool调用
- Retry恢复
- Resource调度

不负责：

- 故事规则
- 业务流程定义
- 人工审核规则


---

# 二、整体关系

```
Workflow

    |
    v

Task

    |
    v

Agent Runtime

    |
    +---------+
    |         |
    v         v
 Skill      MCP

    |
    v

Model / Tool
```


---

# 三、Agent模型

一个Agent包含：

```
Agent
 |
 +-- Identity
 |
 +-- Skill集合
 |
 +-- Memory访问权限
 |
 +-- Tool权限
 |
 +-- Runtime配置
```

例如：

## Story Agent

负责：

- 故事生成
- 结构优化


## Image Agent

负责：

- Prompt编译
- 图片生成
- 图片修复


## Review Agent

负责：

- 质量检查
- 风险判断


---

# 四、Task模型

所有执行必须任务化。

Task包含：

```
task_id
workflow_id
agent_type
input
status
retry_count
result
```

状态：

```
PENDING

RUNNING

SUCCESS

FAILED

RETRYING

CANCELLED
```


---

# 五、Context管理

Agent上下文分层：

## 1. Workflow Context

当前流程信息。

例如：

EP002 Production。


## 2. Task Context

当前任务输入。

例如：

Frame05 Contract。


## 3. Memory Context

历史经验。

例如：

类似故事失败案例。


## 4. Tool Context

外部能力返回。

例如：

图片生成结果。


---

# 六、Worker模型

Worker负责实际执行。

例如：

```
Image Worker

Review Worker

Story Worker
```

Worker职责：

- 获取Task
- 执行Skill
- 调用MCP
- 上报状态


---

# 七、Retry与恢复

Runtime必须支持：

- 超时恢复
- 网络失败恢复
- 模型失败恢复
- Worker异常恢复


流程：

```
Task Failed

    |
    v

Event

    |
    v

Retry Policy

    |
    v

重新执行
```


规则：

成功结果不可覆盖。

失败必须保留Attempt记录。


---

# 八、Agent通信

推荐：

Event驱动。

不要Agent直接互调。

例如：

```
Image Agent完成

    |
    v

FRAME_GENERATED Event

    |
    v

Review Agent启动
```

优点：

- 解耦
- 可恢复
- 可追踪


---

# 九、Runtime与Workflow边界

Workflow负责：

> 做什么

例如：

```
先Story
再Visual
再Production
```


Runtime负责：

> 怎么做

例如：

```
哪个Agent执行
哪个Worker执行
调用哪个模型
失败如何恢复
```


---

# 十、与现有Story OS映射

当前：

```
async_task_runtime.py

image_scheduler.py

batch_scheduler.py

runtime_dag.py
```

未来：

```
runtime/

 agent/
 worker/
 task/
 scheduler/
 retry/
 context/
```


---

# 十一、演进路线

## Phase 1

统一Task模型。


## Phase 2

Agent Registry。


## Phase 3

Worker Pool。


## Phase 4

Event驱动恢复。


## Phase 5

多Agent协作。


---

# 十二、目标

最终：

```
Workflow定义目标

Agent负责思考

Skill提供能力

MCP连接工具

Runtime负责执行

Memory负责成长

Trace负责观察
```

Story OS成为真正的AI生产运行平台。
