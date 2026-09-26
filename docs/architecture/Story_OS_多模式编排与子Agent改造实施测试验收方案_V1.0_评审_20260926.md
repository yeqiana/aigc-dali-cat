# Story OS 多模式编排与子 Agent 改造实施 / 测试 / 验收方案 V1.0 — 架构评审

> 日期：2026-09-26
> 评审对象：`Story_OS_多模式编排与子Agent改造实施测试验收方案_V1.0_20260926.md`
> 评审方式：独立架构评审 / 对照当前 Runtime DAG、PREIMAGE、Agent Runtime、Runtime Router、Resource Manager 与三视图实现
> 结论：**CONDITIONAL GO / 需要修订后实施**

---

# 1. 总体结论

方案的大方向是正确的：

```text
Deterministic Runtime
+ Specialized Agents
+ Candidate-only
+ Single Writer
+ Bounded Reflection
+ Capability Routing
```

与 StoryOS 当前演进方向一致，而且明确拒绝：

- Agent 直接推进 Episode State；
- 多 Agent 并发写 Authority；
- 无限 Reflection；
- 把所有 deterministic workflow Agent 化；
- 把 WebCodex 槽位当生产 Worker Pool。

这些边界必须保留。

但 V1.0 当前仍存在一类核心问题：

> **有些“新架构模块”其实已经以不同名字存在；有些“模式”属于不同抽象层，却被放进同一个 OrchestrationMode；Character Agent 的职责边界又跨过了当前 PREIMAGE 已冻结的 Authority 输入。**

如果按文档当前结构直接实施，风险不是“做不出来”，而是：

1. 重复实现已有 Runtime；
2. 新增第二套 Agent Contract / Registry；
3. 让 PREIMAGE Character Agent 同时改它本来应该读取的 Authority；
4. 让 Supervisor / Coordinator / Runtime Scheduler 三层职责重叠；
5. 用“对比串行”证明一个当前已经并行的系统性能提升，验收指标失真。

因此：

```text
方向：GO
当前 V1.0 直接实施：NO-GO
完成本评审 Blocking Revision 后：GO
```

---

# 2. Blocking Issue 1：五种“模式”不是同一抽象层

V1.0 把：

```text
Chain
Parallel
Router
Reflection
Hierarchical
```

统一定义为五种 Orchestration Mode。

这在概念上不够准确。

其中：

### Graph / Topology

```text
Chain
Parallel
```

描述任务之间的拓扑关系。

### Decision Policy

```text
Router
```

描述“任务由谁执行”。

### Quality Protocol

```text
Reflection
```

描述“结果如何复审和修复”。

### Control Structure

```text
Hierarchical
```

描述“谁负责拆解 / 监督 / 聚合”。

它们不是同一个 enum 的互斥值。

当前 `runtime_scheduler.py` 已经有：

```text
serial
parallel_safe
image_managed
```

如果再创建：

```text
OrchestrationMode =
CHAIN / PARALLEL / ROUTER / REFLECTION / HIERARCHICAL
```

会产生第二套执行语义。

## Required Revision

将“多模式”拆成四个维度：

```text
execution_topology:
  serial | parallel_safe | delegated_managed

routing_policy:
  fixed | capability_route

review_policy:
  none | critic | bounded_reflection

control_policy:
  direct | supervised
```

并优先映射到现有 `execution_policy`，不要另造一套互斥模式状态机。

**此项修改完成前，不应实现 OrchestrationMode enum。**

---

# 3. Blocking Issue 2：Character Agent 当前职责跨越 PREIMAGE Authority 边界

V1.0 中 Character Agent 同时负责：

- Character Contract Candidate；
- Character Visual Candidate；
- 三视图；
- PREIMAGE Character Finalize Candidate。

但当前 `preimage_task_contract.py` 的 `CHARACTER_FINALIZE` 明确：

```text
required_read:
  meta/character-contract.json
  meta/character-visual-contract.json

authority_scope:
  character.finalize
```

也就是说：

> Character Contract 和 Character Visual Contract 是 PREIMAGE Character Finalize 的**输入 Authority**，不是它的输出 Scope。

