# Story OS 多模式编排与子 Agent 改造最终实施 / 测试 / 验收方案 V1.1

> 日期：2026-09-26
> 状态：FINAL / GO FOR IMPLEMENTATION（P0 / P1 Shadow）
> 本文已合并 V1.1 二次架构评审结论，作为后续改造唯一执行与验收依据
> 适用范围：StoryOS Runtime / Workflow / Agent Runtime / PREIMAGE / Review / Release
> 核心原则：**复用现有 Runtime、AgentRuntime、PREIMAGE Candidate/Barrier/Commit，不新增第二套状态机、第二套通用 Agent Runtime、第二套 Authority Commit Engine。**

---

# 1. 修订结论

V1.1 吸收 V1.0 独立评审结论，做以下关键调整：

1. 不再把 Chain / Parallel / Router / Reflection / Hierarchical 放在同一个互斥 OrchestrationMode 中；
2. 改为四个独立维度：
   - execution_topology；
   - routing_policy；
   - review_policy；
   - control_policy；
3. Character Agent 拆成两个生命周期：
   - PREIMAGE 前 Character Authoring / Lock；
   - PREIMAGE 内 Character Finalize Adapter；
4. 不新增通用 `agent_registry.py` / `agent_execution_contract.py`，优先扩展现有 Platform Agent Runtime；
5. Authority Reducer 定义为 facade，不复制 `authority_commit.py`；
6. Episode Supervisor 降级为 Orchestration Facade，不成为第二调度器；
7. 性能基线改为**当前 HEAD 的现有并行 PREIMAGE**；
8. Router fallback 改为 capability-safe；
9. 三视图增加注册窗口与 late override invalidation；
10. Guardian 改为 Detection / Classification facade，复用已有 Recovery；
11. 新增正式 Shadow Phase；
12. Agent Execution 增加 idempotency / attempt / deadline / trace / shadow / resume；
13. 增加 duplicate dispatch / crash resume / idempotent commit 故障注入；
14. Context Capsule 优先复用并泛化现有 `preimage_task_contract.py`；
15. 不预先承诺“大 Episode Supervisor”，只有当 P0-P5 证明需要时才增加 facade。

因此 V1.1 的目标不是“新增一层 Agent 平台”，而是：

```text
把现有 StoryOS Runtime 能力
统一到同一个 Agent Execution Protocol 下
```

---

# 2. 当前可复用事实

当前仓库已经存在以下关键能力：

## 2.1 Runtime

- `runtime_dag.py`
- `runtime_scheduler.py`
- `runtime_resource_manager.py`
- `runtime_router.py`
- `runtime_checkpoint.py`
- `production_recovery.py` / `production_recovery_persistence.py`；
- `runtime_failure_classifier.py`；
- `runtime_failure_strategy.py`；
- `persistent_runner_daemon.py` / runner heartbeat；
- `next_action.py`

## 2.2 Agent Platform

- `platform/agent/runtime/agent_runtime.py`
- `platform/agent/runtime/contracts.py`
- `platform/agent/application/agent_service.py`
- Execution Recorder；
- Trace Observer；
- Skill Runtime Adapter；
- MCP Tool Adapter。

现有 `AgentRuntime` 的职责已经符合目标边界：

```text
execute an already-decided plan
NOT choose workflow step
NOT choose business state transition
```

因此本方案只扩展它的 Episode Production Adapter 能力，不重新建立 Runtime。

注意：`AgentApplicationService` 当前 Agent definition registry 是进程内临时数据，**P0/P1 不把它当生产级 Agent Registry 权威**。Character/World/Visual Adapter 使用静态代码注册或现有 Workflow/Node 配置构造 `AgentExecutionPlan`；只有未来确有跨进程动态 Agent 定义需求时，才单独设计持久化 Registry。

## 2.3 PREIMAGE

当前已经有：

```text
Task Contract
→ Authority Snapshot
→ Candidate
→ Verify
→ Scope Collision Check
→ Barrier
→ authority_commit
```

其中 `preimage_task_contract.py` 已具备：

- task_id；
- task_type；
- snapshot_id；
- required_read；
- authority_inputs；
- candidate_output；
- verifier；
- retry_policy；
- authority_scope；
- candidate_only target。

V1.1 将其作为 Agent Task / Input Capsule 的主要基础。

## 2.4 Authority

当前已有：

- `authority_commit.py`
- expected SHA；
- stale fail-closed；
- process lock；
- atomic replace；
- PREIMAGE barrier。

这些继续是唯一 Authority Commit 机制。

## 2.5 Character Three-View

当前已有：

- optional `references/characters/three-view.json`；
- character id 校验；
- front / side / back 声明；
- SHA；
- Character Visual Contract stale binding；
- Pixel Master supersedes three-view；
- 未提供时 `applicable=false`。

V1.1 只补生命周期和 invalidation 规则。

---

# 3. 多模式改为四维编排模型

不新增一个单一 `OrchestrationMode` enum。

## 3.1 execution_topology

映射现有 Runtime Scheduler。

允许值：

```text
serial
parallel_safe
delegated_managed
```

语义：

### serial

同一 Runtime wave 独占。

### parallel_safe

满足 dependency / scope / resource 后可并行。

### delegated_managed

Runtime DAG 只调起一个复合节点，内部并发由既有 Scheduler 管理。

例如：

```text
IMAGE_PRODUCTION
→ image_scheduler / batch_scheduler
```

