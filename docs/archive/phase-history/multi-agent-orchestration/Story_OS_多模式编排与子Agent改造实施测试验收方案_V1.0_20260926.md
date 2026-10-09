# Story OS 多模式编排与子 Agent 改造实施 / 测试 / 验收方案 V1.0

> 日期：2026-09-26
> 状态：IMPLEMENTATION PLAN / 待评审
> 适用范围：StoryOS Runtime / Workflow / Agent Runtime / PREIMAGE / Review / Release
> 原则：**不推翻现有 Runtime DAG，不新增第二套状态机，不让 Agent 直接写 Canonical Authority。**

---

# 1. 背景与改造目标

StoryOS 当前已经具备：

- Episode State / Runtime DAG / Next Action；
- PREIMAGE 四任务并行协议；
- Candidate → Verify → Barrier → Single Writer Atomic Commit；
- Frame Contract 并行编译；
- Image Scheduler / Batch Scheduler；
- Retry / Recovery / Ledger / Evidence；
- WORK / WebCodex / CODEX Runtime 路由与 fallback；
- Character Contract / Character Visual Contract；
- Story Semantic / Recent-5 / Concept Ambition / Final Review；
- MySQL Authority + Runtime Workspace + Event / Trace / Performance Ledger。

当前缺口已经不是“有没有 Agent”或“有没有 DAG”，而是：

1. 任务编排仍以单一路径思维为主，缺少显式的 **Chain / Parallel / Router / Reflection / Hierarchical** 多模式执行协议；
2. PREIMAGE 等步骤已经表现出子 Agent 雏形，但 Agent 身份、职责、输入输出、权限、Candidate 协议和调度协议还没有统一；
3. Runtime Router 已能选择 WORK / CODEX，但还没有形成“任务级能力路由”；
4. Reflection / Critic 目前分散在不同模块，没有统一次数、成本、升级和终止规则；
5. Worker / Agent / Supervisor / Deterministic Gate 的职责边界需要进一步固化；
6. 前期人物一致性已经新增可选三视图入口，需要由 Character 子 Agent 统一消费，而不是继续把人物约束散落到 prompt；
7. 多 Agent 增加后，必须防止：
   - 重复读取同一 Authority；
   - 多 Agent 同时写共享状态；
   - Agent 数量导致 token / latency 反增；
   - LLM 接管本应确定性执行的 Gate / Retry / State Transition。

本次改造目标不是“Agent 越多越好”，而是形成：

```text
Deterministic Runtime Skeleton
        +
Multi-Mode Orchestration
        +
Specialized SubAgents
        +
Single-Writer Authority
        +
Bounded Reflection
        +
Capability-Aware Routing
```

---

# 2. 明确不做什么

本次方案明确不做：

1. 不新建第二套 Episode State。
2. 不替换现有 `runtime_dag.py`。
3. 不替换现有 `scheduler_core.py` / `image_scheduler.py`。
4. 不把所有 Runtime Step 改成 Agent。
5. 不允许 Agent 直接：
   - transition Episode State；
   - 修改 Gate PASS；
   - 覆盖已 PASS Authority；
   - 跳过失败；
   - 修改 Repair Budget；
   - 修改 Ledger 状态机规则。
6. 不让多个 Agent 同时写同一 Authority。
7. 不把 WebCodex 槽位当 StoryOS Worker Pool。
8. 不引入依赖外部 Agent Framework 才能运行的核心路径。
9. 不以“Agent 聊天”作为 Agent 间状态同步方式。
10. 不把 Reflection 做成无限循环。

---

# 3. 目标架构

## 3.1 总体结构

```text
                         Runtime Coordinator
                                 │
                        Capability Router
                                 │
                         Episode Supervisor
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
         Story Lane          Preimage Lane       Release Lane
             │                   │                   │
         Story Agent        Stage Supervisor      Release Agent
             │                   │
             │        ┌──────────┼──────────┐
             │        │          │          │
             │   Character    World / Env   Visual Director
             │      Agent        Agent         Agent
             │        └──────────┼──────────┘
             │                Parallel
             │                   │
             └──────────── Authority Reducer
                                 │
                           Frame Contract
                                 │
                         Visual Lock 1 + 3
                                 │
                       Production Scheduler
                                 │
                       Parallel Frame Workers
                                 │
                          Review / Critic
                                 │
                        Bounded Reflection
                                 │
                           Release Chain
```

---

