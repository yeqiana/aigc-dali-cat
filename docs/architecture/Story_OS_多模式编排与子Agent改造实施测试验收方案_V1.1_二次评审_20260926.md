# Story OS 多模式编排与子 Agent 改造实施 / 测试 / 验收方案 V1.1 — 二次架构评审

> 日期：2026-09-26
> 评审对象：`Story_OS_多模式编排与子Agent改造实施测试验收方案_V1.1_20260926.md`
> 评审方式：独立二次评审 / 对照当前 Runtime Scheduler、Platform AgentRuntime、PREIMAGE Task Contract、Authority Commit、Runtime Router、Production Recovery
> 最终结论：**GO FOR P0 / P1 SHADOW；PRODUCTION CUTOVER 受 P0 Acceptance Gate 约束**

---

# 1. 总体结论

V1.1 已经解决 V1.0 的主要结构性问题。

与 V1.0 相比，V1.1 已从：

```text
“计划新增一套多 Agent 编排层”
```

收敛为：

```text
“在现有 Runtime / AgentRuntime / PREIMAGE / Commit 之上
建立统一 Agent Execution Protocol 与薄 Adapter”
```

这与当前 StoryOS 的成熟度更匹配。

二次评审结论：

```text
方案方向：GO
P0 协议/幂等/基线实施：GO
P1 Character Adapter Shadow：GO
P1 Production Cutover：CONDITIONAL GO
P2+ World / Visual / Critic：必须依据 P1 实测收益逐项 GO
```

当前**没有需要重写总体方案的架构级 Blocking Issue**。

仍有一个必须在 P1 Production Cutover 前完成的实现级 Gate：

> **durable execution eligibility + idempotent commit receipt**

V1.1 已经把它明确提升为 P0 Blocking Acceptance，因此它不再是“方案遗漏”，而是明确的实施门槛。

---

# 2. V1.0 Blocking Issue 复核

## 2.1 五种模式混成一个 enum

### V1.0 问题

把：

- Chain；
- Parallel；
- Router；
- Reflection；
- Hierarchical；

作为同一层的 OrchestrationMode。

### V1.1 修复

已拆成：

```text
execution_topology
routing_policy
review_policy
control_policy
```

并明确 execution topology 映射现有 Runtime Scheduler。

### 结论

**RESOLVED**

建议实施时继续保持：

- 不引入第二套 runnable-state machine；
- P0 先 projection，不强制迁移现有 `image_managed` 名字。

---

## 2.2 Character Agent 跨越 PREIMAGE frozen authority

### V1.0 问题

Character Agent 同时修改：

- Character Contract；
- Character Visual Contract；
- PREIMAGE Character Finalize。

这与当前 `CHARACTER_FINALIZE` 的 required_read / authority_scope 冲突。

### V1.1 修复

已拆为：

```text
Character Authoring / Lock
        ↓
frozen Character Contract / Character Visual
        ↓
PREIMAGE CharacterFinalizeAgentAdapter
        ↓
character.finalize only
```

### 结论

**RESOLVED**

当前边界与 `preimage_task_contract.py` 一致。

---

## 2.3 重复创建 Agent Runtime / Registry

### V1.0 问题

计划在 `episodes/_system` 新建通用 Agent Runtime / Registry。

### V1.1 修复

明确复用：

- `platform/agent/runtime/contracts.py`
- `platform/agent/runtime/agent_runtime.py`
- Skill / MCP / Trace / Recorder。

并明确：

> `AgentApplicationService` 当前进程内临时 Registry 不作为 Production Agent Registry 权威。

### 结论

**RESOLVED**

这是关键改进。

P0 推荐直接构造静态 Adapter → `AgentExecutionPlan`，不需要先建设 Agent Registry 平台。

---

## 2.4 Reducer 成为第二套 Commit Engine

### V1.0 问题

有复制 `authority_commit.py` 的风险。

### V1.1 修复

Reducer 被降级为：

```text
collect
→ verify
→ conflict check
→ existing authority_commit
```

### 结论

**RESOLVED**

实现时建议优先扩展 `preimage_protocol.py`，只有确实出现重复 collect/verify 逻辑时才新增薄 `preimage_reducer.py`。

---

# 3. V1.0 Major Issue 复核

## 3.1 Supervisor / Scheduler 重叠

V1.1 已明确：