兼容原则：

```text
现有 image_managed
→ 兼容映射 delegated_managed
```

第一阶段可以保留旧字段名，只加 projection，不立即迁移。

---

## 3.2 routing_policy

允许值：

```text
fixed
capability_route
```

### fixed

保持已有 executor。

### capability_route

由 deterministic Capability Router 从允许执行器中选择。

Router 不修改：

- DAG dependency；
- Node Authority；
- write scope；
- Gate。

---

## 3.3 review_policy

允许值：

```text
none
critic_once
bounded_reflection
```

### critic_once

一次 fresh reviewer。

### bounded_reflection

```text
Generate
→ deterministic validation
→ cheap/local triage
→ Critic
→ targeted repair <= 1
→ final critic
→ ACCEPT_CANDIDATE / NEEDS_USER / BLOCK
```

默认：

```yaml
max_review_attempts: 2
max_auto_repairs: 1
technical_retry_consumes_review_budget: false
```

---

## 3.4 control_policy

允许值：

```text
direct
supervised
```

### direct

已有 Runtime Node 直接交 executor。

### supervised

由 Stage Adapter：

- 拆 Candidate Task；
- 构造 Agent Plan；
- 收集结果；
- 调用既有 verifier / barrier / commit。

Supervisor 不是第二调度器。

---

# 4. 唯一调度权边界

必须固定三层 owner：

## 4.1 Global Runtime Coordinator

职责：

```text
选择哪个 Episode 可获得运行资源
```

不决定 Episode 内节点。

## 4.2 Runtime DAG + Runtime Scheduler

职责：

```text
选择某 Episode 哪些 Node runnable
```

它仍是 Episode 内唯一 DAG / dependency / resource wave 决策源。

## 4.3 Stage / Agent Adapter

职责：

```text
把一个已被 Runtime Scheduler 选中的 Node
转换成 AgentExecutionPlan / Candidate execution
```

不再做全局 dependency scheduling。

因此不允许：

```text
Runtime Scheduler
+
Episode Supervisor
+
Stage Supervisor
```

三者各自拥有 runnable set。

---

# 5. Agent 生命周期与边界

第一批不直接创建 5 个通用 Agent Service。

先从 Adapter 化开始。

---

# 6. Character 生命周期拆分

这是 V1.1 最重要修订。

## 6.1 Character Authoring / Lock

发生在 PREIMAGE 前。

流程：

```text
Character Seed
    ↓
Three-View optional
    ↓
Character Contract Candidate
    ↓
Character Visual Contract Candidate
    ↓
Validate
    ↓
Lock
```

这里可以使用 Character Authoring Agent，但它最终不能直接 PASS Gate。

输出：

- Character Contract；
- Character Visual Contract；
- Three-View Manifest；
- Character Lock Evidence。

---

## 6.2 PREIMAGE Character Finalize Adapter

PREIMAGE 内的 `CHARACTER_FINALIZE` 只允许读取冻结输入：

```text
meta/character-contract.json
meta/character-visual-contract.json
three-view summary if applicable
story-gates
authority snapshot
```

输出 Scope 仍严格是：

```text
character.finalize
```

它不能：

- 改 Character Contract；
- 改 Character Visual Contract；
- 修改 Three-View；
- 扩大 authority_scope。

正式命名建议：

```text
CharacterFinalizeAgentAdapter
```

而不是笼统的 Character Agent 全权接管。

---

# 7. Three-View 生命周期

## 7.1 正常注册窗口

推荐：

```text
Character Authoring
→ before Character Visual LOCK
```

此时注册或修改三视图属于正常前期输入。

---

## 7.2 Late Override

若在 Character Visual 已 LOCK、Storyboard 已 LOCK 或更后阶段，用户显式替换三视图：

```text
Direct User Authority Change
→ Character Visual STALE
→ PREIMAGE Snapshot STALE
→ Frame Contract STALE
→ Visual candidates authority refresh required
```

必须：

- 留 direct-user evidence；
- 不静默替换；
- 不自动复用旧 Pixel Master；
- 不自动 PASS。

---

## 7.3 Pixel Master takeover

顺序：

```text
Character Crop
> Pixel Master
> Three-View
> Series Identity
> Text Contract
```

一旦当前 Episode Pixel Master 合法：

- three-view 不再作为 primary identity reference；
- three-view 仍保留为上游 evidence；
- Pixel Master stale 后可重新回退 three-view，但必须经过现有 authority refresh 规则。

### 7.4 STALE 语义不新增 Episode State

这里的 `Character Visual STALE / PREIMAGE STALE / Frame Contract STALE` 是**派生有效性判断**，不是新增 Episode Stage，也不允许把 `episode-state` 回滚到一个新的 `STALE` 状态。

实际实现应复用现有 SHA / snapshot / contract verify：

```text
three-view SHA changed
→ character-visual verify fails / requires rebuild
→ old PREIMAGE snapshot mismatch
→ old Frame Contract SHA mismatch
→ downstream candidate cannot commit / reuse
```

只有已有 Runtime 的合法 transition 可以改变 Episode State。

---

# 8. Agent Execution Contract：扩展现有 Platform Contract

不新增第二套通用 Agent Runtime。

V1.1 建议扩展 `platform.agent.runtime.contracts.AgentExecutionPlan` 或增加 Episode Adapter Envelope。

最低字段：