如果同一个 Character Agent 在 PREIMAGE 阶段又重写：

```text
character-contract
character-visual-contract
```

则会导致：

```text
读取 frozen input
→ Agent 修改 input authority
→ snapshot stale
→ candidate 自己把自己变 stale
```

或者更坏：

```text
Agent 绕过 PREIMAGE scope
→ 修改不属于 character.finalize 的 Canonical Authority
```

## Required Revision

必须拆成两个生命周期角色：

### A. Character Authoring / Lock

发生在 PREIMAGE 之前：

```text
Character Seed
→ Three-View optional input
→ Character Contract
→ Character Visual Contract
→ LOCK
```

可以由 Character Agent 辅助生成 Candidate，但最终必须在 Storyboard Lock / PREIMAGE 前冻结。

### B. PREIMAGE Character Finalize

只允许：

```text
read Character Contract
read Character Visual Contract
read Three-View summary
→ output character.finalize Candidate
```

不得重写 Character Contract / Character Visual Contract。

因此 Phase 1 应定义为：

> **Character Agent Adapter for existing CHARACTER_FINALIZE**

而不是“一次性接管所有人物 Authority”。

---

# 4. Blocking Issue 3：提议的新 Agent Runtime / Registry 与现有 Platform Agent Runtime 重复

V1.0 第 22 节建议新增：

```text
episodes/_system/agent_execution_contract.py
episodes/_system/agent_registry.py
```

但仓库已经存在：

```text
platform/agent/runtime/agent_runtime.py
platform/agent/runtime/contracts.py
platform/agent/application/agent_service.py
```

现有 `AgentRuntime` 已明确：

> executes an already-decided plan; does not choose Workflow steps, Agents, Skills, or business state transitions.

这和新方案希望保持的权限边界完全一致。

现有 `AgentApplicationService` 也已经包含 Agent definition registry / execute plan facade。

## Required Revision

P0 不得在 `episodes/_system` 再造一套通用 Agent Runtime / Registry。

应改为：

```text
platform.agent.runtime.contracts
        ↑ extend only when necessary

platform.agent.runtime.AgentRuntime
        ↑ reuse

Episode-specific adapter
        ↓
episodes/_system/agents/character_agent_adapter.py
```

如果现有 Platform Agent Contract 不足，应优先：

1. 扩字段；
2. 新增 Episode Adapter；
3. 保持 Agent Runtime 仍只执行 already-decided plan。

只有证明现有 Platform Runtime 无法承载 Candidate-only Contract 时，才允许新增新的通用 runtime contract。

---

# 5. Blocking Issue 4：Authority Reducer 不应成为第二套 Commit Engine

V1.0 提议新增：

```text
authority_reducer.py
```

但当前已经存在：

- `authority_commit.py`
- PREIMAGE Barrier；
- expected SHA；
- scope collision；
- atomic replace；
- stale fail-closed。

当前 PREIMAGE 实际已经实现：

```text
Task
→ Candidate
→ Verify
→ Barrier
→ authority_commit
```

## Required Revision

“Reducer”应作为**逻辑角色 / facade**，而不是新的 Authority Engine。

第一阶段推荐：

```text
preimage_reducer.py
  = collect + verify + call existing authority_commit
```

或者直接扩展 `preimage_protocol.py`。

不得出现：

```text
authority_commit.py
+
authority_reducer.py
```

各自维护一套 stale / lock / atomic commit 逻辑。

---

# 6. Major Issue 1：Episode Supervisor 与已有 Runtime Coordinator / Scheduler 职责可能重叠

当前已经存在：

- Episode Runner；
- Runtime DAG；
- Runtime Scheduler；
- Runtime Resource Manager；
- Runtime Checkpoint；
- Next Action；
- 全局 Coordinator 设计。

V1.0 又新增：

```text
Runtime Coordinator
→ Capability Router
→ Episode Supervisor
→ Stage Supervisor
```

层级有膨胀风险。

如果每层都负责：

- dispatch；
- dependency；
- resource；
- retry；
- resume；

很容易出现“双调度源”。

## Required Revision

先定义唯一 Owner：

### Global

```text
Runtime Coordinator
→ 选择哪个 Episode 可以运行
```

