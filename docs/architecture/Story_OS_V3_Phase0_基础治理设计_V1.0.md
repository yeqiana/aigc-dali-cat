# Story OS V3 Phase 0 基础治理设计 V1.0

更新时间：

2026-09-09

项目：

Story OS

分支：

story-platform-v3


---

# 一、Phase 0目标

Phase 0 不做平台替换。

目标：

在不影响 story 分支生产链的前提下，为 Story OS 增加平台化基础能力。

当前生产链保持：

```
Runtime
 ↓
Workflow
 ↓
Production
 ↓
Review
 ↓
Release
```

新增旁路：

```
Production Runtime
        |
        + Event
        |
        + Trace
        |
        + Artifact Index
        |
        + Platform Adapter
```


---

# 二、Phase 0禁止事项

禁止：

- 替换 episode-state.json
- 替换 Workflow Runner
- 引入 Spring Boot
- 引入数据库作为生产事实源
- 修改图片生产 Runtime
- 修改 Scheduler 执行逻辑
- 创建第二状态机

原因：

当前生产链已经稳定，V3首先需要建立可观察、可扩展底座。


---

# 三、Phase 0模块

## 1. core

职责：

定义平台公共模型。

目录：

```
core/
 ├── contracts/
 ├── enums/
 └── models/
```

包含：

- RequestId
- EpisodeId
- TaskId
- ArtifactId
- EventId

原则：

只定义事实，不包含业务流程。


---

# 四、Event Contract

## 目标

记录系统发生了什么。

不是状态机。


## Event模型

```json
{
  "event_id": "evt_xxx",
  "event_type": "TASK_STARTED",
  "aggregate_id": "episode_xxx",
  "timestamp": "2026-09-09T10:00:00",
  "payload": {}
}
```


## 初始事件类型

```
EPISODE_CREATED
WORKFLOW_STARTED
TASK_STARTED
TASK_COMPLETED
TASK_FAILED
ARTIFACT_CREATED
REVIEW_COMPLETED
RELEASE_CREATED
```


## 存储

Phase 0：

```
jsonl / 文件
```

Phase 1：

```
MySQL event表
```


---

# 五、Trace Contract

## 目标

回答：

一次生产为什么成功/失败。


## Trace结构

```
Trace
 |
 + Span
 |
 + Input
 |
 + Output
 |
 + Error
```


示例：

```json
{
 "trace_id":"trace001",
 "step":"image_generation",
 "duration":120,
 "status":"SUCCESS"
}
```


记录：

- Runtime调用
- Agent执行
- Skill调用
- MCP调用
- Provider调用


---

# 六、Artifact Contract

## 目标

统一管理生产资产引用。

注意：

不迁移当前图片目录。

只增加索引能力。


模型：

```
Artifact
 |
 + path
 + sha256
 + type
 + owner
 + created_by
```


类型：

```
STORY
FRAME
IMAGE
VIDEO
PROMPT
EVIDENCE
RELEASE
```


---

# 七、Platform Adapter

## 目标

隔离旧 Runtime 与未来平台。


当前：

```
Runtime
```

未来：

```
Control Plane
      |
Adapter
      |
Runtime
```


Phase 0只提供接口：

```
submitTask()
queryTask()
recordEvent()
recordTrace()
registerArtifact()
```

不改变实际执行。


---

# 八、目录规划

新增：

```
platform/
 ├── core/
 ├── event/
 ├── trace/
 ├── artifact/
 └── adapter/
```


---

# 九、实施顺序

## P0-1

创建 Contract。

状态：

```text
P0-1.1 基础目录与通用模型：IMPLEMENTED
P0-1.2 Event / Trace / Artifact Contract：IMPLEMENTED（待 Python 环境执行单测）
```

交付：

- Event Contract
- Trace Contract
- Artifact Contract
- Event / Trace / Artifact 基础枚举
- Contract 最小单元测试

实现位置：

```text
platform/core/contracts/
platform/core/enums/
tests/platform/test_core_contracts.py
```

边界：

- Contract 只记录事实
- 不推进 episode-state
- 不承担 Workflow 调度
- 不执行文件迁移
- 不接数据库


## P0-2

增加 Runtime Observer。

能力：

```
运行时产生事件
        ↓
记录trace
        ↓
关联artifact
```


## P0-3

增加 Platform Adapter。

旧流程保持不变。


## P0-4

真实EP生产验证。

验证：

- 不影响生产
- 可追踪完整链路
- 可回放执行过程


---

# 十、Phase 0完成标准

满足：

1. story 分支生产无变化
2. V2.7流程继续运行
3. 每个任务可生成Event
4. 每次执行可生成Trace
5. 每个资产可建立Artifact索引
6. 后续可无痛接入MySQL/Redis/Spring Boot


---

# 结论

Phase 0不是重构。

它是给Story OS增加“操作系统内核日志层”。

先让系统知道：

- 发生了什么
- 谁执行的
- 产生了什么
- 为什么失败

然后再进入数据库、Control Plane和Agent平台化。