```json
{
  "execution_id": "ae_xxx",
  "task_id": "task_xxx",
  "agent_code": "character_finalize",
  "agent_version": "1",
  "execution_type": "episode_candidate",
  "idempotency_key": "episode/task/snapshot/attempt",
  "attempt": 1,
  "authority_snapshot": {
    "snapshot_id": "...",
    "authority_sha256": {}
  },
  "capability_requirements": [
    "reasoning",
    "filesystem"
  ],
  "routing_decision": {
    "executor": "WORK",
    "provider": "webcodex",
    "reason": "..."
  },
  "input_contract": {},
  "candidate_output": "meta/runtime/...",
  "candidate_schema_version": 1,
  "authority_scope": [
    "character.finalize"
  ],
  "allowed_reads": [],
  "allowed_writes": [
    "candidate_output"
  ],
  "forbidden_writes": [
    "episode_state",
    "story_gates",
    "production_ledger"
  ],
  "deadline_at": null,
  "shadow": false,
  "parent_execution_id": null,
  "trace_id": null,
  "resume_from": null,
  "budget": {
    "max_rounds": 1,
    "max_tokens": null,
    "timeout_seconds": 900
  }
}
```

规则：

- `max_tokens=null` 表示未显式限制；
- 不使用 `0` 表示无限；
- idempotency_key 必须稳定；
- attempt 必须单调；
- shadow execution 不允许 canonical commit。

### 8.1 Execution Eligibility 与 Commit Receipt

当前 `authority_commit.py` 已能保证 expected SHA、snapshot、lock 与 atomic write，但**尚未原生提供 idempotency_key / attempt / execution_id 的 durable commit receipt**。因此 P0 必须先补一个最小的执行资格/收据层，P1 Production 切换之前必须完成。

要求：

```text
execution eligibility:
  task_id
  snapshot_id
  execution_id
  attempt
  idempotency_key
  status

commit receipt:
  idempotency_key
  execution_id
  attempt
  input_sha
  output_sha
  committed_at
```

实现原则：

- 不创建第二套 Authority 内容存储；
- receipt 属于 Runtime execution evidence；
- 可以扩展现有 PREIMAGE task-state / execution persistence 与 `authority_commit` precondition；
- 同一 `idempotency_key` 已成功 commit 时，再次收到同一 commit 请求必须返回 `REPLAYED/PASS`（或等价成功语义），不得再次 mutation；
- superseded execution / attempt 必须 fail-closed；
- commit receipt 必须走现有 Storage Policy，在 MySQL 模式不得假定本地 JSON 是 canonical。

---

# 9. Candidate-only 权限

继续沿用：

```text
Agent Runtime
→ Candidate
→ Verify
→ Barrier
→ Commit
```

Agent 仅允许写：

```text
candidate_output
trace
execution record
shadow comparison
```

其中 `execution record / commit receipt / shadow comparison` 均属于 Runtime Evidence，不得成为第二套业务 Authority。

Agent 禁止写：

```text
episode-state
story-gates PASS
production ledger state
runtime checkpoint canonical stage
other agent candidate
canonical shared authority
```

---

# 10. Reducer 定义为 facade

V1.1 不新增第二套 Authority Engine。

所谓 Reducer 只负责：

```text
collect
→ verify
→ conflict check
→ call existing authority_commit
```

推荐落点：

```text
preimage_reducer.py
```

或直接扩展：

```text
preimage_protocol.py
```

它必须调用现有：

- `authority_commit.py`
- expected SHA；
- lock；
- atomic replace。

不允许重复实现这些机制。

---

# 11. Context Capsule 复用 PREIMAGE Task Contract

不创建完全独立的 Input Capsule Schema。

优先泛化：

```text
preimage_task_contract.task_contract()
```

增加可选字段：

```text
capability_requirements
routing_policy
review_policy
control_policy
idempotency_key
attempt
deadline
shadow
trace
```

其它 Episode Agent Adapter 使用相同 Envelope。

目标：

- 一个 Task Contract；
- 多种 executor；
- Candidate schema 各自专业化。

---

# 12. Character Agent Adapter

## 12.1 输入

从现有 `CHARACTER_FINALIZE` task_contract 获取。

额外允许：

- three-view summary；
- Character Visual projection；
- runtime capability metadata。

## 12.2 输出

保持现有 Candidate schema：

```text
character.finalize
```

## 12.3 实施目标

第一阶段不是“更智能”，而是证明：

- AgentRuntime 能安全执行现有 PREIMAGE Candidate；
- 不破坏 authority；
- 上下文可以更小；
- routing / trace / performance 可统一。

---

# 13. World / Visual Adapter

只有 Character Adapter Shadow 验证通过后再做。

## 13.1 World

包装：

```text
WORLD_PREPARE
```

保持 scope：

- visual.world_identity；
- visual.world_state；
- visual.temporal_continuity；
- visual.wardrobe。

## 13.2 Visual Director

包装：

```text
VISUAL_NARRATIVE_PREPARE
```

保持 scope：

- visual.narrative_core；
- visual.shot_progression；
- visual.capture_grammar。

不新增新的 canonical documents。

---

# 14. Critic Protocol

Critic Agent 只负责 Review Candidate。

Critic 输出中的通过语义建议使用 `ACCEPT_CANDIDATE`，避免与 StoryOS Gate 的 `PASS` 混淆。即使兼容旧字段仍叫 `PASS`，也必须在 schema 中明确：**review decision ≠ Gate PASS，不能直接推进 Episode State。**