# 4. 五种编排模式

StoryOS 不采用单一 Agent 模式，而是按任务性质选择执行模式。

## 4.1 Chain Mode

适合存在硬顺序依赖、Authority Commit、状态推进的步骤。

典型路径：

```text
Story Lock
→ Semantic Review
→ Storyboard Lock
→ PREIMAGE Barrier
→ Frame Contract Index Commit
→ Visual Lock
→ Production Closure
→ Release
```

规则：

- 前置 Evidence 未完成，不得推进；
- Chain Node 不允许 speculative commit；
- Authority Commit 必须 single writer；
- Chain 只负责顺序，不负责创意推理。

## 4.2 Parallel Mode

适合输入冻结后相互独立的 Candidate Task。

典型场景：

- PREIMAGE：
  - Character Finalize；
  - Environment Prepare；
  - World Prepare；
  - Visual Narrative Prepare。
- Frame Contract 多帧编译；
- 独立图片生产；
- 多项 deterministic validators；
- 多个独立 review dimensions。

规则：

- Parallel Task 只能写独立 Candidate；
- 所有 Candidate 绑定相同 Authority Snapshot；
- Barrier 前必须检查 stale；
- Barrier 后由 Reducer 单次 commit；
- 任一 Candidate 失败，不污染已成功兄弟 Candidate。

## 4.3 Router Mode

Router 根据任务能力需求，而不是固定 Agent 名字选择执行器。

输入至少包括：

```json
{
  "task_type": "CHARACTER_PREPARE",
  "requires": ["reasoning", "file_read"],
  "authority_scope": ["character"],
  "latency_class": "normal",
  "quality_class": "high",
  "runtime_constraints": {
    "webcodex_preferred": true,
    "codex_fallback": true
  }
}
```

路由优先级：

```text
显式 Runtime Override
    ↓
当前能力可用性
    ↓
任务权限
    ↓
任务质量要求
    ↓
成本 / 延迟预算
    ↓
Fallback
```

Runtime 基础策略：

```text
WebCodex 可用
→ WORK + WebCodex

WebCodex 不可用 + Codex CLI 可用
→ CODEX fallback

两者均不可用
→ HOST_WAIT / BLOCKED
```

不得因 fallback 改变 Authority 权限模型。

## 4.4 Reflection Mode

Reflection 只用于“高价值语义 / 视觉判断”，不用于所有任务。

统一规则：

```text
Generate
→ Deterministic Validate
→ Cheap Local / Rule Triage
→ Critic
→ 最多 1 次自动 targeted repair
→ Final Critic
→ PASS / NEEDS_USER / BLOCK
```

默认限制：

- `max_reflection_rounds = 2`
- 自动 repair 默认最多 1 次；
- 第二次仍失败，进入 NEEDS_USER / escalation；
- technical retry 不计入 reflection；
- Reflection 不得修改 Runtime State；
- Reflection 结果必须有结构化 issue_codes。

## 4.5 Hierarchical Mode

复杂阶段采用 Supervisor → SubAgent，而不是 Peer-to-Peer Agent Swarm。

```text
Episode Supervisor
      │
Stage Supervisor
      │
  ┌───┼───────────┐
  ↓   ↓           ↓
Agent Agent      Agent
  │   │           │
Candidate Outputs
      │
    Reducer
```

Supervisor 负责：

- 任务拆分；
- dependency；
- routing；
- budget；
- retry classification；
- Candidate 收集；
- conflict detection；
- Barrier；
- Reducer 调用。

Supervisor 不负责直接创作内容。

---

# 5. 子 Agent 设计

第一阶段最多正式化 5 个专业子 Agent，避免 Agent 膨胀。

## 5.1 Story Agent

职责：

- Story candidate；
- 结构与因果链优化；
- 主角动作—异常回应链；
- 高层叙事修订。

输入：

- Concept；
- Story constraints；
- Character identity summary；
- recent-5 evidence；
- standards snapshot。

输出：

```text
StoryCandidate
StoryChangeSet
StoryEvidence
```

禁止：

- 直接写 story-gates PASS；
- 直接推进 Episode State；
- 自己 finalize semantic review。

## 5.2 Character Agent

这是第一优先级落地的子 Agent。

职责：

- Character Contract Candidate；
- Character Visual Candidate；
- 三视图 Identity Anchor；
- Hair / Face / Body / Wardrobe continuity；
- 人物可见性和关系；
- PREIMAGE Character Finalize Candidate；
- Pixel Master 之前的人物身份权威输入整理。

