# Story OS 全局调度与 Agent 运行时最终优化方案 V1.0

> 日期：2026-09-18  
> 状态：Next Version Design / 已规划 / **暂不实施**  
> 目标：在不推翻 StoryOS 现有 Runtime / Workflow / Scheduler / Persistence 基础的前提下，吸收 Land 批处理调度的成熟思想，并结合 2026 年主流 Agent / Workflow / Durable Execution 架构，补齐 StoryOS 的全局调度层，使其从“单 Episode 自治执行”升级为“多 Episode 可持续生产运行时”。

---

# 1. 最终结论

StoryOS **已经具备调度系统的主体骨架**，包括：

- Episode Runner：单 Episode 生命周期驱动；
- Persistent Runner：单 Owner、Heartbeat、Lock；
- Workflow / DAG：阶段与依赖编排；
- scheduler_core：Production Queue、动态 admission、依赖判断、队列锁；
- AsyncTaskRuntime / Image Scheduler：局部并发 Worker；
- Retry / Recovery / Next Action：失败恢复；
- Redis Hot State / MySQL Repository / Runtime Workspace：运行态与持久态分层；
- Event / Trace / Artifact：观测基础。

当前真正缺失的不是“再造一个 scheduler_core”，而是 **高于 Episode Runner 的全局调度层**。

最终建议新增：

```text
StoryOS Runtime Coordinator
（全局运行时协调器 / 主调度器）
```

但它不应该被设计成一个简单的“主调度线程”，而应该被定义为一个**逻辑 Single Coordinator**：

```text
单活调度 Owner
+ Durable Dispatch State
+ Capacity Manager
+ Episode Registry
+ Lease / Heartbeat
+ Retry / Repair / Block
+ Event-driven Wakeup
+ Periodic Reconcile
```

单机阶段可以运行在一个常驻线程或独立进程中；架构上必须避免把“线程”当作权威模型，以便未来自然升级到独立 Runtime Service。

---

# 2. 本方案明确不做什么

本方案不做以下事情：

1. **不修改 WebCodex 的 6 槽位机制。**
2. 不把 WebCodex 6 槽位当成 StoryOS 生产调度池。
3. 不新增 WebCodex Coordinator / Scheduler。
4. 不推翻现有 `episode_runner.py`。
5. 不推翻现有 `scheduler_core.py`。
6. 不重新实现已有 Workflow / DAG。
7. 不让 Runtime Coordinator 直接修改 Episode 业务权威状态。
8. 不引入第二套 Production Queue。
9. 不为了“像 Agent 平台”而把所有 deterministic workflow 改成 LLM 决策。
10. 不直接照搬 Land 的 Java ThreadPool / synchronized 实现。
11. 不强依赖 Temporal、LangGraph、Microsoft Agent Framework、Google ADK 等外部框架。

WebCodex 仍然只是：

```text
开发 / 修复 / 审计 / 测试执行工具
```

StoryOS Runtime Coordinator 是：

```text
StoryOS 自身生产运行时能力
```

二者必须解耦。

---

# 3. Land 项目吸收结论

分析项目：

```text
D:\workspace\YeQianWorkSpace\dcits\SmartLiquidity\ground\land
```

重点参考：

```text
TaskCenterStartThread
TaskDispatchMainThread
TaskDispatchConditionThread
StartTaskThread
ConditionJobThread
ExecuteJobThread
TaskDispatchServiceUtil
TaskMonitorComponent
```

## 3.1 Land 的核心模型

Land 不是让所有线程自行找活，而是把系统分成两层：

```text
               TaskCenterStartThread
                       │
        ┌──────────────┴──────────────┐
        │                             │
ScheduledThreadPoolExecutor      ThreadPoolExecutor
   调度线程池                       执行线程池
        │                             │
        ├─ TaskDispatchMainThread      ├─ StartTaskThread
        └─ ConditionThread             ├─ ConditionJobThread
                                      └─ ExecuteJobThread
```

其中主调度线程负责：

```text
扫描
→ 判断节点状态
→ 生成执行计划
→ 判断任务依赖
→ 选择可执行任务
→ 投递 Worker Pool
```

Worker Pool 负责真正执行。

这是本方案最重要的吸收点：

> **调度权与执行权分离。**

## 3.2 Land 值得吸收的七个设计思想

### A. 主调度和业务执行分池

调度器保持轻量，不被长任务阻塞。

StoryOS 对应：

```text
Runtime Coordinator
        ↓
Episode Runner Pool
        ↓
各领域 Worker
```

### B. 执行计划先落事实，再执行

Land 先生成 Task Execution Plan，再真正启动任务。

StoryOS 应对应为：

```text
Dispatch Record
→ Lease
→ Episode Run
→ Runtime Event / Trace
```

这样才能恢复、追踪、重放，而不是“启动进程 = 调度事实”。

### C. Heartbeat + 失活节点识别

Land 会更新主机活动时间，并识别无法正常工作的节点。

StoryOS 应吸收为：

```text
Coordinator Heartbeat
Episode Runner Heartbeat
Worker Lease TTL
Stale Run Reconcile
```

### D. 依赖满足后再入执行池

Land 明确检查前置任务。

StoryOS 已经有 DAG / Queue Dependency，应继续保留，不把依赖逻辑搬进 Coordinator。

### E. Worker Pool 有独立容量

Land 的调度线程池和任务执行池容量不同。

StoryOS 应进一步升级为“资源槽位”而不是“线程数量”：

```text
Episode Slot
Image Slot
Agent Reasoning Slot
Review Slot
Host Action Slot
```

### F. 关键动作防重复

Land 使用执行状态和 synchronized 防重复调起。

StoryOS 应继续采用更强的：

```text
Lease
Idempotency Key
Single Writer
OS / Redis Lock
Repository CAS / 状态前置条件
```

### G. 调度池和任务池都可观测

Land 已经监控 queueSize、activeCount、taskCount 等。

