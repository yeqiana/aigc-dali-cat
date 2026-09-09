# Story OS V3 Phase1 MySQL 数据模型设计 V1.0

更新时间：

2026-09-09

分支：

story-platform-v3

依据：

《数据库设计规范 V1.0》


---

# 一、设计目标

Phase1 引入 MySQL 作为平台事实查询层。

原则：

数据库保存：

- 系统事实
- 对象关系
- 查询投影
- 历史记录

不保存：

- 图片文件
- Prompt正文大文件
- Runtime执行控制权
- Workflow唯一状态

继续保持：

```
episode-state.json

= 当前生产阶段事实源
```

MySQL：

```
= 平台查询事实层
```


---

# 二、数据库基础规范

遵循：

- snake_case
- bigint unsigned 主键
- datetime(3)
- created_time / updated_time
- deleted软删除
- status枚举字符串
- 索引统一idx/uk命名


---

# 三、核心表设计

## 1. project 项目表

用途：

管理Story OS项目。

```sql
CREATE TABLE project
(
 id bigint unsigned PRIMARY KEY,

 name varchar(64) NOT NULL COMMENT '项目名称',

 description varchar(255),

 status varchar(32) NOT NULL COMMENT '项目状态',

 created_time datetime(3) NOT NULL,
 created_by bigint,
 updated_time datetime(3),
 updated_by bigint,
 deleted tinyint DEFAULT 0
);
```

索引：

```
idx_status
```


---

# 2. episode 剧集表

对应：

```
episodes/**
```

```sql
CREATE TABLE episode
(
 id bigint unsigned PRIMARY KEY,

 project_id bigint unsigned NOT NULL,

 episode_name varchar(128) NOT NULL,

 episode_path varchar(255) NOT NULL,

 status varchar(32) NOT NULL,

 created_time datetime(3) NOT NULL,
 created_by bigint,
 updated_time datetime(3),
 updated_by bigint,
 deleted tinyint DEFAULT 0
);
```

索引：

```
idx_project_id
idx_status
```


---

# 3. workflow_run 工作流执行表

记录一次运行。

```sql
CREATE TABLE workflow_run
(
 id bigint unsigned PRIMARY KEY,

 episode_id bigint unsigned NOT NULL,

 workflow_type varchar(64) NOT NULL,

 status varchar(32) NOT NULL,

 started_time datetime(3),
 finished_time datetime(3),

 created_time datetime(3) NOT NULL,
 updated_time datetime(3),
 deleted tinyint DEFAULT 0
);
```

索引：

```
idx_episode_id
idx_status
```


---

# 4. task 任务表

对应 TaskContract。

```sql
CREATE TABLE task
(
 id bigint unsigned PRIMARY KEY,

 task_no varchar(64) NOT NULL,

 episode_id bigint unsigned NOT NULL,

 task_type varchar(64) NOT NULL,

 status varchar(32) NOT NULL,

 runtime varchar(32),

 started_time datetime(3),
 finished_time datetime(3),

 created_time datetime(3) NOT NULL,
 updated_time datetime(3),
 deleted tinyint DEFAULT 0,

 UNIQUE KEY uk_task_no(task_no)
);
```

索引：

```
idx_episode_id
idx_status
```


---

# 5. event_log 事件表

对应 EventContract。

```sql
CREATE TABLE event_log
(
 id bigint unsigned PRIMARY KEY,

 event_id varchar(64) NOT NULL,

 event_type varchar(64) NOT NULL,

 aggregate_type varchar(32) NOT NULL,

 aggregate_id varchar(64) NOT NULL,

 trace_id varchar(64),

 payload json,

 created_time datetime(3) NOT NULL,

 UNIQUE KEY uk_event_id(event_id)
);
```

索引：

```
idx_event_type
idx_aggregate_id
idx_trace_id
```


---

# 6. trace_span 链路表

对应 TraceContract。

```sql
CREATE TABLE trace_span
(
 id bigint unsigned PRIMARY KEY,

 trace_id varchar(64) NOT NULL,

 span_id varchar(64) NOT NULL,

 parent_span_id varchar(64),

 operation varchar(128) NOT NULL,

 status varchar(32) NOT NULL,

 duration_ms bigint,

 input_data json,

 output_data json,

 error_message varchar(255),

 created_time datetime(3) NOT NULL
);
```

索引：

```
idx_trace_id
idx_operation
```


---

# 7. artifact_index 资产索引表

对应 ArtifactContract。

```sql
CREATE TABLE artifact_index
(
 id bigint unsigned PRIMARY KEY,

 artifact_id varchar(64) NOT NULL,

 artifact_type varchar(32) NOT NULL,

 path varchar(255) NOT NULL,

 sha256 varchar(64) NOT NULL,

 owner_type varchar(32) NOT NULL,

 owner_id varchar(64) NOT NULL,

 created_by varchar(64),

 created_time datetime(3) NOT NULL,

 UNIQUE KEY uk_artifact_id(artifact_id)
);
```

索引：

```
idx_owner_id
idx_artifact_type
```


---

# 四、Redis设计

Redis不保存历史。

只保存实时状态。

例如：

```
task:{task_id}:status

worker:{worker_id}:heartbeat

queue:image

lock:episode:{id}
```


---

# 五、迁移策略

Phase1不直接切换。

当前：

```
Observer
 ↓
JSONL
```

升级：

```
Observer
 ↓
Repository
 ↓
JSONL + MySQL
```

双写阶段完成后：

```
MySQL成为查询源
```

但 Runtime 状态仍由原系统维护。


---

# 六、Phase1实施顺序

P1.1 MySQL表结构

P1.2 Event Repository

P1.3 Trace Repository

P1.4 Artifact Repository

P1.5 Redis Runtime State


---

# 结论

Phase1完成后，Story OS拥有：

- 平台数据层
- 执行历史查询能力
- 资产索引能力
- Runtime实时状态能力

同时不破坏V2.7生产链。