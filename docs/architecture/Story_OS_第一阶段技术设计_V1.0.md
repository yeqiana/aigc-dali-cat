# Story OS 第一阶段技术设计 V1.0

更新时间：2026-09-09

项目：Story OS

---

# 一、目标

本设计用于把《Story_OS_第一阶段实施任务拆解_V1.0.md》落到可编码级别。

第一阶段不是重写 Story OS，而是在现有 `episodes/_system`、Runtime DAG、Image Scheduler、Evidence Gate 继续稳定运行的前提下，新增平台基础设施。

核心原则：

> 先建立边界、索引、观测和控制能力，再迁移执行权。

第一阶段完成后应具备：

- Episode 可统一查询；
- Workflow / Task 可查询；
- Worker / Runtime 可观测；
- Event / Trace 可追踪；
- Artifact 可索引；
- Redis 可承担锁、实时状态和短期调度信息；
- 现有 Story OS 生产链路不被破坏。

---

# 二、P0 约束：事实源不得漂移

当前仓库已有明确约束：

- `<episode>/meta/episode-state.json` 仍是唯一阶段事实源；
- `story-gates.json` 只保存 Gate Evidence，不建立第二状态机；
- `runtime-request.json` 为绑定后的不可变请求；
- Trace / Event 只能记录执行事实，不授予 PASS。

因此第一阶段数据库的定位必须是：

> Projection / Query Model，而不是新的 Canonical State Machine。

第一阶段禁止：

1. 让 MySQL `episode.current_stage` 反向覆盖 `episode-state.json`；
2. 绕过 `episode_state.py transition` 直接由 Spring Boot 修改 Stage；
3. 因数据库记录存在而把无 Evidence 的任务判为成功；
4. 把 Redis 当永久事实源；
5. 把 Event / Trace 当 Gate Evidence。

正确方向：

```text
Canonical Files / Existing Runtime
            ↓
      Event / Projection
            ↓
          MySQL
            ↓
   Console / Query / Analytics
```

后续若要迁移事实源，必须单独做 Authority Migration 方案，不属于第一阶段。

---

# 三、第一阶段推荐目录

不迁移 `episodes/_system`。

新增外围平台目录：

```text
storyOS/
├── platform/
│   ├── control-plane/          # Spring Boot 控制面，后续独立服务
│   ├── contracts/              # 跨语言 DTO / Event / Schema
│   └── migrations/             # MySQL DDL / migration
│
├── core/
│   ├── ids.py
│   ├── clock.py
│   ├── errors.py
│   └── contracts.py
│
├── event/
│   ├── event.py
│   ├── publisher.py
│   └── event_types.py
│
├── trace/
│   ├── trace.py
│   ├── span.py
│   └── sink.py
│
├── artifact/
│   ├── model.py
│   ├── lineage.py
│   └── indexer.py
│
└── workflow/
    ├── model.py
    ├── projection.py
    └── query.py
```

注意：

这些目录第一阶段主要承担“平台抽象与适配”，不是立刻替换旧实现。

---

# 四、Java / Python 边界

## 4.1 Spring Boot Control Plane 负责什么

Spring Boot 第一阶段只做管理面和查询面：

- Project / Episode 查询；
- Workflow / Task 查询；
- Event / Trace 查询；
- Worker 状态展示；
- Artifact 索引查询；
- 后续为 MCP / Skill Registry 提供 API；
- 后续为前端 Console 提供统一接口。

第一阶段不负责：

- Story 生成；
- Prompt 编译；
- Image Generation；
- Review 判定；
- Episode Stage 直接推进；
- 取代现有 Python Runtime。

## 4.2 Python Runtime 负责什么

现有 Python Runtime 继续负责：

- Runtime DAG；
- Workflow 实际执行；
- Image Scheduler；
- Batch Runtime；
- Retry / Recovery；
- Gate / Evidence；
- Episode 状态推进。

新增一层 Platform Adapter：

```text
Existing Runtime
     ↓
Platform Adapter
     ├── publish_event()
     ├── write_trace()
     ├── project_task_state()
     └── index_artifact()
```

这样旧系统不需要知道 Spring Boot 内部结构。

---

# 五、数据模型设计

第一阶段 MySQL 推荐最小 7 张表：

1. `story_project`
2. `story_episode`
3. `workflow_instance`
4. `workflow_task`
5. `event_log`
6. `trace_span`
7. `artifact_index`