### Episode

```text
Runtime DAG + Runtime Scheduler
→ 选择哪个 Node 可以运行
```

### Agent Task

```text
Stage Adapter
→ 把一个 Node 转成 AgentExecutionPlan
```

因此“Episode Supervisor”第一阶段不应做成独立常驻调度器。

建议改名 / 降级为：

```text
Episode Orchestration Facade
```

只组合现有 DAG / Router / Agent Runtime，不拥有新状态。

---

# 7. Major Issue 2：性能基线选错

V1.0 验收：

```text
PREIMAGE wall time 相比串行下降 ≥ 30%
```

但当前 StoryOS PREIMAGE 已经：

- 四 Host Task split；
- parallel；
- barrier；
- atomic commit；
- 已观察 peak > 1。

所以“相比串行”只能证明并行本身有效，不能证明**新增 Agent Protocol**有效。

## Required Revision

性能必须对比：

```text
Baseline = 当前 HEAD 的现有 PREIMAGE parallel implementation
Candidate = Agent Protocol PREIMAGE
```

Phase 1 首要门槛：

```text
wall time regression <= 5%
token regression <= 10%
model calls 不无故增加
authority correctness = 100%
```

只有 Character / World / Visual Agent 真正带来新的并行度或更小 Context 后，再设置优化目标。

建议二阶段目标：

```text
PREIMAGE wall time improvement >= 10~20%
或
token / repeated-read reduction >= 20%
```

而不是直接要求 30%。

---

# 8. Major Issue 3：Router 必须是 capability-safe，不是 Runtime 名字 fallback

当前 `runtime_router.py` 已经支持：

```text
WebCodex detected → WORK
WebCodex unavailable + Codex CLI → CODEX
```

但任务级 Router 不能简单认为：

```text
WORK unavailable
→ CODEX
```

等价。

例如某 Task 可能需要：

- host-managed workspace；
- isolated reviewer；
- connector；
- product runtime host action；
- image capability。

Codex CLI 未必具备这些能力。

## Required Revision

Capability Router 必须先：

```text
required capabilities
∩
executor capabilities
```

匹配成功后才能 fallback。

必须新增测试：

```text
WebCodex off
+ Codex on
+ task requires host-managed capability
→ NOT ROUTABLE
```

不能只测“Codex installed = fallback success”。

---

# 9. Major Issue 4：三视图的生命周期需要明确注册窗口

当前三视图代码已经做到：

- optional；
- SHA validation；
- Character Visual Contract stale binding；
- Pixel Master supersedes three-view。

但方案只说“三视图可选”，没有规定什么时候允许新增 / 修改。

如果在：

```text
Frame Contract 已编译
Visual Lock 已生成
```

之后替换三视图，则应触发何种 invalidation？

## Required Revision

必须写清：

### Recommended

```text
Three-View Registration Window:
  Character Authoring
  → before Character Visual LOCK
```

### Late Override

若 Storyboard Lock 后用户显式替换：

```text
direct user authority change
→ Character Visual stale
→ PREIMAGE stale
→ Frame Contract stale
→ Visual candidate authority refresh
```

不能静默替换。

---

# 10. Major Issue 5：Guardian 应优先收敛已有 Recovery，而不是新建大模块

V1.0 Guardian 包含：

- heartbeat；
- queue stuck；
- stale lease；
- network；
- MySQL；
- invalid state；
- retry budget；
- reconcile。

但 StoryOS 已经有：

- runtime_recovery；
- persistent runner；
- scheduler；
- retry-tech；
- checkpoint；
- failure strategy。

## Required Revision

Phase 5 首先应做：

```text
Guardian = Detection + Classification facade
```

复用已有 recovery action。

禁止第一版：

```text
runtime_guardian.py
自己实现 retry
自己实现 state repair
自己实现 lease recovery
```

否则必然形成第二套 recovery engine。

---

# 11. Major Issue 6：缺少 Shadow Mode

虽然 V1.0 提到了 conditional go / shadow，但实施阶段没有正式 Shadow Phase。

对于 Agent Protocol 改造，最安全路线应是：

