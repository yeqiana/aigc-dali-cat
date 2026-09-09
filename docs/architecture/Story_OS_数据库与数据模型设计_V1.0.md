# Story OS 数据库与数据模型设计 V1.0

更新时间：

2026-09-09

项目：

Story OS


---

# 一、设计目标

数据库不是替代文件系统。

职责划分：

```
数据库
负责：系统事实、状态、关系、查询

文件系统
负责：故事、图片、视频、Prompt、Evidence

Memory系统
负责：经验、偏好、历史知识
```

目标：

支撑：

- 多 Episode 并行生产
- Workflow 调度
- Agent 协作
- 自动恢复
- Trace 查询
- 成本统计
- 资产追踪


---

# 二、推荐技术栈

第一阶段：

```
MySQL 8
+
Redis
+
文件系统/OSS
```

后续：

```
MySQL
+
Vector DB
+
Memory System
```


---

# 三、MySQL职责

MySQL保存：

## 1. Project

项目表。

字段：

```
id
name
description
status
created_time
```

示例：

```
Story OS
```


---

## 2. Episode

剧集表。

```
episode_id
project_id
name
current_stage
status
created_time
updated_time
```

注意：

episode-state.json继续保留。

数据库作为平台查询入口。

文件作为Episode事实快照。


---

## 3. Workflow Instance

工作流实例。

```
workflow_id
episode_id
workflow_type
status
start_time
end_time
```

例如：

```
EP002 Production Workflow
RUNNING
```


---

## 4. Workflow Task

任务节点。

```
task_id
workflow_id
task_type
status
retry_count
worker_id
start_time
end_time
```

例如：

```
Generate Frame 05
FAILED
retry=2
```


---

## 5. Event Log

事件记录。

支持Event驱动。

```
event_id
event_type
source
payload
created_time
```

示例：

```json
{
 "event":"FRAME_FAILED",
 "frame":"05",
 "reason":"identity_drift"
}
```


---

## 6. Trace Span

执行追踪。

```
trace_id
task_id
operation
model
duration
cost
status
metadata
```

记录：

- 谁执行
- 用什么模型
- 花费多久
- 是否成功


---

## 7. Artifact Index

资产索引。

不保存图片本身。

```
artifact_id
episode_id
type
path
sha256
version
parent_id
created_time
```

例如：

```
frame05_final.png
```

数据库记录：

```
在哪里
来自哪里
哪个版本
```


---

## 8. Generation Attempt

图片生产尝试记录。

```
attempt_id
artifact_id
provider
model
prompt_sha
attempt_no
status
```

用于分析：

- 为什么失败
- 重试多少次
- 哪个模型效果好


---

# 四、Redis设计

Redis不是事实数据库。

负责实时状态。


## 1. 分布式锁

例如：

```
lock:frame:05
```

避免多个Worker重复生产。


## 2. 任务队列

例如：

```
queue:image_generation
```

保存等待执行任务。


## 3. Worker状态

例如：

```
worker:image_01
status=running
```


## 4. 实时进度

例如：

```
episode:EP002:progress
12/20
```


---

# 五、文件系统职责

继续保存：

```
episodes/

 story/
 character/
 frames/
 images/
 evidence/
 release/
```

原因：

- 大文件不进入数据库
- Git管理方便
- 人可直接查看


---

# 六、Memory系统职责

数据库不保存经验。

Memory保存：

## 用户偏好

例如：

```
喜欢现实摄影感
不要解释异常
```


## 创作经验

例如：

```
婚礼悬疑题材
异常不要提前暴露
```


## Agent经验

例如：

```
人物漂移修复方法
```


---

# 七、数据流

```
用户请求

↓

Workflow

↓

Task

↓

Runtime执行

↓

Event

↓

Trace

↓

Artifact

↓

Review

↓

Release
```


---

# 八、哪些数据不要进数据库

不要保存：

## 图片二进制

错误：

```
image_blob
```

正确：

```
path
sha
metadata
```


## 大段Prompt正文

保存：

```
prompt_sha
prompt_path
```


## Story全文

第一阶段继续文件管理。

数据库保存：

```
summary
index
metadata
```


---

# 九、迁移路线

## Phase 0

增加：

```
project

episode

workflow

task

event
```

不改变现有运行。


## Phase 1

接入：

```
trace
artifact
```


## Phase 2

接入：

```
Memory
Vector Search
```


## Phase 3

平台化：

支持：

- 多项目
- 多用户
- 多Agent
- 多媒体生产


---

# 十、最终架构

```
              Story OS

                  |

          Spring Boot Control

                  |

        ----------------------

        |                    |

      MySQL               Redis

     事实数据             实时状态


                  |

          Python Agent Runtime

                  |

          MCP / Skill

                  |

             Models

                  |

             Memory
```


# 结论

MySQL负责记账。

Redis负责现场调度。

文件系统负责资产。

Memory负责成长。

四者共同组成 Story OS 的数据基础设施。