## 14.1 Fresh Isolation

Critic：

- 不继承创作 Agent scratch；
- 只读取 Authority + candidate；
- 不读取创作者隐藏决策；
- 不写创作 source。

## 14.2 输出

统一：

```json
{
  "decision": "ACCEPT_CANDIDATE|REPAIR|NEEDS_USER|BLOCK",
  "issue_codes": [],
  "severity": "LOW|MEDIUM|HIGH",
  "repair_scope": [],
  "evidence": []
}
```

## 14.3 Reflection budget

```text
review attempt <= 2
auto targeted repair <= 1
technical retry independent
```

---

# 15. Capability Router V2

优先扩展现有 `runtime_router.py`，不创建另一套总 Runtime Router。

可以新增：

```text
task_capability_router.py
```

但它只做 Task-level selection。

Capability source 必须区分：

```text
static declaration
  executor 能做什么

dynamic health probe
  executor 现在是否可用
```

动态健康结果必须有采样时间 / TTL；过期健康状态不能被当成当前可用性。Router decision evidence 至少记录 capability snapshot 与 probe timestamp。

---

## 15.1 Capability Matching

任务声明：

```text
required
optional
forbidden
```

示例：

```json
{
  "required": [
    "reasoning",
    "filesystem"
  ],
  "optional": [
    "host_workspace"
  ],
  "forbidden": [
    "canonical_state_write"
  ]
}
```

---

## 15.2 Executor Capabilities

示例：

```text
WORK + WebCodex
  reasoning
  filesystem
  workspace_edit
  host_workspace
  review_isolation

CODEX
  reasoning
  filesystem
  local_process

Local deterministic
  filesystem
  mysql
  local_visual
```

---

## 15.3 Fallback Rules

不是：

```text
WebCodex unavailable
→ Codex
```

而是：

```text
WebCodex unavailable
AND
Codex satisfies every REQUIRED capability
AND
Codex is allowed by task policy
→ CODEX fallback
```

否则：

```text
NOT_ROUTABLE / HOST_WAIT
```

必须有测试：

```text
WebCodex off
Codex on
task requires host_workspace
→ Codex rejected
```

---

# 16. Runtime Guardian V2

第一版只做 detection / classification facade。

## 16.1 检测

- heartbeat stale；
- running job timeout；
- queue stuck；
- network error；
- MySQL transient error；
- invalid transition；
- stale authority；
- retry budget；
- lease age；
- host request age。

## 16.2 动作

优先调用现有：

- `production_recovery.py` / recovery persistence；
- `runtime_failure_classifier.py`；
- `runtime_failure_strategy.py`；
- persistent runner heartbeat / owner lock；
- image `retry-tech`；
- scheduler；
- checkpoint。

Guardian 自己不实现新的 retry/state repair engine。

## 16.3 Diagnostic Agent

只有：

```text
deterministic classifier = UNKNOWN
```

才启动 Diagnostic Agent。

Guardian 常驻 LLM 调用必须为 0。

---

# 17. Shadow Mode

这是 V1.1 新增正式阶段。

## 17.1 原理

```text
Current Production Producer
→ writes canonical authority

New Agent Adapter
→ shadow candidate only

Comparator
→ compare
```

Shadow 不能：

- canonical commit；
- gate pass；
- episode transition。

---

## 17.2 Shadow Comparison

至少比较：

- schema validity；
- semantic equivalence；
- required field coverage；
- issue count；
- wall time；
- model time；
- token usage；
- repeated authority reads；
- failure rate；
- timeout rate。

Shadow evidence 不固定为 Episode 本地 JSON。逻辑分类为 `runtime evidence / shadow comparison`，由现有 Storage Policy / Runtime Workspace / MySQL persistence 决定物理落点。

允许在 JSON-mode 测试夹具中使用类似：

```text
meta/runtime/agent-shadow/
```

但在 MySQL 模式不得把该文件路径当 canonical authority。

---

# 18. Durable / Idempotency

多 Agent 改造必须把重复 dispatch 当核心故障。

## 18.1 idempotency key

建议：

```text
episode_id
+ node_id
+ snapshot_id
+ task_type
+ attempt
+ shadow
```

## 18.2 commit rule

只有：

```text
expected snapshot
+ expected attempt
+ allowed execution
```

可以 commit。

---

# 19. Duplicate Dispatch 故障注入

## D1：Candidate 后 crash

```text
Agent returns Candidate
→ process crash before final status
→ resume
→ same idempotency key
→ no duplicated canonical commit
```

## D2：同 task 双 dispatch

```text
task dispatched twice
→ candidate A
→ candidate B
→ only expected execution can commit
```

## D3：commit response lost

```text
commit success
→ response lost
→ reducer retry
→ idempotent success
→ no duplicate mutation
```

## D4：superseded attempt

```text
attempt 1 slow
attempt 2 completes
attempt 1 late return
→ attempt 1 rejected
```

---

# 20. Dynamic Agent Activation

Agent 不按数量启动，而按收益和需求启动。

## 20.1 简单 Episode

最多必要 Adapter。

不强制：

- World；
- Visual；
- Critic Agent 全部激活。

## 20.2 启动条件

```text
DAG Node selected
AND
agent adapter enabled
AND
capability matched
AND
authority snapshot frozen
AND
resource available
→ agent execution
```

否则：

```text
legacy producer
或
wait / blocked
```

---