`generation_attempt` 可作为第一阶段后半段加入。

---

# 六、MySQL 表结构草案

以下字段是技术基线，不代表最终 SQL 已冻结。

## 6.1 story_project

```sql
CREATE TABLE story_project (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_key VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    description VARCHAR(1000) NULL,
    created_at DATETIME(3) NOT NULL,
    updated_at DATETIME(3) NOT NULL
);
```

## 6.2 story_episode

```sql
CREATE TABLE story_episode (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    project_id BIGINT NOT NULL,
    episode_key VARCHAR(255) NOT NULL,
    name VARCHAR(255) NULL,
    current_stage VARCHAR(64) NULL,
    runtime_status VARCHAR(32) NULL,
    canonical_state_path VARCHAR(1000) NOT NULL,
    canonical_state_sha256 CHAR(64) NULL,
    last_projected_at DATETIME(3) NULL,
    created_at DATETIME(3) NOT NULL,
    updated_at DATETIME(3) NOT NULL,
    UNIQUE KEY uk_project_episode(project_id, episode_key),
    KEY idx_episode_stage(current_stage),
    KEY idx_episode_runtime_status(runtime_status)
);
```

说明：

`current_stage` 只是 `episode-state.json` 的投影字段。

## 6.3 workflow_instance

```sql
CREATE TABLE workflow_instance (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    workflow_key VARCHAR(128) NOT NULL UNIQUE,
    episode_id BIGINT NOT NULL,
    workflow_type VARCHAR(64) NOT NULL,
    execution_mode VARCHAR(32) NULL,
    status VARCHAR(32) NOT NULL,
    checkpoint_ref VARCHAR(1000) NULL,
    started_at DATETIME(3) NULL,
    ended_at DATETIME(3) NULL,
    created_at DATETIME(3) NOT NULL,
    updated_at DATETIME(3) NOT NULL,
    KEY idx_workflow_episode(episode_id),
    KEY idx_workflow_status(status)
);
```

## 6.4 workflow_task

```sql
CREATE TABLE workflow_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_key VARCHAR(160) NOT NULL UNIQUE,
    workflow_id BIGINT NOT NULL,
    node_key VARCHAR(128) NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    attempt_no INT NOT NULL DEFAULT 0,
    retry_count INT NOT NULL DEFAULT 0,
    worker_id VARCHAR(128) NULL,
    error_code VARCHAR(128) NULL,
    error_summary VARCHAR(1000) NULL,
    started_at DATETIME(3) NULL,
    ended_at DATETIME(3) NULL,
    updated_at DATETIME(3) NOT NULL,
    KEY idx_task_workflow(workflow_id),
    KEY idx_task_status(status),
    KEY idx_task_worker(worker_id)
);
```

## 6.5 event_log

```sql
CREATE TABLE event_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_id VARCHAR(128) NOT NULL UNIQUE,
    event_type VARCHAR(128) NOT NULL,
    source VARCHAR(128) NOT NULL,
    project_key VARCHAR(128) NULL,
    episode_key VARCHAR(255) NULL,
    workflow_key VARCHAR(128) NULL,
    task_key VARCHAR(160) NULL,
    payload JSON NULL,
    occurred_at DATETIME(3) NOT NULL,
    created_at DATETIME(3) NOT NULL,
    KEY idx_event_type(event_type),
    KEY idx_event_episode(episode_key),
    KEY idx_event_task(task_key),
    KEY idx_event_occurred(occurred_at)
);
```

## 6.6 trace_span

```sql
CREATE TABLE trace_span (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    trace_id VARCHAR(128) NOT NULL,
    span_id VARCHAR(128) NOT NULL UNIQUE,
    parent_span_id VARCHAR(128) NULL,
    task_key VARCHAR(160) NULL,
    operation VARCHAR(128) NOT NULL,
    runtime VARCHAR(64) NULL,
    provider VARCHAR(64) NULL,
    model VARCHAR(128) NULL,
    status VARCHAR(32) NOT NULL,
    duration_ms BIGINT NULL,
    token_input BIGINT NULL,
    token_output BIGINT NULL,
    cost_micros BIGINT NULL,
    metadata JSON NULL,
    started_at DATETIME(3) NOT NULL,
    ended_at DATETIME(3) NULL,
    KEY idx_trace_id(trace_id),
    KEY idx_trace_task(task_key),
    KEY idx_trace_operation(operation)
);
```

