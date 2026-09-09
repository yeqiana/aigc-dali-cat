# Story OS V3 Phase 2-P2.1 Workflow Model 数据模型设计 V1.0

更新时间：
2026-09-09

分支：
story-platform-v3

---

# 一、设计目标

Phase 2 不替换 episode-state.json。

目标：

将 Workflow 从 Runtime 内部隐含状态，提升为平台可理解的数据模型。

当前：

```
episode-state.json
        |
        Runtime
```

演进：

```
Workflow Model
        |
Workflow Projection
        |
Runtime
```

---

# 二、设计原则

遵循数据库规范：

- bigint unsigned 主键
- snake_case命名
- datetime(3)
- 公共字段统一
- status 使用枚举
- JSON只保存扩展数据

禁止：

- Workflow表保存完整故事内容
- Workflow表替代Runtime状态文件
- 一个字段保存整个DAG

---

# 三、核心模型

## 1. workflow_definition

作用：

定义一个Workflow模板。

例如：

```
AI_STORY_PRODUCTION
```

字段：

```sql
id bigint unsigned
workflow_code varchar(64)
workflow_name varchar(128)
version varchar(32)
status varchar(32)
config_data json
created_time datetime(3)
updated_time datetime(3)
deleted tinyint
```

说明：

保存流程定义，不保存运行状态。

---

# 四、workflow_run

作用：

一次Workflow执行实例。

例如：

```
EP002 Production Run
```

字段：

```sql
id bigint unsigned

workflow_id bigint

episode_id bigint

run_no varchar(64)

status varchar(32)

started_time datetime(3)

finished_time datetime(3)

created_time datetime(3)

updated_time datetime(3)

deleted tinyint
```

状态：

```
CREATED
RUNNING
SUCCESS
FAILED
CANCELLED
```

---

# 五、workflow_step

作用：

Workflow中的步骤实例。

例如：

```
Prompt Compile
Image Generate
Review
Release
```

字段：

```sql
id bigint unsigned

workflow_run_id bigint

step_code varchar(64)

step_name varchar(128)

step_order int

status varchar(32)

task_id bigint

started_time datetime(3)

finished_time datetime(3)

created_time datetime(3)

updated_time datetime(3)

deleted tinyint
```

---

# 六、workflow_transition

作用：

描述步骤之间关系。

例如：

```
IMAGE_GENERATE
        |
        v
IMAGE_REVIEW
```

字段：

```sql
id bigint unsigned

workflow_id bigint

from_step_code varchar(64)

to_step_code varchar(64)

condition_data json

created_time datetime(3)

updated_time datetime(3)

deleted tinyint
```

---

# 七、与现有Runtime关系

当前：

```
episode-state.json

负责：
Runtime真实执行状态
```

新增：

```
workflow_run
workflow_step

负责：
平台查询和分析
```

---

# 八、双写策略

Phase 2采用：

```
Runtime
 |
 + episode-state.json
 |
 + Event
       |
       v
 Workflow Projection
       |
       v
 workflow_run / workflow_step
```

不允许：

```
Console直接修改workflow状态
```

---

# 九、索引设计

workflow_run：

```
idx_episode_id
idx_workflow_id_status
idx_created_time
```

workflow_step：

```
idx_workflow_run_id
idx_task_id
idx_status
```

workflow_transition：

```
idx_workflow_id
```

---

# 十、Phase 2后续

P2.1 Workflow Model

完成后进入：

```
P2.2 Workflow Projection

Event
 ↓
Projection
 ↓
Workflow状态查询
```

然后：

```
P2.3 Shadow Workflow Engine
```

---

# 总结

Workflow Model的定位：

不是替代Runtime。

而是让Story OS第一次拥有：

- 可查询Workflow
- 可分析执行过程
- 可支持Control Plane
- 可支撑Agent协作

的数据模型。