# 21. Performance Baseline

V1.1 修正基线：

```text
Baseline = 当前 HEAD 已实现的 PREIMAGE parallel path
Candidate = Agent Adapter / Agent Protocol path
```

不再用 serial baseline 证明 Agent 提速。

### 21.1 Baseline Capture 方法

P0 结束、任何 Agent Adapter 改生产路径之前，冻结当前 HEAD baseline：

- 固定同一 Episode / fixture 集；
- 固定模型、reasoning effort、Runtime、Provider；
- 每个场景至少 5 次有效运行，取 median，并记录 p90/p95（样本不足时只记录 median/min/max，不伪报 p95）；
- technical retry 单独统计，不从原始事实中删除；
- 外部 provider 波动场景采用 paired shadow run；
- 比较 wall / model / wait / token / repeated reads / failure；
- baseline 写入现有 Performance Ledger / benchmark evidence。

---

# 22. P1 性能验收

Character Agent Adapter / Shadow：

| 指标 | 门槛 |
|---|---:|
| Authority correctness | 100% |
| stale canonical commit | 0 |
| duplicate canonical commit | 0 |
| wall time regression | ≤ 5% |
| token regression | ≤ 10% |
| 无三视图额外模型调用 | 0 |
| 三视图不存在时额外 wall overhead | < 3% |

P1 的目标首先是**零安全回退**。

---

# 23. P2 性能目标

当 World / Visual Adapter 也接入后：

| 指标 | 目标 |
|---|---:|
| PREIMAGE wall time vs current HEAD | ≥ 10% 改善，或 |
| token / repeated-read | ≥ 20% 降低 |
| parallel utilization | 不低于 current HEAD |
| candidate contract reject rate | < 5% |
| review retry rate | 不高于 baseline |

满足“速度改善”或“token/读取明显下降”至少一个即可证明架构收益。

---

# 24. Agent 收益判定

每个 Agent Adapter 必须回答：

```text
它到底改善了什么？
```

四类至少一项有实测收益：

- Speed；
- Token / Cost；
- Quality；
- Recovery。

如果四项都没有收益，则该 Agent Adapter 不进入 production。

---

# 24.1 P0 必须先解决的幂等提交缺口

在进入 Character Adapter production 之前，必须先证明：

- authority commit 可识别同一 idempotency key 的成功重放；
- attempt 2 成功后，attempt 1 晚到不能 commit；
- commit 已成功但响应丢失时，重试不会产生第二次 mutation；
- MySQL / JSON 模式具有相同逻辑语义。

这属于 P0 的 Blocking Acceptance，不允许推迟到最终 E2E。

---

# 25. 实施阶段

## P0：抽象对齐

不改变 Production 行为。

实施：

1. 盘点 Platform Agent Runtime；
2. 扩展现有 AgentExecutionPlan / Episode Adapter Envelope；
3. execution_topology / routing_policy / review_policy / control_policy；
4. idempotency / execution eligibility / durable commit receipt；
5. attempt / supersede；
6. shadow；
7. deadline；
8. trace；
9. resume；
10. capability requirements；
11. 冻结 current-HEAD Performance Ledger baseline。

验收：

- current production path zero behavior change；
- all new fields backward-compatible；
- Runtime Scheduler 仍是唯一 Episode node scheduler。
- duplicate-dispatch / lost-response commit replay tests green；
- AgentApplicationService 临时 registry 不成为生产权威依赖；
- baseline evidence 已冻结。

---

## P1：Character Finalize Agent Adapter

只包装：

```text
PREIMAGE_CHARACTER_FINALIZE
```

不改变其它 PREIMAGE producer。

验收：

- 同样 task contract；
- 同样 authority scope；
- 同样 verifier；
- 同样 barrier；
- 同样 authority_commit；
- 无 three-view 旧路径无额外调用；
- three-view 为 frozen input。

---

## P1.5：Character Shadow

Current producer 与 Agent Adapter 同跑。

Agent 只写 shadow candidate。

至少在多个 fixture + 一个真实 Episode 上比较。

进入 production 的条件：

- schema 100%；
- semantic equivalence 达标；
- wall/token 无不可接受退化；
- zero authority side effect。

---

## P2：World / Visual Adapter

按一个一个 Adapter 接入：

1. WORLD_PREPARE；
2. VISUAL_NARRATIVE_PREPARE；
3. ENVIRONMENT_PREPARE 是否 Agent 化根据收益决定。

每个都先 shadow。

---

## P3：Critic + Bounded Reflection

先统一输出协议。

不先统一所有 Review 实现。

按：

1. Story Semantic；
2. PREIMAGE semantic；
3. Final Semantic；

逐步接入。

---

## P4：Task Capability Router

扩展现有 Runtime Router。

先 shadow route：

```text
legacy selected executor
vs
capability router suggested executor
```

一致性稳定后再启用实际 route。

---

## P5：Guardian Facade

先 detection / classification。

动作继续复用现有 Recovery。

---

## P6：Episode Orchestration Facade（可选）

只有满足任一：

- 调用链明显重复；
- adapter dispatch 逻辑散落；
- resume 重建逻辑重复；
- observability 缺统一入口；

才增加 facade。

它不能拥有新状态或新 scheduler。

---

# 26. 测试矩阵

## 26.1 Contract

- backward compatible；
- invalid capability rejected；
- invalid write scope rejected；
- missing snapshot rejected；
- invalid idempotency rejected；
- superseded attempt rejected；
- shadow commit rejected。