## 6.7 artifact_index

```sql
CREATE TABLE artifact_index (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    artifact_id VARCHAR(128) NOT NULL UNIQUE,
    episode_key VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(64) NOT NULL,
    logical_name VARCHAR(255) NULL,
    relative_path VARCHAR(1000) NOT NULL,
    sha256 CHAR(64) NULL,
    version_no INT NOT NULL DEFAULT 1,
    parent_artifact_id VARCHAR(128) NULL,
    authority_level VARCHAR(32) NULL,
    metadata JSON NULL,
    created_at DATETIME(3) NOT NULL,
    KEY idx_artifact_episode(episode_key),
    KEY idx_artifact_type(artifact_type),
    KEY idx_artifact_sha(sha256)
);
```

---

# 七、Redis 设计

Redis 第一阶段只存短生命周期数据。

统一 Key Prefix：

```text
storyos:{env}:...
```

例如开发环境：

```text
storyos:dev:...
```

## 7.1 分布式锁

```text
storyos:dev:lock:episode:{episodeKey}
storyos:dev:lock:task:{taskKey}
storyos:dev:lock:frame:{episodeKey}:{frameNo}
```

要求：

- 必须设置 TTL；
- 必须有 owner token；
- 解锁必须校验 owner；
- 不允许永久锁。

## 7.2 Worker 心跳

```text
storyos:dev:worker:{workerId}
```

Hash 字段：

```text
status
runtime
current_task
last_heartbeat
capacity
```

TTL 建议：60~120 秒。

## 7.3 Episode 实时进度

```text
storyos:dev:episode:{episodeKey}:progress
```

Hash：

```text
stage
running_tasks
completed_tasks
failed_tasks
total_tasks
updated_at
```

该数据只用于 UI 实时展示，不作为事实源。

## 7.4 队列

如果第一阶段已有稳定 Python Scheduler，不强行迁移到 Redis Queue。

只有在明确需要跨进程 / 跨机器 Worker 时，再引入：

```text
storyos:dev:queue:image
storyos:dev:queue:review
```

第一阶段禁止“为了用了 Redis 就把现有 Scheduler 改成 Redis 队列”。

---

# 八、Event Contract

所有平台 Event 使用统一 Envelope：

```json
{
  "event_id": "evt_xxx",
  "event_type": "TASK_FAILED",
  "schema_version": 1,
  "source": "image_scheduler",
  "occurred_at": "2026-09-09T15:00:00+08:00",
  "project_key": "storyOS",
  "episode_key": "10_彼此的天上/02_玻璃另一边的手",
  "workflow_key": "wf_xxx",
  "task_key": "task_xxx",
  "trace_id": "trace_xxx",
  "payload": {}
}
```

第一阶段核心事件：

```text
WORKFLOW_STARTED
WORKFLOW_COMPLETED
WORKFLOW_FAILED
TASK_QUEUED
TASK_STARTED
TASK_RETRYING
TASK_COMPLETED
TASK_FAILED
WORKER_ONLINE
WORKER_OFFLINE
ARTIFACT_CREATED
ARTIFACT_UPDATED
EPISODE_STAGE_PROJECTED
```

注意：

`EPISODE_STAGE_PROJECTED` 表示数据库同步了文件事实，不表示数据库推进了阶段。

---

# 九、Trace Contract

建议统一三个层级：

## 9.1 Execution Trace

记录：

- Task
- Worker
- Runtime
- Provider
- Model
- Duration
- Cost
- Result

## 9.2 Decision Trace

记录重要决策：

```text
为什么 Retry
为什么 Repair
为什么切换 Provider
为什么标记 Tech Failed
```

Decision 不必独立成第一阶段新表，可先存：

```text
trace_span.metadata.decision
```

后续量大再拆。

## 9.3 Artifact Trace

由 `artifact_index` + `parent_artifact_id` + SHA 建立血缘。

---

# 十、Python Platform Adapter

第一阶段建议新增轻量适配接口，而不是 Runtime 直接访问 MySQL 表结构。

接口建议：

```python
class PlatformSink:
    def publish_event(self, event): ...
    def start_span(self, span): ...
    def finish_span(self, span): ...
    def project_episode(self, episode_snapshot): ...
    def project_workflow(self, workflow_snapshot): ...
    def project_task(self, task_snapshot): ...
    def index_artifact(self, artifact): ...
```