```text
Global Coordinator
→ Episode selection

Runtime DAG + Scheduler
→ Node selection

Stage / Agent Adapter
→ selected Node execution adaptation
```

并将 Episode Supervisor 降为可选 Orchestration Facade。

**RESOLVED**

---

## 3.2 错误性能基线

V1.1 已改为：

```text
Baseline = current HEAD parallel PREIMAGE
Candidate = Agent Adapter path
```

并新增：

- 至少 5 次有效样本；
- median；
- paired shadow；
- technical retry 单独记录；
- Performance Ledger baseline。

**RESOLVED**

---

## 3.3 Runtime 名字 fallback 不等于 capability-safe routing

V1.1 已明确：

```text
fallback only when
required capabilities ⊆ executor capabilities
```

并要求动态 health probe + TTL。

**RESOLVED**

注意：当前 `runtime_router.py` 的 WebCodex → Codex fallback 仍然是 Runtime-level 能力；P4 的 task capability router 必须作为更窄的一层，不应破坏当前 router。

---

## 3.4 Three-View 生命周期不清

V1.1 已明确：

### Normal

```text
before Character Visual LOCK
```

### Late Override

```text
direct user evidence
→ derived validity fails
→ snapshot / frame contract / downstream reuse fail-closed
```

且明确：

> STALE 是派生有效性，不新增 Episode State。

**RESOLVED**

---

## 3.5 Guardian 重复 Recovery

V1.1 已纠正真实模块：

- `production_recovery.py`
- recovery persistence；
- `runtime_failure_classifier.py`
- `runtime_failure_strategy.py`
- persistent runner heartbeat；
- retry-tech；
- scheduler / checkpoint。

Guardian 定义为 detection / classification facade。

**RESOLVED**

---

## 3.6 Shadow 缺失

V1.1 已增加正式 P1.5 Shadow。

**RESOLVED**

---

## 3.7 AgentExecutionContract 字段不足

V1.1 已加入：

- idempotency_key；
- attempt；
- capability requirements；
- routing decision；
- deadline；
- shadow；
- parent execution；
- trace；
- resume；
- schema version。

且修正 `max_tokens=null` 语义。

**RESOLVED**

---

## 3.8 Duplicate Dispatch / Durable Commit

V1.1 已新增：

- D1 Candidate 后 crash；
- D2 双 dispatch；
- D3 commit response lost；
- D4 superseded late return。

并把 commit receipt 提升为 P0 Blocking Acceptance。

**RESOLVED AT DESIGN LEVEL**

实现尚未完成，属于 P0 工作项。

---

# 4. 当前唯一 Mandatory Implementation Gate

## Durable Execution Eligibility + Commit Receipt

现有 `authority_commit.py` 当前提供：

- expected SHA；
- snapshot id；
- lock；
- atomic write；
- append-only commit evidence。

但它当前**没有**：

- idempotency_key precondition；
- execution_id eligibility；
- attempt supersede；
- durable successful replay receipt。

因此当前代码不能直接保证：

```text
commit succeeded
→ response lost
→ same request replay
→ idempotent success
```

第二次调用现有 commit 更可能得到：

```text
STALE
```

因为 authority SHA 已发生变化。

这并不是 V1.1 的缺陷，因为 V1.1 已明确要求 P0 补齐。

## P0 Acceptance 必须证明

### A

```text
same idempotency_key
+ previous commit success
→ REPLAYED/PASS
→ zero second mutation
```

### B

```text
attempt 2 is active
attempt 1 late return
→ attempt 1 rejected
```

### C

```text
execution_id not eligible
→ commit fail-closed
```

### D

MySQL / JSON compatibility mode 行为一致。

在这些测试通过前：

> **Character Adapter 可以 Shadow，但不能替换 Production producer。**

---

# 5. 剩余 Major Implementation Concerns

这些不是方案级 blocker，但实施中必须控制。

## 5.1 AgentExecutionPlan 扩展必须 backward-compatible

当前 Platform Contract 很小：

```text
AgentExecutionPlan
  agent_code
  agent_version
  context
  steps
  execution_type
  execution_id
```

建议 P0 优先：

### 方案 A：扩展 optional 字段

如果 API / persistence serialization 无破坏。

或：

### 方案 B：Episode Adapter Envelope

```text
EpisodeAgentExecutionEnvelope
        contains
AgentExecutionPlan
```

如果直接改 Platform Contract 会影响现有 P7.4 API。

必须先跑：