## 26.2 Character

- no three-view；
- valid three-view；
- bad SHA；
- wrong character id；
- late override；
- stale chain；
- Pixel Master takeover；
- Pixel Master stale fallback；
- multi-character reference。

## 26.3 Agent Runtime

- plan executes；
- tool permission；
- candidate-only write；
- timeout；
- crash；
- resume；
- duplicate dispatch；
- trace；
- shadow。

## 26.4 Router

- exact capability；
- optional capability；
- missing required capability；
- explicit runtime override；
- WebCodex lost + Codex sufficient；
- WebCodex lost + Codex insufficient；
- no executor；
- no permission escalation。

## 26.5 Reflection

- critic once；
- one repair；
- second fail → NEEDS_USER；
- technical retry independent；
- issue_codes；
- no infinite loop。

## 26.6 Guardian

- network；
- MySQL；
- stale job；
- stale lease；
- invalid transition；
- exhausted technical retry；
- content failure must not retry-tech；
- force-pass forbidden。

---

# 27. Integration Tests

## I1 Existing PREIMAGE Baseline

先冻结当前 HEAD 指标：

- wall；
- resource；
- token；
- reads；
- peak concurrency；
- success rate。

这是后续唯一正式对照。

## I2 Character Adapter Shadow

```text
same input snapshot
→ legacy character finalize
→ agent shadow finalize
→ compare
```

## I3 Character Production

仅在 shadow 通过后：

```text
agent candidate
→ existing verifier
→ existing barrier
→ existing authority_commit
```

## I4 Three-View

```text
register before lock
→ contract bind SHA
→ character finalize
→ frame contract
→ visual baseline
→ Pixel Master takeover
```

## I5 Late Three-View Override

```text
locked episode
→ direct user replace three-view
→ stale chain
→ old visual candidate cannot silently remain authoritative
```

## I6 Router

Capability-safe fallback。

## I7 Duplicate Dispatch

执行 D1-D4。

## I8 Guardian

Injected technical failure。

---

# 28. E2E 分阶段验收

## Phase E2E-A

范围：

```text
Story Lock
→ PREIMAGE
→ Frame Contract
```

无三视图。

目的：

- backward compatibility。

## Phase E2E-B

同范围 + three-view。

目的：

- Character Adapter；
- identity anchor；
- stale；
- Pixel Master 前置关系验证。

## Phase E2E-C

```text
Story
→ Visual Lock
```

加入：

- World；
- Visual；
- Critic。

## Final E2E

至少一个**全新 Episode**：

```text
IDEA
→ PUBLISH_READY
```

并包含：

- Agent Adapter；
- fallback；
- one injected technical recovery；
- complete Performance Ledger；
- complete runtime evidence。

---

# 29. Observability

优先扩展现有 Trace。

新增字段：

```text
execution_topology
routing_policy
review_policy
control_policy
agent_adapter
agent_execution_id
idempotency_key
attempt
shadow
authority_snapshot_id
candidate_id
router_reason
executor
capability_match
fallback_active
review_attempt
repair_attempt
guardian_classification
```

不新建第二套 Trace Store。

---

# 30. Feature Flags

建议：

```yaml
agent_runtime:
  protocol_v2_enabled: false

  adapters:
    character_finalize: false
    world_prepare: false
    visual_narrative_prepare: false

  shadow:
    enabled: false

  task_capability_router:
    enabled: false

  bounded_reflection:
    enabled: false

  guardian_facade:
    enabled: false
```

不增加：

```text
specialized_agents_enabled
multi_mode_enabled
```

这种过大的总开关作为唯一控制。

必须能逐 Adapter 回滚。

---

# 31. 推荐代码落点

## 优先修改 / 扩展

```text
platform/agent/runtime/contracts.py
platform/agent/runtime/agent_runtime.py
episodes/_system/preimage_task_contract.py
episodes/_system/preimage_protocol.py
episodes/_system/runtime_scheduler.py
episodes/_system/runtime_router.py
episodes/_system/runtime_observability.py
```

## 可新增薄层

```text
episodes/_system/agents/character_finalize_adapter.py
episodes/_system/agents/world_prepare_adapter.py
episodes/_system/agents/visual_narrative_adapter.py
episodes/_system/task_capability_router.py
episodes/_system/reflection_policy.py
episodes/_system/runtime_guardian_facade.py
episodes/_system/agent_shadow_compare.py
```

## 不建议新增

```text
episodes/_system/agent_runtime.py
episodes/_system/agent_registry.py
episodes/_system/authority_commit_engine.py
episodes/_system/episode_scheduler_v2.py
```

---

# 32. Authority 验收

必须始终成立：

- Agent writes Candidate only；
- Snapshot-bound；
- Scope-bound；
- Attempt-bound；
- Idempotency-bound；
- Barrier；
- Existing authority_commit；
- Atomic；
- Single Writer；
- stale fail-closed；
- superseded attempt fail-closed；
- shadow no commit。

任何一项失败：

```text
NO-GO
```

---

# 33. 性能验收

## P1

目标：

```text
安全等价
```

不是强求提速。

## P2+

必须在以下至少一项有收益：

- wall time；
- token；
- repeated read；
- quality；
- recovery。

且其它指标无明显回退。

---

# 34. 质量验收