StoryOS 应形成 Global Runtime Dashboard：

```text
Runnable Episodes
Running Episodes
Blocked Episodes
Queue Depth
Resource Utilization
Dispatch Latency
Retry / Repair / Block
Stale Lease
Throughput
```

---

# 4. Land 不应该直接照搬的部分

Land 属于经典批处理调度架构，StoryOS 是 Agent + Workflow + AIGC Runtime，两者不能简单复制。

不建议直接照搬：

- 固定周期 DB 全表扫描作为唯一触发方式；
- 大量 Thread / synchronized 作为跨进程一致性手段；
- 单纯依靠执行日志表表达所有 Runtime State；
- 将任务依赖、调度、执行、恢复全部集中到一个大 MainThread；
- 用线程数量直接代表业务资源容量；
- 把 Scheduler 做成业务状态的直接修改者。

StoryOS 应吸收其**设计思想**，而不是复制其实现技术。

---

# 5. 2026 主流 Agent / Workflow 架构吸收结论

StoryOS 最适合采用的不是“全 Agent 自主决策”，而是：

```text
Deterministic Workflow
        +
Specialized Agents
        +
Durable Runtime
        +
Global Coordinator
```

也就是“确定性骨架 + 智能节点”。

## 5.1 OpenAI Agents SDK：Manager / Handoff / Code Orchestration

OpenAI Agents SDK 当前明确区分：

- Manager / Agents as Tools；
- Handoffs；
- LLM orchestration；
- Code orchestration；
- parallel execution；
- tracing / guardrails / sessions / HITL。

对于 StoryOS：

```text
确定的生产流程
→ Code / Workflow 决策

创作、评审、语义判断
→ Agent 决策
```

不应该让 LLM 决定：

```text
是否越过生产 Gate
是否写 Canonical State
是否跳过失败
是否并发写 Authority
```

## 5.2 Microsoft Agent Framework：Workflow Graph + Agent Executor

Microsoft 2026 Agent Framework 的方向非常适合 StoryOS：

```text
Explicit Workflow Graph
+ Deterministic Executor
+ Agent Executor
+ Human-in-the-loop
+ Checkpoint / Resume
+ Sequential / Concurrent / Handoff
```

其核心思想是：

> 已知流程由 Graph 控制，只有需要智能判断的节点才交给 Agent。

这与 StoryOS 当前 Workflow / Gate / Review 架构高度一致。

## 5.3 Google ADK：Graph Workflow + Sequential / Parallel / Loop

Google ADK 已把 Workflow Agent 进一步演化到更灵活的 Graph Workflow / Dynamic Workflow。

StoryOS 可吸收：

- Sequential：Story → Storyboard → Visual Lock；
- Parallel：独立审计、检索、部分 Review；
- Loop：生成 → 评审 → 修复 → 再评审；
- Dynamic Routing：不同失败码进入不同恢复路径。

## 5.4 LangGraph：Checkpoint 与 Durable State

LangGraph 强调：

```text
Graph State Checkpoint
Thread-scoped Persistence
Resume
Failure Recovery
Human-in-the-loop
Long-term Store
```

StoryOS 已有：

```text
Checkpoint
Resume
Memory
Event / Trace
MySQL
Redis
Workspace
```

下一步不是引入 LangGraph，而是继续把这些能力统一成 StoryOS 自己的 Durable Runtime Contract。

## 5.5 Temporal：Task Queue + Worker Pull + Capacity Awareness

Temporal 最值得 StoryOS 吸收的是：

> Worker 有空闲容量时才从 Task Queue 获取任务。

以及：

- Task Queue 持久；
- Worker 崩溃任务不丢；
- Task Routing；
- Throttling；
- Retry；
- Worker Versioning；
- Workflow / Activity 分离。

StoryOS 不需要直接接 Temporal，但 Runtime Coordinator 应具备类似思想：

```text
任务不是“推给一个忙碌线程”

而是：

Capacity available
→ Reserve
→ Dispatch
→ Lease
→ Execute
→ Ack / Retry
```

---

# 6. StoryOS 当前已有的调度层

当前 StoryOS 并非“没有调度”。

实际上已经有三层。

## 6.1 Episode 生命周期调度

```text
persistent_runner_daemon
        ↓
episode_runner
        ↓
next_action / runtime_dag / workflow
```

负责：

- Episode Single Owner；
- Heartbeat；
- Retry；
- Capability Wait；
- Human Required；
- Resume；
- 生命周期推进。

## 6.2 Production Queue 调度

```text
scheduler_core
        ↓
image_scheduler / batch_scheduler
```

当前已经实现：

- queue transaction；
- cross-process lock；
- ready_items；
- dependency；
- dynamic admission；
- worker cap；
- first-completed 补位；
- technical failure 降并发；
- serial callback；
- ledger commit。

这已经是一个局部 Scheduler Kernel。

## 6.3 Worker Runtime

```text
AsyncTaskRuntime
Image Worker
Product Runtime Adapter
Review Runtime
Model Runtime
```

真正承担耗时执行。

---

# 7. StoryOS 当前缺口

当前最大的问题是：

```text
每个 Episode 知道自己下一步干什么

但是整个 StoryOS
不知道“现在应该让哪个 Episode 跑”
```

缺少全局视角：

- 当前共有多少 READY Episode；
- 当前有多少 RUNNING Episode；
- 谁在 HOST_WAIT；
- 谁在 CAPABILITY_WAIT；
- 谁失败可重试；
- 谁需要 Repair；
- 谁必须 Human Required；
- 哪个 Episode 快完成；
- 哪个 Episode 已长时间饥饿；
- 当前图片能力是否有余量；
- 当前模型调用能力是否有余量；
- 当前 Host Action 是否有余量；
- 是否允许启动新 Episode；
- 某个 Runner 死亡后谁负责重新领取。

因此当前架构可以概括为：

```text
局部自治：强
全局协调：弱
```

---