```text
current production path writes authority
+
new agent path runs shadow
+
compare candidate / latency / token / issue codes
+
new agent path no commit
```

## Required Revision

在 Phase 1 和 Phase 2 之间增加：

```text
Phase 1.5：Shadow Agent Run
```

至少覆盖：

- Character Finalize；
- World；
- Visual Narrative。

Shadow 期间：

- 不写 Canonical Authority；
- 允许写 trace / shadow comparison；
- 比较 semantic equivalence；
- 比较 token / wall time；
- 不影响 Gate。

---

# 12. Major Issue 7：AgentExecutionContract 仍缺少几个生产字段

方案中的 Contract 缺：

- idempotency_key；
- attempt；
- expected_output_sha / candidate schema version；
- deadline；
- routing decision；
- capability requirements；
- cancellation / superseded；
- parent execution / trace；
- shadow flag；
- resume token / checkpoint reference。

## Required Revision

最低增加：

```json
{
  "idempotency_key": "...",
  "attempt": 1,
  "candidate_schema_version": 1,
  "capability_requirements": [],
  "routing_decision": {},
  "deadline_at": "...",
  "shadow": false,
  "parent_execution_id": "...",
  "trace_id": "...",
  "resume_from": null
}
```

同时明确：

```text
max_tokens = 0
```

到底表示：

- 禁用？
- 无限？
- 不配置？

建议用 `null` 表示未设置，不使用 0 表达无限。

---

# 13. Major Issue 8：还缺 Durable / Duplicate Dispatch 验收

多 Agent 后真正危险的问题不是普通 fail，而是：

```text
dispatch succeeded
→ process crash
→ restart
→ same task dispatched again
```

当前方案故障注入里有 Agent crash，但没有把“重复 dispatch / exactly-once commit”单独列出来。

## Required Revision

新增测试：

### D1

```text
Agent returns Candidate
→ host crashes before status update
→ resume
→ same idempotency_key
→ no duplicated canonical commit
```

### D2

```text
same task dispatched twice
→ two Candidate
→ only expected execution/attempt can commit
```

### D3

```text
Reducer commit success
→ response lost
→ retry Reducer
→ idempotent success / no duplicate mutation
```

---

# 14. Minor Issue 1：Agent 数量不应成为硬验收指标

V1.0：

```text
简单 Episode Agent 激活数 ≤ 3
```

这是有意义的成本提醒，但不适合作为最终硬 Gate。

更合理：

- Agent activation count 可观测；
- 与 baseline 比较；
- “无收益的 Agent”淘汰。

否则以后合理的 4 个轻量 Agent 会因数字本身失败。

---

# 15. Minor Issue 2：E2E 范围应分阶段

V1.0 总体验收要求：

```text
至少一个全新 Episode IDEA → PUBLISH_READY
```

作为最终验收合理。

但 Phase 0 / 1 不应要求每次都跑完整发布链。

建议：

### Phase 0

Contract / adapter tests。

### Phase 1

Story Lock → PREIMAGE → Frame Contract。

### Phase 2 / 3

Visual Lock / Review。

### Final

全新 Episode → PUBLISH_READY。

降低早期迭代成本。

---

# 16. Minor Issue 3：Context Capsule 应尽量复用现有 PREIMAGE task_contract

当前 `preimage_task_contract.py` 已经有：

- task_id；
- task_type；
- snapshot_id；
- depends_on；
- required_read；
- authority_inputs；
- candidate_output；
- verifier；
- retry_policy；
- authority_scope；
- candidate_only target。

这已经非常接近方案里的 Input Capsule。

因此不建议 P0 新造完全独立的 Capsule Schema。

应优先：

```text
PREIMAGE Task Contract
→ generalize into Agent Execution Input
```

而不是：

```text
PREIMAGE Task Contract
+
Agent Input Capsule
```

并存两套。

---

# 17. 推荐修订后的实施顺序

原方案：

```text
Contract
→ Character Agent
→ PREIMAGE Supervisor
→ Reducer
→ World Agent
→ Visual Agent
...
```

评审建议调整为：

## P0：抽象对齐，不加 Runtime