实现可以分：

```text
NoopPlatformSink
FilePlatformSink
HttpPlatformSink
```

默认必须允许：

```text
平台服务不可用
↓
现有生产继续运行
```

也就是说第一阶段 Control Plane 不能成为生产硬依赖。

---

# 十一、Spring Boot 模块建议

第一阶段不需要 Spring Cloud 微服务化。

先做单体控制面：

```text
platform/control-plane/
├── storyos-control-api
├── storyos-control-domain
├── storyos-control-infra
└── storyos-control-app
```

如果希望更轻量，也可单 Maven Module 起步。

建议包结构：

```text
com.storyos.platform
├── episode
├── workflow
├── task
├── event
├── trace
├── artifact
├── worker
└── common
```

技术建议：

- Spring Boot 3.x
- Java 17+
- MyBatis / MyBatis-Plus 二选一
- MySQL 8
- Redis
- Flyway 或 Liquibase 二选一

第一阶段不建议：

- Spring Cloud 全家桶；
- Kafka；
- Elasticsearch；
- Kubernetes 强依赖；
- 复杂 Service Mesh。

---

# 十二、Control Plane API

第一阶段以查询和 projection ingestion 为主。

## 12.1 Episode

```text
GET /api/v1/episodes
GET /api/v1/episodes/{episodeKey}
POST /internal/v1/projections/episodes
```

## 12.2 Workflow

```text
GET /api/v1/workflows
GET /api/v1/workflows/{workflowKey}
GET /api/v1/workflows/{workflowKey}/tasks
POST /internal/v1/projections/workflows
POST /internal/v1/projections/tasks
```

## 12.3 Event

```text
POST /internal/v1/events
GET  /api/v1/events
```

## 12.4 Trace

```text
POST /internal/v1/traces/spans
GET  /api/v1/traces/{traceId}
```

## 12.5 Artifact

```text
POST /internal/v1/artifacts
GET  /api/v1/episodes/{episodeKey}/artifacts
```

## 12.6 Worker

```text
GET /api/v1/workers
```

Worker 写入第一阶段可优先走 Redis heartbeat，而不是 MySQL 高频写。

---

# 十三、数据同步策略

第一阶段采用：

> Canonical File → Projection Adapter → MySQL

不采用双向同步。

## Episode Stage 同步

正确：

```text
episode_state.py transition
        ↓
文件 transition 成功
        ↓
读取最新 episode-state.json
        ↓
Platform Adapter 投影到 MySQL
```

错误：

```text
先改 MySQL stage
↓
再尝试改 episode-state.json
```

## Projection 失败

Projection 失败不得导致已完成的 canonical transition 回滚。

应：

1. 记录本地 projection pending；
2. 后台重放；
3. Console 标记 projection stale。

---

# 十四、幂等设计

第一阶段所有 ingestion 接口必须幂等。

建议：

- Event：`event_id` 唯一；
- Trace Span：`span_id` 唯一；
- Workflow：`workflow_key` 唯一；
- Task：`task_key` 唯一；
- Artifact：`artifact_id` 唯一；
- Episode：`project_id + episode_key` 唯一。

所有 projection 使用 Upsert 语义。

重复发送不能产生重复事实。

---

# 十五、失败与降级策略

第一阶段平台层必须是“可拔掉的”。

## MySQL不可用

- Control Plane 查询失败；
- Runtime 不停止；
- Projection 暂存本地；
- 恢复后重放。

## Redis不可用

- 实时进度和跨进程锁能力降级；
- 单机旧 Scheduler 可继续时继续；
- 不允许假装已获得分布式锁。

## Spring Boot不可用

Python Platform Adapter 自动进入：

```text
Noop / File Spool 模式
```

生产主链不得因此整体阻塞。

---

# 十六、旧代码接入点

第一阶段优先选择少量稳定边界接入，不全库埋点。

建议优先：

1. `episode_state.py`
   - Stage 投影事件；

2. `runtime_dag.py`
   - Workflow start/end；

3. `async_task_runtime.py`
   - Task lifecycle；

4. `image_scheduler.py`
   - image task / worker / retry；

5. `batch_scheduler.py`
   - batch execution trace；

6. `asset_lineage.py`
   - Artifact projection；