# 8. 最终目标架构

```text
                         ┌──────────────────────┐
                         │ Platform / Console   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │ StoryOS Runtime Coordinator  │
                    │ 全局运行时协调器              │
                    │                              │
                    │ Discover / Prioritize        │
                    │ Capacity / Lease             │
                    │ Dispatch / Reconcile         │
                    │ Retry / Repair / Block       │
                    └──────────────┬───────────────┘
                                   │
                         Episode Dispatch Queue
                                   │
                 ┌─────────────────┼─────────────────┐
                 ▼                 ▼                 ▼
          Episode Runner A   Episode Runner B   Episode Runner C
                 │                 │                 │
                 └─────────────────┼─────────────────┘
                                   ▼
                        Workflow / Runtime DAG
                                   │
                 ┌─────────────────┼──────────────────┐
                 ▼                 ▼                  ▼
         Deterministic        Agent Executor       Human Gate
           Executor
                 │                 │                  │
                 └─────────────────┼──────────────────┘
                                   ▼
                            Domain Runtime
                 ┌─────────────────┼──────────────────┐
                 ▼                 ▼                  ▼
          scheduler_core       Review Runtime     Tool / MCP
                 │
                 ▼
          Async Worker Pool
```

---

# 9. 四层职责必须严格分离

## 9.1 L0：Runtime Coordinator

只回答：

```text
谁应该运行？
什么时候运行？
还能运行几个？
失败后是 retry / repair / block？
谁需要被重新领取？
```

它不回答：

```text
这一帧是否合格？
剧情是否通过？
Episode 当前 canonical stage 应该写成什么？
```

## 9.2 L1：Episode Runner

只负责一个 Episode：

```text
我的当前状态是什么？
我的 Next Action 是什么？
我的 Workflow 下一步是什么？
我的失败如何恢复？
```

Episode Runner 仍然是 Episode 生命周期 Single Writer。

## 9.3 L2：Workflow / Agent

Workflow 决定 deterministic 路径。

Agent 负责：

- 创作；
- 分析；
- 评审；
- 分类；
- 建议；
- 非确定性决策。

Agent 不直接成为 Canonical State Writer。

## 9.4 L3：Worker Runtime

负责真正执行：

- 图片生成；
- 模型调用；
- 文件处理；
- Review；
- MCP / Tool；
- Host Action。

Worker 只返回 Result / Event，不决定全局生产状态。

---

# 10. Coordinator 的核心原则：Single Coordinator，不等于 Single Thread

推荐模型：

```text
Logical Single Active Coordinator
```

而不是把架构绑死到：

```text
Thread-1
```

单机 MVP 可以：

```text
一个常驻 Process
或者
Platform Runtime 中一个 Background Thread
```

但必须具有：

```text
Coordinator Lease
Coordinator ID
Heartbeat
Lease Expiry
Failover Claim
```

这样未来才能从：

```text
单机 StoryOS
```

升级到：

```text
多 Runner / 多 Worker
```

而不改调度语义。

---

# 11. 调度与执行彻底分离

最终模型：

```text
Coordinator
    │
    │ 只 Dispatch
    ▼
Episode Runner Pool
    │
    │ 只推进 Episode
    ▼
Workflow
    │
    │ 只产生可执行 Step
    ▼
Domain Worker Pool
    │
    │ 只执行 Work
    ▼
Result Event
```

Coordinator 不等待图片生成完成。

Coordinator 不等待 Agent 长推理完成。

Coordinator 只维护：

```text
Dispatch
Lease
Heartbeat
Capacity
Result State
```

因此一个长图片任务不会卡死整个调度循环。

---

# 12. Runtime Capacity：从“线程数”升级成“资源槽位”

StoryOS 不应统一使用一个 `max_workers` 表示所有能力。

建议定义：

```yaml
runtime_capacity:
  episode:
    max_active: configurable

  image:
    max_inflight: 3

  agent_reasoning:
    max_inflight: configurable

  review:
    max_inflight: configurable

  host_action:
    max_inflight: configurable

  io:
    max_inflight: configurable
```

注意：

> Slot 是业务资源许可，不等于 OS Thread。

例如：

```text
Episode A
  正在等待 Host Action

Episode B
  正在等模型返回

Episode C
  正在图片生成
```

三个 Episode 可以同时存在，但使用的是不同资源。

---

# 13. Resource-Aware Scheduling

每个可执行 Step 应声明资源需求：

```json
{
  "resource_class": "image",
  "units": 1,
  "exclusive_authority": "episode:EP021:production_queue"
}
```

Coordinator 调度时判断：

```text
Runnable
+
Dependency Satisfied
+
Capacity Available
+
Authority Available
+
No Human Block
=
Dispatchable
```

这比“有线程就跑”更适合 StoryOS。

---

# 14. Episode Dispatch Queue

新增全局逻辑队列：

```text
Episode Dispatch Queue
```

注意：

> 它不是 Production Queue 的替代品。

两者职责：

```text
Episode Dispatch Queue
决定哪个 Episode 获得 Runner

Production Queue
决定一个 Episode 内哪些图片任务执行
```

建议状态：

```text
DISCOVERED
READY
RESERVED
RUNNING
WAITING_RESOURCE
RETRY_WAIT
REPAIR_REQUIRED
HUMAN_REQUIRED
COMPLETED
FAILED_TERMINAL
CANCELLED
```

---

# 15. 调度优先级

不建议简单 FIFO。

建议默认：

```text
P0 恢复中的 Episode
P1 接近完成且无阻塞的 Episode
P2 已等待较久的正常 Episode
P3 新建 Episode
P4 Speculative / Optimization
```

再增加 Aging：

```text
等待时间越长
Priority Boost 越高
```

避免某篇长期饥饿。

最终 Priority Score 只用于**调度顺序**，不影响内容质量决策。

---

# 16. Coordinator 主循环

推荐混合模式：

```text
Event Driven
+
Periodic Reconcile
```