- Agent API；
- execution recorder；
- trace；
- shadow validation；

回归后再决定。

---

## 5.2 Shadow Comparator 不应默认再加一个昂贵 LLM

建议比较顺序：

```text
schema
→ deterministic field coverage
→ normalized structural diff
→ domain-specific validators
→ sampled semantic critic only when needed
```

否则 Shadow 本身会显著增加 token / wall time，使性能结论失真。

---

## 5.3 Capability health 需要 freshness

V1.1 已要求 probe timestamp / TTL。

实施必须区分：

```text
declared capability
available now
healthy enough for this task
```

不要因为“codex.exe 存在”就认为：

- host workspace；
- review isolation；
- image generation；
- connector；

都可用。

---

## 5.4 Three-View late override 必须通过验证链失效，不回滚 Stage

V1.1 已写对。

实现验收必须证明：

```text
Episode still STORYBOARD_LOCKED or current legal state
BUT
old downstream evidence becomes non-reusable
```

不要新增：

```text
EPISODE_STATE = STALE
```

---

# 6. Minor Issues

## 6.1 delegated_managed 名字暂不值得迁移

当前 Runtime Scheduler 合法值：

```text
serial
parallel_safe
image_managed
```

V1.1 的 `delegated_managed` 作为目标语义合理。

建议 P0：

```text
保持 image_managed
增加 semantic projection / alias
```

不要为命名改动制造大范围 migration。

---

## 6.2 Agent 数量不是 KPI

V1.1 已基本从“Agent 数量”转为收益判断，这是正确的。

最终评价应看：

- wall；
- token；
- quality；
- recovery。

不是 Agent 数。

---

# 7. 推荐的最终实施顺序

二次评审建议保持 V1.1 顺序，仅把 P0 再明确为三个小阶段。

## P0-A：Baseline / Contract Freeze

- freeze current HEAD benchmark；
- Platform Agent Contract compatibility assessment；
- orchestration metadata projection；
- no behavior change。

## P0-B：Execution Identity

- idempotency；
- execution_id；
- attempt；
- supersede；
- resume；
- trace。

## P0-C：Commit Receipt

- durable receipt；
- eligibility precondition；
- replay；
- D1-D4 failure injection；
- MySQL / JSON parity。

通过后才进入：

## P1

Character Finalize Adapter。

## P1.5

Shadow。

## P1 Production

只有 Shadow + P0 Commit Gate 都通过后。

之后：

## P2

World / Visual，一个一个接。

## P3+

Critic / Router / Guardian 按收益推进。

---

# 8. 二次评审 Go / No-Go

## GO：现在可以开始

以下工作可以直接开工：

- P0-A Baseline；
- P0-B Execution Identity；
- P0-C Commit Receipt；
- Character Adapter skeleton；
- Shadow comparison framework；
- related tests。

## CONDITIONAL GO

以下必须等 P0 Gate：

- Character Agent 替换现有 Production Character producer；
- Agent Candidate 成为 canonical PREIMAGE 输入；
- duplicate-dispatch runtime 正式启用。

## 暂不应实施

- 新 Agent Registry Service；
- 新 Authority Commit Engine；
- 新 Episode Scheduler；
- 大 Episode Supervisor；
- World / Visual / Critic 全部同时上线。

---

# 9. 最终评审结论

V1.1 已经从“架构概念方案”收敛成了**可以实施的增量改造方案**。

它现在与当前 StoryOS 的真实能力关系清楚：

```text
Runtime DAG
        ↓
Runtime Scheduler
        ↓
Agent Adapter
        ↓
Platform AgentRuntime
        ↓
Candidate
        ↓
Existing Verifier / Barrier
        ↓
Existing Authority Commit
```

并且：

- Runtime Router 不被重造；
- Recovery 不被重造；
- Agent Registry 不被重造；
- Commit Engine 不被重造；
- Episode State 不被重造。

因此二次评审正式结论：

# **GO FOR IMPLEMENTATION**

但这里的 GO 指：

> **可以进入 P0，并在 P0 通过后进入 Character Adapter Shadow。**

不是：

> “现在立即把所有子 Agent 开进生产。”

Production Cutover 的硬 Gate 是：

```text
Durable Commit Receipt
+ Attempt Supersede
+ D1-D4
+ Character Shadow
+ Performance Baseline
+ Authority Zero Regression
```

全部通过。

在此条件下，这套架构值得实施。