7. `final_candidate_snapshot.py`
   - Release artifact indexing。

原则：

> 先接边界，不在每个业务函数里散落数据库代码。

---

# 十七、测试设计

## 17.1 Unit

必须覆盖：

- Event serialization；
- Trace span lifecycle；
- Projection upsert；
- Artifact lineage；
- Redis lock owner 校验；
- Redis TTL；
- 幂等 ingestion。

## 17.2 Integration

使用 Docker Compose 启动：

```text
MySQL
Redis
Control Plane
```

验证：

- Python Adapter → Control Plane；
- Control Plane → MySQL；
- Worker heartbeat → Redis；
- 重复 Event 不重复写入。

## 17.3 Regression

必须继续跑现有 Story OS 测试。

重点保证：

```text
平台功能关闭
≈
改造前行为
```

## 17.4 Recovery Smoke

模拟：

1. Control Plane 中断；
2. Runtime 正常执行；
3. Event 暂存；
4. Control Plane 恢复；
5. Projection 重放；
6. 数据最终一致。

---

# 十八、第一阶段执行顺序

建议严格按以下顺序：

```text
P0.1 定义 contracts / IDs / Event Envelope
↓
P0.2 实现 NoopPlatformSink + File Spool
↓
P0.3 接 episode_state / runtime_dag 两个最小埋点
↓
P0.4 建 MySQL migration
↓
P0.5 建 Spring Boot Control Plane 骨架
↓
P0.6 实现 Projection Ingestion API
↓
P0.7 接 MySQL Repository
↓
P0.8 接 Redis Worker Heartbeat / Lock
↓
P0.9 接 Image Scheduler / Batch Scheduler Trace
↓
P0.10 Artifact Index
↓
P0.11 Integration + Recovery Smoke
```

---

# 十九、第一阶段明确不做

为了控制范围，以下内容不进入第一阶段：

- 不迁移 `episodes/_system` 到 `src/`；
- 不把 Workflow Authority 从文件迁移到数据库；
- 不重写 Runtime DAG；
- 不引入 Kafka；
- 不引入 Elasticsearch；
- 不引入 Kubernetes 作为开发硬依赖；
- 不正式接入 TencentDB-Agent-Memory / Mem0；
- 不做多租户；
- 不做完整 RBAC；
- 不做 Spring Cloud 微服务拆分；
- 不做新的图片 Provider 重构。

---

# 二十、验收标准

第一阶段必须同时满足：

## 兼容性

- 关闭 Platform Adapter 后现有 Runtime 正常运行；
- EP002/测试 Episode 不因 Control Plane 缺失而无法执行。

## 数据

- Episode / Workflow / Task / Event / Trace / Artifact 可查询；
- MySQL 与 canonical file 的 stage 投影一致；
- 投影漂移可检测。

## Redis

- Worker 状态可查询；
- 锁有 TTL；
- 锁 owner 安全释放。

## Trace

至少能回答：

- 哪个任务失败；
- 谁执行；
- 重试几次；
- 使用哪个 Runtime / Model；
- 耗时多少；
- 最终 Artifact 在哪里。

## Recovery

- Control Plane 暂停后 Runtime 可继续；
- 恢复后平台数据可重放补齐。

---

# 二十一、完成后的目标形态

第一阶段完成后：

```text
                        React Console（可后置）
                               ↓
                     Spring Boot Control Plane
                         ↓               ↓
                      MySQL            Redis
                         ↑               ↑
                         └──── Platform API ────┐
                                              │
Existing Story OS / Python Runtime            │
    ↓                                         │
Runtime DAG → Scheduler → Worker → Gate       │
    ↓                                         │
Canonical Files / Evidence                    │
    ↓                                         │
Platform Adapter ─────────────────────────────┘
```

这一步完成后，Story OS 会从“只能靠目录和日志理解运行状态”，升级为“既保留 Git/文件权威，又具备平台查询、Trace、Task、Artifact 和实时状态能力”。

---

# 二十二、结论

第一阶段最重要的不是 Spring Boot 本身，也不是 MySQL 本身。

真正目标是建立一个稳定边界：

> **现有 Story OS 继续负责生产真相，平台层负责管理、投影、查询和观测。**

这样后续再引入 Workflow Center、MCP、Skill、Memory、Web Console 时，不需要推翻当前已经稳定的生产链路。