不要只靠固定 30 秒轮询。

逻辑：

```text
while active:

    1. ingest runtime events

    2. reconcile stale leases

    3. discover runnable episodes

    4. refresh capacity

    5. rank candidates

    6. reserve capacity

    7. create dispatch record

    8. launch / attach Episode Runner

    9. observe completion / wait / failure

   10. release capacity

   11. classify retry / repair / block

   12. sleep until:
       - event arrives
       - capacity releases
       - retry becomes due
       - reconcile timer fires
```

---

# 17. Durable Dispatch：必须先有事实，再有执行

参考 Land Execution Plan 和 Temporal Durable Task。

顺序必须是：

```text
Create Dispatch Record
        ↓
Reserve Lease
        ↓
Start / Attach Runner
        ↓
Runner ACK
        ↓
RUNNING
```

不能：

```text
先启动 subprocess
再猜它是不是已经开始
```

建议 Dispatch Record：

```text
dispatch_id
episode_id
episode_uid
workflow_version
requested_action
resource_class
priority
status
owner_id
lease_until
attempt
created_at
started_at
finished_at
last_heartbeat
last_error_code
resume_token
trace_id
```

---

# 18. Exactly Once 不作为目标

生产调度应采用：

```text
At-least-once Dispatch
+
Idempotent Execution
+
Single Writer Authority
```

而不是追求不可实现的跨进程 Exactly Once。

每个执行入口都必须有：

```text
Idempotency Key
Precondition
Current State Check
Authority Check
```

重复 Dispatch 应变成：

```text
ATTACH_EXISTING
ALREADY_COMPLETED
NOOP
```

而不是重复生成或重复写入。

---

# 19. Single Writer 最终边界

必须明确每个权威域只有一个写 Owner。

| Authority | Writer |
|---|---|
| Global Dispatch | Runtime Coordinator |
| Episode Lifecycle | Episode Runner / Workflow |
| Production Queue | scheduler_core |
| Frame / Image Attempt | Production Runtime |
| Review Decision | Review Persistence / Gate |
| Approval | Approval Persistence |
| Release | Release Persistence |
| Runtime Hot State | 对应 Runtime Store |
| Artifact Binary | Runtime Workspace |

Coordinator **严禁**：

```text
直接改 episode-state
直接改 production-ledger
直接改 frame-review
直接改 release-manifest
```

它只能触发合法 Owner 执行。

---

# 20. Redis / MySQL / Workspace 最终职责

## 20.1 MySQL：Durable Fact / Control Plane

适合：

- Episode Registry；
- Dispatch Record；
- Workflow Run；
- Run Attempt；
- Event / Trace Metadata；
- Approval / Review / Release；
- Durable Checkpoint；
- Recovery History；
- Coordinator election / lease metadata（如需要）。

原则：

```text
可审计
可查询
可恢复
必须长期保留
```

## 20.2 Redis：Hot Runtime State

适合：

- Capacity；
- Active Lease；
- Heartbeat；
- Runnable Hint；
- Current Runner；
- Fast Routing；
- Rate Limit；
- Short-lived lock；
- Wakeup Signal。

原则：

```text
丢失后可从 Durable Fact 重建
```

## 20.3 Runtime Workspace：Large Evidence / Artifact

继续保存：

- 图片；
- 大模型原始输出；
- Prompt Package 大文档；
- Evidence；
- 日志；
- 大型报告；
- 可重建/可外置的大 JSON。

MySQL 只保留：

```text
identity
hash
projection
reference
query fields
```

继续遵循当前 Payload Slimming 方向。

---

# 21. Agent 在最终架构里的位置

不建议定义一个“万能 Master Agent”。

建议：

```text
Runtime Coordinator
不是 Agent
```

它是 deterministic control plane。

Agent 存在于 Workflow 节点中。

推荐 Specialist Agents：

```text
Story Agent
Storyboard Agent
Visual Planning Agent
Prompt Agent
Review Agent
Repair Advisor Agent
Release Advisor Agent
Memory / Experience Advisor
```

Coordinator 不询问 LLM：

```text
“下一篇应该跑谁？”
```

而是用明确策略计算。

---

# 22. Manager Agent 只用于开放式任务

可在 Episode 内部增加：

```text
Episode Supervisor Agent
```

但只用于：

- 创作策略；
- 信息汇总；
- 多 Agent 协作；
- 非确定性问题分析。

不能用于：

- Queue Lock；
- Durable Retry；
- Stage Authority；
- Production Gate；
- Resource Allocation。

最终模型：

```text
Global Coordinator = Deterministic

Workflow            = Deterministic Graph

Agent Node          = Intelligent

Worker              = Deterministic Executor
```

---

# 23. Failure Taxonomy 最终统一

当前 StoryOS 已经有多个 failure code，应进一步统一为三大调度动作：

## RETRY

临时技术故障：

- network；
- timeout；
- provider busy；
- transient IO；
- temporary capacity unavailable。

行为：

```text
Exponential Backoff
+ Retry Budget
+ Jitter
```

## REPAIR

状态或产物可以自动修复：

- stale derived asset；
- recoverable queue residue；
- invalid projection；
- contract mismatch 可重建；
- failed derived prompt。

行为：

```text
Repair Task
→ Validate
→ Requeue
```

## BLOCK

无法自动解决：

- Human Required；
- Policy Decision；
- Missing Authority；
- Semantic Ambiguity；
- destructive migration ambiguity。

行为：

```text
释放执行 Slot
保留 Durable State
等待外部决策
```

这与用户当前要求的：

```text
retry / repair / block
```

完全一致。

---

# 24. Recovery Model

每个 Dispatch 都有 Lease。

```text
RESERVED
   ↓
RUNNING
   ↓
Heartbeat
```

超过 TTL：

```text
STALE
  ↓
Reconcile
  ├─ Runner still alive → ATTACH
  ├─ Durable work finished → COMMIT RESULT
  ├─ Work unknown → SAFE RECONCILE
  └─ Work never started → REQUEUE
```