1. 盘点并复用：
   - Platform AgentRuntime；
   - AgentExecutionPlan；
   - PREIMAGE Task Contract；
   - Runtime Scheduler；
   - Resource Manager；
   - Authority Commit。
2. 定义四维 orchestration metadata；
3. 扩展 Candidate-only permission；
4. 补 idempotency / attempt / trace 字段。

## P1：Character Agent Adapter

只包装：

```text
PREIMAGE_CHARACTER_FINALIZE
```

不修改 Character Contract / Visual Contract。

三视图继续作为 frozen input。

## P1.5：Shadow

新 Character Agent 与现有 Host Task 同时运行：

```text
old path = authority
new path = shadow
```

比较：

- semantic output；
- latency；
- token；
- repeated reads；
- failure rate。

## P2：World / Visual Narrative Adapter

逐个替换现有 PREIMAGE producer。

仍复用原 Candidate / Barrier / Commit。

## P3：Critic Protocol + Bounded Reflection

统一 Review 合同，但先不改 Gate。

## P4：Task Capability Router

扩展 `runtime_router` / Runtime Scheduler，而不是另造总 Router。

## P5：Guardian Facade

先统一检测，动作继续调用现有 Recovery。

## P6：Episode Orchestration Facade

只有当 P0-P5 证明现有 Episode Runner / DAG 的组合调用确实难维护时，再引入 facade。

**不建议预先承诺一个全新的 Episode Supervisor service。**

---

# 18. 修订后的性能验收建议

## P1 / Shadow

| 指标 | 门槛 |
|---|---:|
| Authority correctness | 100% |
| wall time regression | ≤ 5% |
| token regression | ≤ 10% |
| extra model call on no-three-view path | 0 |
| stale commit | 0 |
| duplicate canonical commit | 0 |

## P2

| 指标 | 目标 |
|---|---:|
| PREIMAGE wall time vs current HEAD | 改善 ≥ 10%，或不退化且 token 降 ≥ 20% |
| repeated authority reads | 降 ≥ 20% |
| parallel utilization | ≥ current HEAD |
| Candidate reject due contract mismatch | < 5% |

## Final

在真实 Episode 中证明：

- Agent 模式不是只“换名字”；
- 至少在 speed / token / quality / recovery 中一项有可测收益；
- 其它关键指标无明显回退。

---

# 19. Go / No-Go 条件

## 修订后 GO

满足：

- 五模式拆成不同维度；
- Character Agent lifecycle 修正；
- 不复制 Platform Agent Runtime / Registry；
- Reducer 复用 authority_commit；
- 加 Shadow Phase；
- Capability-safe fallback；
- Durable duplicate-dispatch tests；
- 性能 baseline 改为 current HEAD。

## 当前版本 NO-GO 的实施项

不得直接开始：

- 新建第二套通用 Agent Registry；
- 新建第二套 Authority Commit Engine；
- Character Agent 在 PREIMAGE 修改 Character Contract；
- 先开发“大 Episode Supervisor”；
- 用 serial baseline 宣称 Agent 改造提速。

---

# 20. 最终评审意见

这份方案**值得继续**，而且“确定性骨架 + 专业 Agent + Single Writer”是正确方向。

但 StoryOS 当前已经比普通 Agent 项目成熟得多：

- 有 DAG；
- 有 parallel task；
- 有 snapshot；
- 有 candidate；
- 有 barrier；
- 有 atomic commit；
- 有 Agent Runtime；
- 有 resource manager；
- 有 recovery。

因此下一阶段的关键不是“把这些能力重新用 Agent 名字写一遍”，而是：

> **把现有能力统一到同一个 Agent Execution Protocol 下，同时保持已有 Authority / DAG / Recovery 为唯一事实源。**

评审建议：

```text
V1.0 = CONDITIONAL GO

先按 Blocking Issue 1~4 修订为 V1.1
再进入 P0 / P1
```

其中第一批真正值得实施的代码只有：

1. orchestration metadata 对齐；
2. Platform AgentRuntime Candidate-only 扩展；
3. Character Agent Adapter；
4. Shadow comparison；
5. 测试与 Performance Ledger。

**先证明 Character Agent 有收益，再决定是否继续增加 World / Visual / Critic Agent。**