人物身份链：

```text
文字 Character Seed
    ↓
三视图（可选）
    ↓
Character Visual Contract
    ↓
PREIMAGE Character Candidate
    ↓
Frame Identity Requirement
    ↓
Visual Lock Baseline
    ↓
Pixel Master
    ↓
Character Crop
```

优先级：

```text
Character Crop
> Pixel Master
> Character Three-View
> Series Character Identity
> Text Contract
```

未提供三视图时：

```text
three_view.applicable = false
→ 完全沿用旧流程
```

## 5.3 World Agent

职责：

- World Identity；
- Environment；
- Temporal Continuity；
- physical cues；
- 可见世界规则；
- 世界与人物服装/道具环境一致性。

输出：

```text
WorldCandidate
EnvironmentCandidate
TemporalContinuityCandidate
```

## 5.4 Visual Director Agent

职责：

- Visual Narrative；
- Shot Progression；
- Frame visual function；
- capture grammar；
- high-impact frame intent；
- visual continuity。

不负责：

- 真正图片生成；
- Provider routing；
- Ledger；
- Pixel PASS。

## 5.5 Critic Agent

职责：

- Story Semantic；
- Concept Ambition；
- Visual Semantic；
- Final QA；
- adversarial review。

必须与创作 Agent 隔离：

- fresh context；
- 只读 Authority；
- 唯一允许写 Candidate Review；
- Reviewer 不负责修复；
- 修复必须回到对应创作 Agent。

---

# 6. Agent Execution Contract

统一定义：

```json
{
  "agent_execution_id": "ae_xxx",
  "task_id": "task_xxx",
  "agent_type": "CHARACTER",
  "mode": "parallel",
  "authority_snapshot": {
    "story_sha256": "...",
    "character_sha256": "..."
  },
  "input_capsule": {},
  "allowed_reads": [],
  "allowed_writes": [
    "candidate_path"
  ],
  "forbidden_writes": [
    "episode_state",
    "story_gates",
    "production_ledger"
  ],
  "budget": {
    "max_rounds": 1,
    "max_tokens": 0,
    "timeout_seconds": 900
  }
}
```

## 6.1 Candidate-only 原则

子 Agent 的输出必须遵守：

```text
SubAgent
→ Candidate
→ Schema Validate
→ Authority Snapshot Validate
→ Scope Collision Check
→ Conflict Check
→ Reducer
→ Atomic Commit
```

严禁：

```text
SubAgent → Canonical Authority
```

---

# 7. Reducer / Single Writer

新增统一逻辑角色：

```text
Authority Reducer
```

它可以由 deterministic code 实现，不需要 LLM。

职责：

1. 检查所有 required Candidate 是否到齐；
2. 检查 Authority Snapshot 是否 stale；
3. 检查 scope collision；
4. 检查 Candidate schema；
5. 检查互斥字段；
6. 生成 commit plan；
7. 单次 atomic commit；
8. 记录 commit evidence；
9. 更新 barrier。

Reducer 不做：

- 创作；
- 内容评分；
- Runtime 路由。

第一阶段优先复用现有：

- `authority_commit.py`
- PREIMAGE Barrier
- expected SHA
- process lock
- atomic replace

不重新造一套 commit 系统。

---

# 8. Capability Router

## 8.1 能力模型

建议统一 capability：

```text
reasoning
vision
image_generation
filesystem
workspace_edit
mysql
local_visual
review_isolation
long_context
low_latency
high_quality
```

执行器注册：

```json
{
  "executor": "WORK",
  "provider": "WebCodex",
  "capabilities": [
    "reasoning",
    "filesystem",
    "workspace_edit",
    "review_isolation"
  ]
}
```

## 8.2 路由决策

Router 只做 deterministic 选择：

```text
Task Requirement
    ↓
Allowed Executors
    ↓
Available Executors
    ↓
Runtime Policy
    ↓
Capacity
    ↓
Cost / Latency
    ↓
Selected Executor
```

禁止 LLM 自己决定“我想用哪个 Runtime”。

---

# 9. Runtime Guardian

用户要求的“额外监测并发槽”不应最终实现为一个长期占资源的 LLM Agent。

正式方案应拆成：

## 9.1 Deterministic Guardian

职责：