禁止：

```text
超时
→ 直接重新生成
```

特别是图片/模型任务必须先判断已有结果，避免重复消费与重复事实。

---

# 25. Human-in-the-loop

Human Required 不应该占 Worker。

```text
RUNNING
  ↓
HUMAN_REQUIRED
  ↓
Release Capacity
  ↓
Persist Context
  ↓
Human Decision
  ↓
READY
```

这样一篇卡人工不会拖住其他 Episode。

---

# 26. 多 Episode 并行最终模型

例如：

```text
Backlog

EP021 READY
EP022 READY
EP023 READY
EP024 READY
EP025 READY
```

假设当前 Episode Capacity = 3：

```text
Coordinator
   │
   ├─ EP021 → Runner A
   ├─ EP022 → Runner B
   ├─ EP023 → Runner C
   │
   ├─ EP024 WAITING
   └─ EP025 WAITING
```

当 EP022：

```text
HOST_WAIT
```

它释放执行资源：

```text
EP024 → Runner Slot
```

当 EP021：

```text
COMPLETED
```

立即补：

```text
EP025
```

这才是 StoryOS 自己真正的“空槽补位”。

与 WebCodex 六槽无关。

---

# 27. Episode 内部并发继续由 scheduler_core 管

不要把图片调度移到 Global Coordinator。

保持：

```text
Runtime Coordinator
      ↓
Episode Runner
      ↓
scheduler_core
      ↓
Image Workers
```

当前 `scheduler_core.run_execution_loop` 已经具备：

- max worker cap；
- dynamic admission；
- first completed refill；
- dependency unlock；
- technical failure capacity reduction；
- serial consume callback。

应该继续作为 Episode 内局部 Scheduler Kernel。

---

# 28. Event Contract

建议 Coordinator 只消费统一 Runtime Event：

```text
EPISODE_READY
EPISODE_STARTED
STEP_STARTED
STEP_COMPLETED
STEP_FAILED
RESOURCE_WAIT
HUMAN_REQUIRED
RUNNER_HEARTBEAT
RUNNER_STALE
RECOVERY_STARTED
RECOVERY_COMPLETED
EPISODE_COMPLETED
EPISODE_FAILED
```

所有事件至少带：

```text
event_id
episode_uid
run_id
dispatch_id
trace_id
event_type
occurred_at
source
payload_projection
```

大 payload 继续外置。

---

# 29. State Machine

Global Dispatch：

```text
DISCOVERED
    ↓
READY
    ↓
RESERVED
    ↓
RUNNING
    ├────────────→ WAITING_RESOURCE
    ├────────────→ RETRY_WAIT
    ├────────────→ REPAIR_REQUIRED
    ├────────────→ HUMAN_REQUIRED
    ├────────────→ FAILED_TERMINAL
    └────────────→ COMPLETED
```

只允许显式 transition。

不要通过“某个 JSON 是否存在”推测状态。

---

# 30. Backpressure

全局调度必须支持背压。

当：

```text
Image Capacity = 0
```

Coordinator 不再启动大量会立即卡在图片阶段的新 Episode。

当：

```text
Model Provider degraded
```

降低 Agent Reasoning admission。

当：

```text
Review backlog too high
```

优先清 Review，限制上游生成。

这比固定最大 Episode 并发更重要。

---

# 31. Queue Fairness

建议采用：

```text
Priority
+
Aging
+
Resource Awareness
```

不建议纯 Priority，否则低优先级 Episode 可能永久饿死。

可定义：

```text
effective_priority
=
base_priority
+ recovery_bonus
+ near_completion_bonus
+ wait_age_bonus
- expensive_resource_penalty
```

第一版不必复杂，先支持 Aging 即可。

---

# 32. 可观测性

Console 至少显示：

## Coordinator

- leader / follower；
- heartbeat；
- loop latency；
- last reconcile；
- dispatch count；
- stale lease count。

## Queue

- READY；
- RUNNING；
- WAITING_RESOURCE；
- RETRY_WAIT；
- REPAIR_REQUIRED；
- HUMAN_REQUIRED。

## Capacity

- Episode Slots；
- Image Slots；
- Agent Slots；
- Review Slots；
- Host Slots。

## Performance

- Episode lead time；
- stage latency；
- dispatch latency；
- queue wait；
- retry count；
- recovery success；
- resource utilization；
- throughput。

## Reliability

- duplicate dispatch prevented；
- stale runner recovered；
- orphan result reconciled；
- authority conflict；
- queue mutation busy。

---

# 33. 建议新增模块

基于 V3 Platform 化方向，新的全局能力建议进入：

```text
platform/runtime/coordinator/
```

建议：

```text
runtime_coordinator.py
episode_registry.py
dispatch_model.py
dispatch_repository.py
capacity_manager.py
scheduling_policy.py
lease_manager.py
recovery_reconciler.py
event_consumer.py
coordinator_metrics.py
```

Compatibility Adapter：

```text
episodes/_system/coordinator_adapter.py
```

只负责把已有 Episode Runner 接入新 Coordinator。

不要把新全局逻辑继续堆进：

```text
episode_runner.py
scheduler_core.py
```

---

# 34. 数据模型建议

不要求一次全部建表。

最小集：

## Runtime Episode

```text
episode_uid
episode_path_ref
lifecycle_state
runtime_state
priority
created_at
updated_at
```

## Dispatch

```text
dispatch_id
episode_uid
action
status
attempt
owner
lease_until
resource_class
trace_id
error_code
created_at
started_at
completed_at
```

## Capacity Snapshot

第一版可以放 Redis：

```text
resource_class
capacity
in_use
reserved
updated_at
```

History 进入 MySQL Event / Trace，不必每次 Snapshot 都永久存。

---

# 35. 调度策略第一版必须简单

不要第一版就做复杂 AI Scheduler。