- Story Semantic 不下降；
- Character identity 不下降；
- three-view Episode identity drift 应下降；
- false PASS 不增加；
- force-pass 不增加；
- review retries 不增加；
- no-three-view 路径质量等价。

---

# 35. Go / No-Go

## P0 GO

- 协议 backward-compatible；
- 无 production behavior change；
- 无第二套 Runtime / State / Commit。

## P1 GO

- Character Adapter Shadow 通过；
- Authority correctness 100%；
- wall regression <= 5%；
- token regression <= 10%。

## P2 GO

- World / Visual 各自 Shadow 通过；
- 至少 speed/token/quality/recovery 一项有实测收益。

## Final GO

- full E2E；
- Performance Ledger；
- duplicate dispatch tests；
- capability fallback；
- Guardian recovery；
- zero authority regression。

---

# 36. 最终架构

```text
Global Runtime Coordinator
        │
Runtime DAG + Scheduler
        │
selected Node
        │
Stage / Agent Adapter
        │
Platform AgentRuntime
        │
Candidate
        │
Existing Verifier
        │
Barrier
        │
Existing authority_commit
        │
Canonical Authority
```

跨切面：

```text
Capability Router
Reflection Policy
Guardian Facade
Observability
Performance Ledger
```

---

# 37. 核心原则

StoryOS 不需要重新“Agent 化”。

StoryOS 需要的是：

> **把已有成熟的 DAG、Candidate、Barrier、Single Writer、Agent Runtime、Recovery、Router 统一成一个严格的 Agent Execution Protocol。**

第一批真正值得实施的只有：

1. Platform Agent Contract 扩展；
2. Character Finalize Adapter；
3. Shadow Compare；
4. capability-safe routing metadata；
5. idempotency / duplicate dispatch；
6. Performance Ledger 对照。

等这批证明收益后，再增加 World / Visual / Critic Adapter。

**任何新 Agent，如果不能证明速度、成本、质量或恢复性至少一项改善，就不进入 Production。**

---

# 38. 二次评审结论与强制实施门槛（已合并）

本节合并原 V1.1 二次评审中所有对实施具有约束力的结论。后续不再单独维护评审文档。

## 38.1 最终 Verdict

```text
方案方向：GO
P0 协议 / 幂等 / 基线实施：GO
P1 Character Adapter Shadow：GO
P1 Production Cutover：CONDITIONAL GO
P2+ World / Visual / Critic：按 P1 实测收益逐项 GO
```

当前没有需要重写总体方案的架构级 Blocking Issue。

Production Cutover 仍有一个不可绕过的硬门槛：

> **Durable Execution Eligibility + Idempotent Commit Receipt**

因此：

- 可以立即开始 P0；
- 可以在 P0 期间开发 Character Adapter skeleton 与 Shadow Compare；
- 可以在 P0 通过后运行 Character Adapter Shadow；
- **不能在 P0 Commit Gate 通过前，让 Agent Candidate 替换现有 Production producer。**

## 38.2 已解决的结构性问题

| 问题 | 最终处理 |
|---|---|
| Chain / Parallel / Router / Reflection / Hierarchical 混成单一模式 | 拆成 `execution_topology / routing_policy / review_policy / control_policy` |
| Character Agent 修改 PREIMAGE frozen input | 拆成 Character Authoring/Lock 与 PREIMAGE CharacterFinalizeAgentAdapter |
| 新建第二套 Agent Runtime / Registry | 复用 `platform/agent/runtime`；临时 Registry 不作为 Production Authority |
| Reducer 变成第二套 Commit Engine | Reducer 只做 collect/verify facade，最终调用现有 `authority_commit.py` |
| Episode Supervisor 与 Scheduler 重叠 | Runtime DAG + Scheduler 仍是唯一 Episode 内 runnable owner |
| 性能基线错误使用串行路径 | 基线固定为当前 HEAD 的并行 PREIMAGE |
| WebCodex → Codex 无条件 fallback | 改为 required capability 全满足才允许 fallback |
| Three-View late override 生命周期不清 | 使用 SHA / snapshot / contract invalidation，STALE 不新增 Episode State |
| Guardian 重复造 Recovery | Guardian 只做 detection/classification，动作复用现有 recovery |
| 缺 Shadow | 正式增加 P1.5 Shadow |
| AgentExecutionContract 字段不足 | 增加 idempotency / attempt / capability / trace / shadow / resume 等 |
| Duplicate Dispatch 未覆盖 | 增加 D1-D4 故障注入和 Commit Receipt Gate |

## 38.3 P0 强制 Gate：Execution Eligibility + Commit Receipt

现有 `authority_commit.py` 已经提供：

- expected SHA；
- snapshot；
- process lock；
- atomic write；
- append-only commit evidence。

但当前还不能天然保证：

```text
commit succeeded
→ response lost
→ same request replay
→ idempotent success
→ zero second mutation
```

P0 必须补齐最小的执行资格与提交收据能力，且不得形成第二套 Authority Store。

必须证明：

### A. Replay

```text
same idempotency_key
+ previous commit success
→ REPLAYED / equivalent success
→ zero second mutation
```

### B. Attempt Supersede

```text
attempt 2 active / committed
attempt 1 late return
→ attempt 1 rejected
```

### C. Execution Eligibility

```text
execution_id not eligible
→ commit fail-closed
```

### D. Storage Parity

MySQL authority mode 与 JSON compatibility / test mode 必须保持相同逻辑语义。

在 A-D 全部通过前：