- Worker heartbeat；
- Job timeout；
- stale lease；
- queue stuck；
- provider network error；
- MySQL error；
- invalid state transition；
- authority stale；
- deadlock / lock age；
- retry budget；
- host request age。

运行方式：

```text
Event-driven
+
periodic reconcile
```

## 9.2 Diagnostic Agent

只有 Guardian 检测到“不确定技术故障”时才按需启动。

```text
Guardian detects anomaly
→ classify
→ deterministic repair possible?
    YES → repair
    NO  → Diagnostic Agent
```

这样避免“为了监控而常驻一个 LLM”。

---

# 10. Dynamic Agent Activation

不是每个 Episode 都启动所有 Agent。

## 10.1 启动矩阵

| 场景 | Story | Character | World | Visual | Critic |
|---|---:|---:|---:|---:|---:|
| 纯代码修复 | 0 | 0 | 0 | 0 | 0 |
| 简单 Story | 1 | 1 | 0/1 | 1 | 1 |
| 多人物 Episode | 1 | 1 强化 | 1 | 1 | 1 |
| 世界观复杂 | 1 | 1 | 1 强化 | 1 | 1 |
| 视觉高难 | 1 | 1 | 1 | 1 强化 | 1 强化 |
| Release only | 0 | 0 | 0 | 0 | 1 |

## 10.2 Agent Activation Policy

```text
DAG Node requires agent
AND
required capability is available
AND
authority input is frozen
AND
resource slot available
→ dispatch

otherwise
→ deterministic wait / route / fallback
```

---

# 11. 并发策略

## 11.1 推荐资源槽

不以线程数作为业务容量，使用资源槽：

```text
episode_slots
reasoning_slots
review_slots
image_slots
host_action_slots
diagnostic_slots
```

初始建议：

```yaml
agent_runtime:
  reasoning_slots: 3
  review_slots: 2
  diagnostic_slots: 1
```

这不是硬编码最终值，只是 Phase 1 默认。

## 11.2 同 Authority 写冲突

同一个 Authority Scope：

```text
character/*
world/*
story/*
visual/*
```

同一时刻只能有一个 Reducer Commit。

Candidate 可并行，Commit 不可并行。

---

# 12. Context Capsule

避免每个 Agent 重复读取整个仓库。

每个 Task 由 Supervisor 生成 Input Capsule：

```json
{
  "episode_id": "...",
  "task_type": "CHARACTER_PREPARE",
  "authority_snapshot": {},
  "required_documents": [],
  "derived_summary": {},
  "constraints": {},
  "output_schema": {},
  "write_scope": []
}
```

目标：

- 降低重复文件读取；
- 降 token；
- 降上下文漂移；
- 提高 deterministic reproducibility。

---

# 13. 实施阶段

## Phase 0：协议冻结

目标：不改变当前生产行为，只定义协议。

实施：

- AgentExecutionContract；
- AgentType enum；
- OrchestrationMode enum；
- CapabilityRequirement；
- Candidate Envelope；
- Reducer Contract；
- Reflection Policy；
- Guardian Event Contract。

验收：

- 现有 Episode 路径行为 100% 不变；
- 新字段均为 backward-compatible；
- 未注册 Agent 时继续当前 Runtime。

## Phase 1：Character SubAgent

目标：把当前 PREIMAGE `CHARACTER_FINALIZE` 正式化为 Character Agent。

实施：

- CharacterAgent adapter；
- 可选 three-view anchor；
- Character input capsule；
- Character candidate schema；
- existing PREIMAGE verifier 复用；
- existing authority commit 复用。

验收：

- 无三视图：输出与旧流程语义等价；
- 有三视图：Character Visual Contract 绑定三视图 SHA；
- Pixel Master 生成后优先级高于三视图；
- stale 三视图能触发 Character Visual stale；
- Character Agent 不能写 story-gates / episode-state。

## Phase 2：World + Visual Director Agent

目标：把 PREIMAGE 四任务正式挂到 Agent Protocol。

实施：

- World Agent；
- Visual Director Agent；
- Environment 可以继续 deterministic + Agent candidate 混合；
- PREIMAGE Supervisor；
- Parallel Dispatch；
- Reducer atomic commit。

验收：

- 四 Candidate peak concurrency > 1；
- 任何单 Agent 失败无 partial authority commit；
- snapshot drift → STALE；
- barrier 仅在全 required Candidate PASS 后 READY。

## Phase 3：Critic / Reflection Protocol