V1：

```text
1. Filter runnable
2. Filter authority
3. Filter resource
4. Priority + Aging
5. Reserve
6. Dispatch
```

足够。

后续 Experience Store 可以用于**建议调度参数**，但不直接改权威策略。

例如：

```text
历史统计发现图片 Provider 最近失败率升高
→ Advisor 建议降低 image capacity

而不是：
LLM 自动把 capacity 从 3 改成 1
```

---

# 36. 配置

建议增加：

```yaml
runtime_coordinator:
  enabled: false

  reconcile_interval_seconds: 10
  lease_ttl_seconds: 60

  episode_capacity:
    max_active: 2

  scheduling:
    policy: priority_aging

  recovery:
    retry_limit: 3
    auto_attach: true
    stale_reclaim: true
```

其中数值只是初始 Canary 配置，应通过真实生产数据校准，不作为长期硬编码。

现有：

```text
production.max_inflight_images
```

继续由 Image Scheduler 管，不迁移到 Coordinator。

---

# 37. 启动模型

第一阶段：

```text
story_os.py coordinator start
```

或者：

```text
platform runtime coordinator
```

它启动：

```text
Coordinator Loop
+
Heartbeat
+
Event Consumer
+
Reconciler
```

Episode Runner 仍使用现有入口。

Coordinator 只是统一调用。

---

# 38. 兼容现有一句话生产

当前：

```text
story_os.py create "..." --full-auto
```

必须继续可用。

兼容模式：

```text
Coordinator Disabled
→ 当前行为完全不变
```

Coordinator Enabled：

```text
create
→ Register Episode
→ READY
→ Coordinator Dispatch
→ Episode Runner
```

这样可以灰度切换。

---


# 39. 下一版本迭代范围（已规划，暂不实现）

> **状态：PLANNED / DEFERRED / 暂不实现。**  
> 本节与 Runtime Coordinator 一起归入 StoryOS 的**下一版本架构迭代**。当前版本只冻结设计，不进入代码实施，不作为当前正式生产验收的阻塞前置。

下一版本包含两条并行升级主线：

```text
Track A：Runtime Scheduling Upgrade
全局调度 / Capacity / Lease / Dispatch / Recovery

Track B：Retrieval Intelligence Upgrade
问题重写 / Knowledge Router / 结构化知识 / Hybrid Retrieval / Rerank / Context Builder
```

两条主线共同服务于同一个目标：

```text
Runtime Coordinator
负责“谁运行、何时运行、还能运行几个”

Retrieval Intelligence Layer
负责“Agent 在运行时应该拿到哪些知识、经验和上下文”
```

## 39.1 Track A：全局调度架构升级

沿用本方案前文的 Runtime Coordinator 设计：

- Global Episode Dispatch；
- Capacity Manager；
- Lease / Heartbeat；
- Retry / Repair / Block；
- Stale Reconcile；
- Multi-Episode Scheduling；
- Resource-aware Scheduling；
- Backpressure；
- Single Coordinator + Single Writer Boundary。

当前状态：

```text
DESIGN_FROZEN
IMPLEMENTATION_DEFERRED
```

## 39.2 Track B：Retrieval Intelligence / RAG 能力升级

不单独建设一个传统“向量数据库式 RAG 系统”，而是在现有：

```text
Memory
Experience Store
Story DNA
Similarity
Advisor
Agent Registry
Skill Registry
MCP Registry
Event / Trace
MySQL / Redis
```

基础上，补齐统一 Retrieval Layer：

```text
Task / User Input
        ↓
Retrieval Query Planner
问题规范化 / 问题重写 / 多查询拆解
        ↓
Knowledge Router
按 Story / Visual / Production / Runtime / Experience / Rules 路由
        ↓
Structured Knowledge
结构化实体 / Metadata / Evidence Level
        ↓
Hybrid Retrieval
Metadata Filter + Keyword/BM25 + Semantic Retrieval
        ↓
Reranker
相关性 + Authority + Evidence + Recency
        ↓
Context Builder
去重 / 压缩 / 引用 / Token Budget
        ↓
Specialist Agent
```

### 数据结构化

优先把历史问题、生产经验、规则、Episode 资产从“整篇 MD/JSON 文档”抽象成可检索实体。

建议最小字段：

```text
knowledge_id
knowledge_type
domain
episode_uid
stage
issue_code
entities
symptoms
root_cause
resolution
evidence_level
verified_by
created_at
updated_at
source_ref
```

目标不是把所有文档全部直接 embedding，而是：

```text
结构化事实优先
文档 Chunk 补充
向量语义召回兜底
```

### Retrieval Query Planner

负责把自然语言或 Workflow Task 转成检索计划。

例如：

```text
“Frame19 人脸为什么又变了？”
```

转成：

```json
{
  "intent": "diagnose_identity_drift",
  "domain": "visual_consistency",
  "episode_uid": "...",
  "frame": 19,
  "entities": ["character_identity"],
  "queries": [
    "identity anchor missing",
    "reference injection",
    "face consistency"
  ]
}
```

问题重写应**按需触发**，不是所有查询强制改写。

### Knowledge Router

与 Agent Router 严格区分：

```text
Agent Router
→ 选择谁来执行

Knowledge Router
→ 选择到哪里找知识
```

建议知识域：

```text
Story Knowledge
Visual Knowledge
Character / Identity Knowledge
Production Knowledge
Runtime Incident
Experience Store
Project Rules
Release / Quality Rules
```

### Hybrid Retrieval

StoryOS 中大量信息是精确 ID：

```text
EP003
Frame19
W-17
P02_face
VISUAL_LOCK
PRODUCTION
```

因此不采用纯向量检索。

推荐：

```text
Metadata Filter
      +
Keyword / BM25
      +
Semantic Vector
      ↓
Candidate Set
```

### Reranker

第一轮召回强调 Recall，第二轮重排强调 Precision。

建议排序因素：