> **Character Adapter 只能 Shadow，不能成为 canonical producer。**

## 38.4 Platform Agent Contract 的实施约束

P0 应优先评估两种 backward-compatible 方案：

### Option A：扩展现有 AgentExecutionPlan 的 optional fields

前提：

- API serialization 无破坏；
- Execution Recorder 无破坏；
- Trace 无破坏；
- 已有 Agent caller 无需同步迁移。

### Option B：Episode Adapter Envelope

```text
EpisodeAgentExecutionEnvelope
        contains
AgentExecutionPlan
```

如果直接改 Platform Contract 会扩大兼容风险，优先采用 Envelope。

无论哪种方案，都禁止再新增第二套通用 Agent Runtime。

## 38.5 Shadow Comparator 成本约束

Shadow 比较顺序必须优先 deterministic：

```text
schema
→ required field coverage
→ normalized structural diff
→ domain-specific validators
→ sampled semantic critic only when necessary
```

不允许默认再启动一个昂贵 LLM 来比较每一份 Shadow Candidate，否则会污染 wall/token benchmark。

## 38.6 Capability Router 健康时效

Task Capability Router 必须区分：

```text
declared capability
available now
healthy enough for this task
```

动态 probe 必须记录：

- sampled_at；
- TTL；
- health result；
- capability snapshot。

不能因为检测到 `codex.exe` 就推断它拥有 host workspace、review isolation、image generation、connector 等未声明 capability。

## 38.7 Three-View 最终约束

正常注册窗口：

```text
Character Authoring
→ before Character Visual LOCK
```

Late override：

```text
Direct User Authority Change
→ character visual verification stale
→ PREIMAGE snapshot stale
→ Frame Contract stale
→ downstream candidate non-reusable
```

这里的 STALE 是派生有效性，不是新的 Episode State。

## 38.8 Runtime Guardian 最终边界

Guardian 第一版只负责：

```text
detect
→ classify
→ call existing recovery action
```

复用：

- `production_recovery.py` / persistence；
- `runtime_failure_classifier.py`；
- `runtime_failure_strategy.py`；
- persistent runner heartbeat / owner lock；
- image retry-tech；
- scheduler；
- checkpoint。

Guardian 常驻 LLM 调用必须为：

```text
0
```

只有 deterministic classifier 无法分类时，才允许按需启动 Diagnostic Agent。

---

# 39. 最终实施顺序（唯一顺序）

后续改造统一按以下顺序执行。

## P0-A：Baseline / Contract Freeze

- 冻结 current HEAD benchmark；
- Platform Agent Contract compatibility assessment；
- orchestration metadata projection；
- no production behavior change。

必须产出 current HEAD PREIMAGE Performance Ledger baseline。

## P0-B：Execution Identity

- idempotency_key；
- execution_id；
- attempt；
- supersede；
- resume；
- trace；
- eligibility state。

## P0-C：Commit Receipt

- durable commit receipt；
- commit eligibility precondition；
- replay；
- D1-D4；
- MySQL / JSON logical parity。

只有 P0-A/B/C 全部通过，才允许进入 Production Adapter Cutover。

## P1：Character Finalize Adapter

只包装：

```text
PREIMAGE CHARACTER_FINALIZE
```

保持原 task contract、authority scope、verifier、barrier 和 `authority_commit`。

## P1.5：Character Shadow

```text
legacy producer = canonical
agent adapter = shadow candidate
```

比较：

- schema；
- semantic equivalence；
- wall；
- token；
- repeated read；
- failure；
- timeout。

## P1 Production

必须同时满足：

```text
P0 Commit Gate
+ Character Shadow
+ Performance Baseline
+ Authority Zero Regression
```

才允许切正式 producer。

## P2

World / Visual 逐个 Adapter 接入，**每个都必须先 Shadow**。

## P3+

Critic / Task Capability Router / Guardian 按收益逐项推进。

---

# 40. 最终 Go / No-Go

## GO：现在允许开始

- P0-A；
- P0-B；
- P0-C；
- Character Adapter skeleton；
- Shadow comparison framework；
- 对应测试。

## CONDITIONAL GO

以下动作必须等待 P0 Gate：

- Character Agent 替换现有 Production producer；
- Agent Candidate 成为 canonical PREIMAGE 输入；
- duplicate-dispatch runtime 正式启用。

## 暂不实施

- 新 Agent Registry Service；
- 新 Authority Commit Engine；
- 新 Episode Scheduler；
- 大 Episode Supervisor；
- World / Visual / Critic 一次全部上线。

---

# 41. 最终执行口径

本文件是后续改造的**唯一施工图 + 测试方案 + 验收标准 + 评审约束**。

以后执行时不再在“实施方案”和“评审文档”之间来回选择。

冲突处理原则：

```text
Authority / Safety Gate
> Phase Acceptance
> Implementation Detail
> Performance Optimization
```

即：

- Authority 安全优先于提速；
- P0 Gate 优先于 P1 Production；
- Shadow 证明收益优先于继续增加 Agent；
- 不允许为了 Agent 化而重造现有成熟 Runtime。

最终执行结论：

# **GO FOR IMPLEMENTATION**

但 GO 的范围严格定义为：

> **立即进入 P0；P0 通过后进入 Character Adapter Shadow；Production Cutover 必须通过 Commit Receipt + Attempt Supersede + D1-D4 + Shadow + Performance Baseline + Authority Zero Regression。**