目标：统一 Review 和 bounded reflection。

实施：

- Critic Agent protocol；
- fresh isolated reviewer；
- issue_codes；
- repair routing；
- max reflection rounds；
- review cost telemetry。

验收：

- reviewer 不可写 source；
- attempt 1 fail → targeted repair；
- attempt 2 fail → NEEDS_USER / BLOCK；
- 不存在无限 review loop；
- technical retry 不消耗 reflection budget。

## Phase 4：Capability Router

目标：任务级选择 WORK / WebCodex / CODEX / local tool。

实施：

- executor registry；
- capability matching；
- availability probe；
- fallback；
- capacity-aware route；
- reason evidence。

验收：

- WebCodex available → WORK；
- WebCodex unavailable + Codex available → CODEX；
- explicit runtime override wins；
- fallback 不改变 write permission；
- route decision 可审计。

## Phase 5：Runtime Guardian

目标：卡点自动发现和技术修复。

实施：

- heartbeat；
- queue age；
- stale lease；
- network error；
- MySQL error；
- retry-tech；
- invalid transition；
- authority stale；
- periodic reconcile。

验收：

- Guardian 本身不占 reasoning slot；
- 可恢复技术故障自动修复；
- 内容失败不得 technical retry；
- 不能自动 force-pass；
- Guardian action 全部写 trace/evidence。

## Phase 6：Episode Supervisor

目标：形成统一 orchestration entrypoint。

Supervisor 消费：

- Runtime DAG；
- Agent Registry；
- Capability Router；
- Resource Manager；
- Checkpoint；
- Guardian；
- Reducer。

验收：

- 不新增 Episode State；
- 不新增 Production Queue；
- 不改变 single writer；
- resume 可从 checkpoint 重建 runnable set。

---

# 14. 测试方案

## 14.1 Unit Tests

### Agent Contract

- invalid write scope rejected；
- missing snapshot rejected；
- invalid candidate schema rejected；
- unsupported orchestration mode rejected。

### Router

- capability match；
- unavailable executor excluded；
- explicit override；
- WebCodex → Codex fallback；
- no executor → BLOCKED；
- permission never escalates。

### Character Agent

- three-view absent；
- three-view present；
- stale SHA；
- wrong character id；
- pixel master supersedes three-view；
- multi-character references。

### Reflection

- attempt count；
- targeted repair；
- technical retry independence；
- hard stop；
- issue_codes required。

### Guardian

- network retry；
- stale job；
- invalid state；
- stale authority；
- exhausted budget；
- deadlock timeout。

## 14.2 Integration Tests

### I1：PREIMAGE Parallel

```text
Story Lock
→ 4 Candidate Tasks
→ parallel
→ verify
→ barrier
→ atomic commit
```

断言：

- peak > 1；
- one failure ≠ partial commit；
- stale snapshot blocks commit。

### I2：Character Three-View

```text
three-view
→ Character Agent
→ Character Visual
→ Frame Contract
→ Visual Lock baseline
→ Pixel Master
```

断言：

- baseline 前用 three-view；
- baseline 后 Pixel Master 接管；
- 未提供 three-view 时旧路径不变。

### I3：Reflection

注入一个 Story Semantic fail：

```text
attempt 1 fail
→ repair
→ attempt 2 pass
```

另一个：

```text
attempt 1 fail
→ repair
→ attempt 2 fail
→ NEEDS_USER
```

### I4：Router Fallback

```text
WebCodex on  → WORK
WebCodex off + Codex on → CODEX
both off → BLOCK
explicit WORK → WORK
```

### I5：Guardian Recovery

注入：

- provider network failure；
- MySQL transient failure；
- queue item running timeout；
- stale lease。

要求：

- technical recovery；
- no duplicated authority；
- no extra content repair consumed。

---

# 15. End-to-End 测试

至少使用 3 类 Episode：

## E2E-A：无三视图简单 Episode

目的：

- backward compatibility。

验收：

- 与改造前相同 Story → PREIMAGE → Visual 路径；
- 不创建 three-view gate；
- 不增加额外 mandatory Agent。

## E2E-B：三视图多人物 Episode

目的：

- Character Agent；
- three-view；
- multi-character identity；
- Pixel Master takeover。

验收：

- 三视图在 baseline 前被实际引用；
- Pixel Master 后停止以三视图作为主参考；
- reference slot 不因三张视图耗尽。