```text
semantic_relevance
metadata_match
authority_level
evidence_level
verification_status
recency
episode_similarity
```

其中 Evidence Level 必须进入排序：

```text
设计建议              < 实际事故
实际事故              < 修复后测试通过
测试通过              < 真实生产验证通过
```

避免未经验证的设计意见压过生产事实。

### Context Builder

Agent 最终不直接吃 Top-N 原始 Chunk。

Context Builder 负责：

- 去重；
- 合并同源事实；
- 按 Authority 排序；
- 保留证据引用；
- Context Token Budget；
- 长文摘要；
- 冲突事实标注；
- 当前 Episode 信息优先。

### Retrieval Evaluation

下一版本实现 Retrieval 时必须同时建设评测集，而不是上线后凭感觉判断。

至少覆盖：

```text
Precision@K
Recall@K
MRR / NDCG
Correct Source Rate
Unsupported Context Rate
Context Redundancy
Retrieval Latency
Agent Answer Grounded Rate
```

测试集优先来自 StoryOS 已经发生过的真实问题：

```text
W-17
W-20
身份锚
Frame Contract
Visual Lock
Network Error
Queue Recovery
Provider Failure
Release Gate
```

## 39.3 两条升级主线的边界

最终关系：

```text
                 Runtime Coordinator
                 【运行时调度】
                         │
                   Episode Runner
                         │
                     Workflow
                         │
                  Agent Router
                         │
             ┌───────────┴───────────┐
             │                       │
      Specialist Agent       Retrieval Intelligence
                                     │
                              Query Planner
                                     │
                              Knowledge Router
                                     │
                             Hybrid Retrieval
                                     │
                                  Rerank
                                     │
                              Context Builder
                                     │
             └──────────── Context ──┘
```

必须保持：

```text
调度层不做知识检索决策
知识检索层不做 Runtime Capacity 决策
Agent 不直接写 Global Dispatch Authority
Coordinator 不直接写 Agent Memory 内容
```

## 39.4 当前版本冻结原则

当前版本：

```text
Runtime Coordinator      = 不实现
Retrieval Intelligence   = 不实现
Query Rewrite            = 不实现
Knowledge Router         = 不实现
Hybrid Retrieval         = 不实现
Reranker                 = 不实现
Context Builder          = 不实现
```

只允许：

- 记录设计；
- 保留未来接口空间；
- 避免当前改造与下一版本方向冲突；
- 当前正式生产验收发现的问题继续修复；
- 不为了下一版本提前引入新 Runtime 行为。

进入下一版本的前置条件：

```text
当前 Persistence / Hot State / Recovery 收口
        ↓
当前正式生产验收通过
        ↓
Stable Baseline Freeze
        ↓
启动下一版本 Track A / Track B
```

---

# 40. 渐进式实施阶段


## Phase S0：Freeze 当前生产基线

前置：

- 当前 Persistence / Redis / JSON Cutover 收口；
- System / Platform 全绿；
- 当前正式生产验收基线冻结。

产出：

```text
Coordinator Design Freeze
```

本阶段不改 Runtime 行为。

## Phase S1：Shadow Coordinator

实现：

- Episode Registry；
- Discover；
- Scheduling Policy；
- Capacity Snapshot；
- Dispatch Plan。

但：

```text
只计算
不启动 Episode
```

与现有真实 Runner 对比：

```text
Shadow Decision
vs
Actual Execution
```

目标：

```text
0 authority mutation
0 production impact
```

## Phase S2：Single Episode Dispatch

Coordinator 开始真正启动 Episode，但：

```text
max_active = 1
```

验证：

- Lease；
- Heartbeat；
- Dispatch；
- Attach；
- Resume；
- Retry；
- Human Wait；
- Completion。

## Phase S3：Multi Episode Capacity

开放：

```text
max_active > 1
```

验证：

- Slot refill；
- resource-aware；
- fairness；
- no cross-episode authority conflict；
- one episode blocked does not block others。

## Phase S4：Resource Queue

加入：

- Image capacity；
- Agent reasoning capacity；
- Review capacity；
- Host action capacity；
- Backpressure。

## Phase S5：Agent Orchestration Normalization

把 Agent 使用统一为：

```text
Agent Executor
Agent-as-tool
Handoff
Evaluator Loop
Parallel Agent
```

但 Workflow Authority 不变。

## Phase S6：Production Closure

连续真实 Episode：

- ≥ 3 篇；
- 0 工程修代码救场；
- 至少一次 Coordinator / Runner 受控故障恢复；
- 至少一次 Resource Exhaustion；
- 至少一次 Human Required；
- 最终全部到 PUBLISH_READY。

---

# 41. 测试方案

## Unit

- Scheduling Policy；
- Aging；
- Capacity；
- Lease；
- State Transition；
- Retry Budget；
- Idempotency。

## Contract

- Coordinator 不能写 Episode Authority；
- Episode Runner 保持 Single Owner；
- scheduler_core 保持 Production Queue Single Writer；
- Resource Slot 与 Thread 数解耦；
- Redis 丢失后可重建；
- MySQL durable facts 可恢复。

## Concurrency

必须测试：

```text
2 Coordinator 同时启动
→ 只有 1 个 active owner

2 次 Dispatch 同 Episode
→ 只有 1 个 Runner owner

Runner stale + recovery
→ attach/requeue 正确

Capacity=2 + 5 Episodes
→ active 永远 <= 2

一个 Human Required
→ 其他 Episode 正常继续
```

## Failure Injection

- Coordinator kill；
- Runner kill；
- Redis restart；
- MySQL transient error；
- Image timeout；
- Agent timeout；
- Host Action timeout；
- stale lease；
- duplicate event；
- delayed event；
- out-of-order event。

## Long Run

至少：

```text
24h Soak
多 Episode
随机 Failure Injection
无 orphan RUNNING
无重复 authority write
无永久 queue starvation
```

---

# 42. 正式生产验收指标