## E2E-C：高复杂世界 Episode

目的：

- World / Character / Visual 并行；
- Critic；
- Guardian；
- fallback。

验收：

- PREIMAGE peak concurrency > 1；
- 无 partial authority；
- injected WebCodex loss 后 Codex 继续；
- Guardian 能恢复一个 technical failure。

---

# 16. 性能测试

必须使用现有 Performance Ledger。

采集：

- wall time；
- resource time；
- agent task time；
- wait time；
- routing latency；
- reducer latency；
- reflection time；
- token / model usage；
- retry count；
- agent activation count。

## 16.1 性能验收目标

第一阶段不是追求绝对极限，而是证明“多 Agent 没把系统变慢”。

建议门槛：

| 指标 | 验收 |
|---|---:|
| PREIMAGE wall time | 相比串行下降 ≥ 30% |
| 并行资源效率 | ≥ 70% |
| Router p95 | < 100ms（纯 deterministic route） |
| Reducer commit | < 2s（不含外部模型） |
| 无三视图路径额外 wall overhead | < 3% |
| 无三视图额外模型调用 | 0 |
| 简单 Episode Agent 激活数 | ≤ 3 个创作 Agent |
| Reflection 自动轮数 | ≤ 2 |
| Guardian 常驻模型调用 | 0 |

性能不达标时，Agent 数量不允许继续增加。

---

# 17. 质量验收

多模式 / Agent 改造不是只测“能跑”。

质量要求：

1. Character consistency 不下降；
2. Story Semantic pass rate 不下降；
3. Review false-pass 不增加；
4. stale authority 不能被 commit；
5. forced-pass 数量不能增加；
6. 无三视图 Episode 质量不得回退；
7. 三视图 Episode 的身份漂移率应明显低于无三视图 baseline。

建议新指标：

```text
character_identity_drift_rate
agent_candidate_reject_rate
reflection_repair_success_rate
authority_conflict_rate
router_fallback_rate
guardian_auto_recovery_rate
```

---

# 18. 安全与权限验收

必须通过：

- Agent 无权直接 transition Episode State；
- Agent 无权直接修改 PASS Gate；
- Agent 无权写其它 Agent 的 Candidate；
- Critic 无权修改创作 source；
- Supervisor 无权绕过 Reducer；
- Router 无权提升 write scope；
- Guardian 无权 force-pass；
- Codex fallback 不提升 Authority。

任何一项失败，本方案不得上线。

---

# 19. 故障注入验收

必须主动注入：

1. WebCodex 消失；
2. Codex 不可用；
3. MySQL timeout；
4. Candidate schema invalid；
5. Authority Snapshot stale；
6. Agent timeout；
7. Agent crash；
8. Reviewer fail；
9. Reducer conflict；
10. Guardian stale-job recovery；
11. 两 Agent 试图写同一 scope；
12. Pixel Master 在三视图之后生成。

要求：

- 可解释；
- 可恢复；
- 不产生 silent partial state；
- 不污染 Episode State；
- 有 Event / Trace / Evidence。

---

# 20. 可观测性

新增 Trace 字段：

```text
orchestration_mode
supervisor_id
agent_type
agent_execution_id
candidate_id
authority_snapshot_sha
router_reason
executor
fallback_active
reflection_round
reducer_commit_id
guardian_action
```

Dashboard 最少提供：

- Agent running / waiting / blocked；
- 各模式占比；
- Agent duration；
- Agent token usage；
- Router fallback；
- Reflection rounds；
- Candidate reject；
- Reducer conflict；
- Guardian recoveries。

---

# 21. 回滚方案

每 Phase 必须可独立关闭。

建议 feature flags：

```yaml
agent_runtime:
  multi_mode_enabled: false
  specialized_agents_enabled: false
  character_agent_enabled: false
  world_agent_enabled: false
  visual_director_agent_enabled: false
  critic_agent_protocol_enabled: false
  capability_router_v2_enabled: false
  guardian_v2_enabled: false
```

关闭后：

- 继续现有 Runtime DAG；
- PREIMAGE 回到现有 Host Task；
- Character Three-View 仍可作为普通 deterministic Authority 输入；
- 不影响 Episode State；
- 不要求数据迁移才能回滚。

---

# 22. 代码落点建议

第一阶段建议新增：