Coordinator 上线验收建议：

```text
Duplicate Dispatch          = 0
Concurrent Authority Writer = 0
Orphan RUNNING              = 0
Lost Dispatch               = 0
Queue Starvation            = 0
Recovery Success            >= 目标阈值
Unexpected Human Rescue     = 0
```

性能指标：

```text
Coordinator loop p95
Dispatch latency p95
Queue wait p95
Episode lead time
Slot utilization
Throughput
```

具体阈值通过 Canary 基线确定，不在设计阶段拍脑袋写死。

---

# 43. 与当前正式生产验收的关系

当前 StoryOS 正处在已有 V3 Runtime 的生产收口阶段。

因此：

> **不要现在立刻插入 Runtime Coordinator 大改，打断即将开始的正式生产验收。**

推荐顺序：

```text
当前 Persistence / Hot State / Recovery 收口
        ↓
现有 StoryOS 正式生产验收
        ↓
Freeze Stable Baseline
        ↓
Coordinator Phase S1 Shadow
        ↓
Coordinator Canary
```

也就是说：

```text
Runtime Coordinator
属于“下一层能力增强”

不是当前验收的阻塞前置
```

这一点非常重要。

---

# 44. 最终架构定位

StoryOS 最终不应该只是：

```text
AIGC 脚本集合
```

也不应该变成：

```text
纯传统批处理调度平台
```

目标应该是：

```text
Durable Agent Workflow Runtime
+
AIGC Production Operating System
```

其核心层次：

```text
┌─────────────────────────────────────────┐
│ Product / Console                       │
├─────────────────────────────────────────┤
│ Runtime Coordinator                     │
│ 全局调度 / Capacity / Lease / Recovery   │
├─────────────────────────────────────────┤
│ Episode Runtime                         │
│ Runner / Workflow / DAG / Checkpoint    │
├─────────────────────────────────────────┤
│ Agent Runtime                           │
│ Specialist / Handoff / Agent-as-tool    │
├─────────────────────────────────────────┤
│ Domain Scheduler                        │
│ scheduler_core / Review / Image         │
├─────────────────────────────────────────┤
│ Worker Runtime                          │
│ Model / Image / Tool / MCP / Host       │
├─────────────────────────────────────────┤
│ Durable State                           │
│ MySQL / Redis / Workspace / Event       │
└─────────────────────────────────────────┘
```

---

# 45. 最终决策

## 应该做

下一版本新增两条架构主线（当前均 **暂不实现**）：

```text
Track A
StoryOS Runtime Coordinator

Track B
Retrieval Intelligence Layer
Query Planner / Knowledge Router / Structured Knowledge
Hybrid Retrieval / Reranker / Context Builder
```

吸收 Land：

```text
主调度与执行池分离
执行计划
Heartbeat
Failover
依赖
Worker Capacity
运行监控
```

吸收主流 Agent：

```text
Deterministic Workflow
Specialized Agents
Manager / Handoff
Graph Execution
Checkpoint / Resume
Durable Task
Human-in-the-loop
Resource-aware Scheduling
Event / Trace
```

## 不应该做

不要：

```text
新增一个万能 AI Master Agent
把所有流程交给 LLM
再造第二套 Workflow
再造第二套 Production Queue
让 Coordinator 直接写业务 Authority
修改 WebCodex 6 槽位机制
```

---

# 46. 一句话架构原则

> **StoryOS 应在现有 Episode Runner 之上增加一个 deterministic、durable、resource-aware 的 Runtime Coordinator：它负责“谁运行、何时运行、还能运行几个、失败后去哪”，Episode Runner 负责“这一篇如何推进”，Workflow 负责“步骤如何流转”，Agent 负责“需要智能的判断”，Worker 负责“真正干活”；所有权威写入继续遵守 Single Writer。**

---

# 47. 参考架构来源

本方案吸收思想而不引入强依赖：

1. OpenAI Agents SDK — Agent Orchestration  
   https://openai.github.io/openai-agents-python/multi_agent/

2. OpenAI Agents SDK — Agents / Manager / Handoffs  
   https://openai.github.io/openai-agents-python/agents/

3. Microsoft Agent Framework — Workflows  
   https://learn.microsoft.com/en-us/agent-framework/journey/workflows

4. Microsoft Agent Framework — Workflow Concepts  
   https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/

5. Google Agent Development Kit — Workflow Agents / Graph Workflows  
   https://adk.dev/agents/workflow-agents/

6. LangGraph — Persistence / Checkpoints  
   https://docs.langchain.com/oss/python/langgraph/persistence

7. Temporal — Task Queues / Capacity-aware Workers  
   https://docs.temporal.io/task-queue

8. Land 本地项目  
   `D:\workspace\YeQianWorkSpace\dcits\SmartLiquidity\ground\land`

---

# 48. 实施优先级

最终优先级：

```text
P0
先完成当前 StoryOS 正式生产验收

P1（下一版本，暂不实现）
Track A：Runtime Coordinator Shadow
Track B：Retrieval Intelligence Shadow / Offline Evaluation

P2（下一版本）
Single Episode Durable Dispatch
Structured Knowledge + Knowledge Router + Hybrid Retrieval

P3（下一版本）
Multi Episode Resource-aware Scheduling
Reranker + Context Builder + Retrieval Evaluation

P4（后续）
Agent Orchestration Normalization / Query Planner 增强

P5（需要时再做）
跨节点 Worker / 分布式扩展
高级 Agentic RAG / Self-RAG / GraphRAG
```

不要因为本方案已经明确，就在当前验收前强行插入 P1-P5。**Track A 调度升级与 Track B Retrieval/RAG 升级当前都只做设计冻结，暂不进入实现。**

当前最正确的动作仍是：

```text
把现有 StoryOS 收口
→ 正式生产验收
→ Freeze Stable Baseline
→ 下一版本同时启动 Track A 调度升级 + Track B Retrieval Intelligence 升级
```