```text
episodes/_system/agent_execution_contract.py
episodes/_system/agent_registry.py
episodes/_system/capability_router.py
episodes/_system/episode_supervisor.py
episodes/_system/preimage_supervisor.py
episodes/_system/authority_reducer.py
episodes/_system/reflection_policy.py
episodes/_system/runtime_guardian.py
episodes/_system/agents/
    character_agent.py
    story_agent.py
    world_agent.py
    visual_director_agent.py
    critic_agent.py
```

优先复用：

```text
runtime_dag.py
runtime_router.py
authority_commit.py
preimage_protocol.py
preimage_task_contract.py
frame_contract.py
scheduler_core.py
runtime_checkpoint.py
runtime_observability.py
production_ledger.py
character_three_view.py
```

---

# 23. 实施顺序

推荐顺序：

```text
P0
Agent Contract
→ Character Agent
→ PREIMAGE Supervisor
→ Authority Reducer wrapper

P1
World Agent
→ Visual Director Agent
→ Critic Protocol
→ Bounded Reflection

P2
Capability Router V2
→ Dynamic Agent Activation
→ Runtime Guardian

P3
Episode Supervisor
→ Performance tuning
→ 多 Episode coordination
```

不要反过来先写一个“大 Supervisor”。

---

# 24. 总体验收 Gate

只有同时满足以下条件，才认为“多模式 + 子 Agent”改造完成：

## Functional

- [ ] Chain / Parallel / Router / Reflection / Hierarchical 五种模式均有至少一个真实生产路径；
- [ ] Character Agent 正式接管 PREIMAGE Character Finalize；
- [ ] 三视图可选路径可用；
- [ ] 无三视图旧路径 100% 可用；
- [ ] Pixel Master 能覆盖三视图；
- [ ] Critic fresh isolation；
- [ ] Runtime fallback 有效；
- [ ] Guardian 有技术恢复闭环。

## Authority

- [ ] Candidate-only；
- [ ] Snapshot；
- [ ] Barrier；
- [ ] Reducer；
- [ ] Atomic Commit；
- [ ] Single Writer；
- [ ] stale fail-closed。

## Performance

- [ ] PREIMAGE ≥ 30% wall-time improvement；
- [ ] 并行效率 ≥ 70%；
- [ ] 无三视图 overhead < 3%；
- [ ] Guardian 常驻 LLM 调用 = 0；
- [ ] Reflection ≤ 2 rounds。

## Regression

- [ ] Runtime tests green；
- [ ] Storage tests green；
- [ ] PREIMAGE tests green；
- [ ] Character tests green；
- [ ] Frame Contract tests green；
- [ ] Recovery tests green；
- [ ] Visual Lock tests green；
- [ ] Release tests green。

## E2E

- [ ] E2E-A 无三视图；
- [ ] E2E-B 三视图多人物；
- [ ] E2E-C 复杂世界 + fallback + failure injection；
- [ ] 至少一个全新 Episode 从 IDEA 到 PUBLISH_READY。

---

# 25. Go / No-Go 决策

## GO

满足：

- P0 / P1 全部 acceptance；
- Authority zero regression；
- 无三视图路径零强制新增模型调用；
- 性能没有负收益；
- E2E-A/B 通过。

## CONDITIONAL GO

- 功能通过；
- 性能改善 < 30% 但无明显退化；
- 允许先小流量 / shadow。

## NO-GO

任一：

- Agent 可直接改 Canonical State；
- 出现 partial authority commit；
- stale Candidate 可 commit；
- Agent 数增加导致 wall time 明显上升；
- simple Episode 被强制启动全部 Agent；
- Reflection 出现无界循环；
- Guardian 需要常驻模型；
- fallback 导致权限升级。

---

# 26. 本方案核心结论

StoryOS 下一阶段不应演化为：

```text
很多 Agent
+ 自由对话
+ 自主写状态
```

而应演化为：

```text
Deterministic Runtime
+ Multi-Mode Orchestration
+ Specialized SubAgents
+ Candidate-only Execution
+ Single-Writer Reducer
+ Bounded Reflection
+ Capability Router
+ Deterministic Guardian
```

子 Agent 的价值不是“看起来更智能”，而是：

- 更明确的专业边界；
- 更小的 Context；
- 更高的可并行度；
- 更低的相互污染；
- 更清楚的测试面；
- 更容易做性能治理。

最终判据只有一个：

> **如果新增 Agent 不能在保持 Authority 安全的前提下，提高速度、质量或可恢复性，就不应该新增这个 Agent。**
