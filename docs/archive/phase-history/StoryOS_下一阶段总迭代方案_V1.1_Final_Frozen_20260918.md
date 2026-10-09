# StoryOS 下一阶段总迭代方案 V1.1 Final / Frozen

更新时间：2026-09-18  
适用分支：story-platform-v3  
状态：**FINAL / DEEP REVIEWED / FROZEN ITERATION BASELINE**  
替代：StoryOS_下一阶段总迭代方案_V1.0_Final_20260918.md

---

# 0. 最终结论

这次深度评审把当前 StoryOS 的下一阶段路线重新按“真实工作区正在发生什么”排了一遍。

最终顺序冻结为：

~~~text
当前 Persistence / MySQL / Redis Authority 收口
        ↓
冻结可复现 Production Profile
        ↓
3 篇真实 Episode 建立 Production SLO
        ↓
只修 measured bottleneck
        ↓
Narrative Fixture Harness
        ↓
StoryFact-lite / Disclosure / Frame Purpose
        ↓
Narrative Shadow + Golden Regression
        ↓
Runtime Coordinator Shadow
        ↓
Single Episode Durable Dispatch
        ↓
Multi Episode Resource-aware Scheduling
        ↓
Retrieval Offline Evaluation
        ↓
Retrieval Runtime Advisory
~~~

下一阶段不是 V4 大重构，也不是第二次平台化。

必须保护：

1. Production Kernel；
2. Existing Resolved Frame Contract；
3. Production Ledger；
4. scheduler_core 的 per-Episode Production Queue；
5. Runtime DAG / Resident Driver；
6. 已经形成的 SHA / Evidence / Dirty / Recovery 体系。

---

# 1. 本次深度评审发现并已修正的问题

## 1.1 Storage Authority 不能继续排在远期 P2

当前工作区正在实际推进：

- MySQL V2 repository；
- Episode / Runtime Request / Frame Contract / Review / Approval / Release persistence；
- Production Ledger persistence projection；
- Redis hot-state authority；
- MySQL authority no-file-fallback；
- Redis authority no-file-fallback。

本轮聚焦验证：

~~~text
32 passed
~~~

覆盖：

- MySQL authority 不读 stale JSON fallback；
- Redis authority 不读 compatibility file fallback；
- Episode State MySQL authority；
- Runtime Request MySQL authority；
- Runtime Checkpoint MySQL authority；
- Production Ledger persistence。

但当前默认配置仍是：

~~~yaml
storage:
  episode_meta_store:
    mode: json

  hot_state:
    mode: file
~~~

因此真实状态是：

> Authority Cutover 能力正在收口，但 production default 尚未切换。

所以正式 Production SLO 之前，必须先冻结实际运行的 Storage Profile。

---

## 1.2 原方案“直接跑 3 篇 Episode”顺序不严谨

如果 MySQL/Redis Authority 在 SLO 之后继续切换：

~~~text
旧 SLO
≠
切换后的真实生产路径
~~~

所以正确前置是：

~~~text
Authority Closure
→ Production Profile Freeze
→ SLO
~~~

---

## 1.3 Runtime Coordinator 不能被简化成“多 Episode Queue”

已有正式设计：

docs/architecture/Story_OS_全局调度与Agent运行时最终优化方案_V1.0_20260918.md

冻结模型是：

~~~text
Logical Single Coordinator

+ Episode Registry
+ Durable Dispatch State
+ Capacity Manager
+ Lease / Heartbeat
+ Dispatch / Reconcile
+ Event-driven Wakeup
+ Periodic Reconcile
~~~

必须严格区分：

~~~text
Global Dispatch State
        ≠
Per-Episode Production Queue
~~~

Per-Episode Production Queue 继续由 Production Kernel / scheduler_core 单写。

Coordinator 只决定：

- 哪个 Episode 应运行；
- 什么时候运行；
- 还能运行几个；
- 分配什么资源；
- stale / blocked 后如何 reconcile。

不得新建第二套 Production Queue。

---

## 1.4 Narrative Fixture Harness 必须早于 Narrative 实现

正确顺序冻结：

~~~text
Fixture Loader
→ Schema Validation
→ StoryFact-lite
→ Disclosure
→ Frame Purpose
→ Frame Contract Hash
→ Shadow
~~~

不能先改 Narrative Contract，再补回归资产。

---

## 1.5 StoryFact 状态和 Disclosure 必须彻底分轴

冻结：

~~~text
StoryFact Status
≠
Audience Disclosure
≠
Character Knowledge
~~~

StoryFact：

~~~text
CONFIRMED
UNKNOWN
UNDECIDED
~~~

其中 UNKNOWN 表示：

> Story Canon / 作者侧当前没有可确认事实值。

如果作者已确认，但当前不能让观众知道：

~~~text
Fact = CONFIRMED
must_not_reveal = Fact ID
~~~

不得写成 UNKNOWN。

该语义已同步修正 VNext Frozen 文档。

---

## 1.6 Review 优化必须从“设计驱动”切换成“测量驱动”

当前已经有：

- W-103 Candidate-aware PATCH；
- W-104 FULL Review 4 shard；
- W-105 ACTIVE / HOST_WAIT / USER_WAIT / IDLE。

代码和测试层已经闭环。

现在缺的是：

> 新 Episode 的真实 wall-time。

所以之后只有 Production SLO 证明 Review 仍不达标，才继续修改 Review。

禁止继续拿 Mock / Replay target 当生产成绩。

---

## 1.7 Narrative QA 不能重新制造 Review Amplification

首版 Narrative QA 必须优先：

1. deterministic validation；
2. 复用现有 actual-pixel Reviewer；
3. 复用现有 FULL / PATCH review prompt；
4. 只增加结构化字段。

禁止默认变成：

~~~text
20 Frames
×
1 个额外 Narrative Vision Call
~~~

否则 Narrative 质量提升会直接被性能回退抵消。

Narrative QA 验收必须同时记录：

~~~text
quality delta
+
review wall delta
+
model-call delta
~~~

---

## 1.8 原“人天估算”不再作为冻结约束

StoryOS 当前同时存在：

- Agent 并发；
- Provider 长 wall；
- 大规模 staged persistence 改造；
- Episode 实产等待；
- 多条独立写入域。

传统固定人天会制造伪精确。

本版改成：

> Entry Gate + Exit Gate + Evidence 驱动。

真正进入 Sprint 时再按当时工作区估算。

---

# 2. 当前真实系统定位

正式架构继续是：

~~~text
V2.x Production Kernel
        +
V3 Platform Control Plane
        +
Runtime Workspace
        +
MySQL / Redis Persistence & Hot State Adapter
~~~

## 2.1 Production Kernel

继续拥有：

- Episode lifecycle；
- Story / Character / World / Visual / Frame Contract；
- Gate / Evidence；
- Production Ledger；
- Production Queue；
- Runtime DAG；
- Image Scheduler；
- Review / Repair / Release。

## 2.2 Platform

负责：

- Event / Trace / Artifact；
- RuntimeStatus；
- Workflow / Agent；
- Experience / Memory；
- Repository；
- Console；
- 后续 Global Runtime Coordinator。

## 2.3 MySQL / Redis

它们是：

> Existing Authority 的持久化 / Hot State 实现。

它们不是：

> 第二套 Production Authority。

---

# 3. 冻结架构不变量

## 3.1 Single Authority

同一业务事实只能存在一个正式 writer。

## 3.2 Single Frame Authority

不得新增：

- ShotContract；
- NarrativeFrameContract；
- 第二 Prompt Authority。

Narrative 只能增强 Existing Resolved Frame Contract。

## 3.3 Single Production Queue per Episode

Coordinator 不得建立新的 Episode Production Queue。

## 3.4 Reviewer Is Evidence, Not Canon

Reviewer 可以：

- 观察；
- 判定；
- 报 issue。

Reviewer 不能反向创造 Story Fact。

## 3.5 Hard Truth > Soft Experience

~~~text
Story Lock
StoryFact
Frame Contract
        >
Memory
Experience
Retrieval
RAG
~~~

## 3.6 Platform 不重写 Kernel

Platform 负责：

- observe；
- dispatch；
- capacity；
- pause / resume / retry command。

Kernel 继续负责生产事实和成片规则。

---

# 4. 总阶段依赖

~~~text
F0  Storage / Authority Closure
        ↓
F1  Production Profile Freeze
        ↓
F2  3-Episode Production SLO
        ↓
F3  Conditional Performance Closure
        │
        └── 若改生产路径 → 回到 F1 / F2 重新冻结并重测

F2/G1 通过后分三条受控支线：

Narrative Track
N0 Fixture Harness
 → N1 Narrative P0
 → N2 Shadow / Canary
 → N3 Narrative P1 + Golden

Coordinator Track
C1 Shadow Coordinator
 → C2 Single Episode Durable Dispatch
 → C3 Multi Episode Capacity

Retrieval Track
N3 / Experience 数据稳定
 → R1 Offline Evaluation
 → R2 Runtime Advisory
~~~

允许并行：

- C1 只读 Shadow 可与 N1 / N2 并行；
- R1 不依赖 C3；只要 Golden / Experience 数据稳定即可离线启动。

禁止并行越权：

- C2/C3 不得抢在稳定 Production Baseline 前主动 dispatch；
- R2 不得抢在 R1 offline evaluation 前进入 runtime。

---

# 5. F0：Storage / Authority Closure

优先级：**当前第一优先级**

这不是远期规划，而是当前真实工作区正在做的事情。

## 5.1 Authority Matrix

每类数据必须明确：

~~~text
Owner / Writer
Reader
Projection
Compatibility Path
Current Mode
Target Mode
Rollback Path
~~~

至少覆盖：

- Episode State；
- Runtime Request；
- Runtime Checkpoint；
- Frame Contract；
- Frame Review；
- Runtime Review；
- Approval；
- Release；
- Provider Receipt；
- Production Ledger；
- Production Queue；
- Runner State；
- Next Action；
- Driver / Beacon；
- Host Request Hot Pointer。

## 5.2 MySQL Authority Gate

进入 mysql authority 后：

- stale JSON 不能静默 fallback；
- DB unavailable 必须 fail-closed；
- missing row 视为 authority missing；
- migration / read-back / checksum 可验证。

## 5.3 Redis Authority Gate

进入 redis authority 后：

- hot state 不得偷读旧文件恢复事实；
- missing key 必须显式 authority missing / rebuildable；
- 可重建数据和不可重建数据要分开；
- recovery 必须证明不会形成双 owner。

## 5.4 当前测试事实

本轮 focused authority：

~~~text
32 passed
~~~

但正式 F0 退出不能只靠 focused tests。

还必须：

- tests/platform full；
- tests/system full；
- recovery focused；
- full-auto entry focused；
- storage cutover / rollback evidence。

## 5.5 F0 Exit

必须同时存在：

- baseline commit SHA；
- storage mode；
- hot-state mode；
- config SHA；
- authority matrix；
- full regression；
- rollback evidence；
- unresolved authority gap = 0。

如果本轮决定**暂不把 production default 切到 mysql/redis**，也允许退出 F0，但必须同时满足：

- 明确冻结 json/file 为本轮 Production Profile；
- MySQL/Redis cutover 标记为 DEFERRED，而不是“半切换”；
- SLO 期间禁止继续修改会改变正式读写路径的 Authority 行为。

如果本轮决定切到 mysql/redis，则必须先完成 disposable Episode canary、真实读写验证和 rollback drill，再进入 F1。

---

# 6. F1：Production Profile Freeze

F1 不开发新功能。

它负责给所有后续性能结论绑定稳定环境。

每一轮 Production Benchmark 必须记录：

~~~text
git commit SHA
config SHA
storage profile
hot-state profile
provider
image model
review model / runtime
image concurrency
review concurrency
Runtime / Agent version
frame count
start timestamp
end timestamp
~~~

没有完整 Provenance：

> 不进入正式 SLO。

---

# 7. F2：3-Episode Production SLO

优先级：**P0**

## 7.1 Cohort Rule

3 篇必须：

- 全新；
- 标准 20 Frame；
- 同一 commit；
- 同一 Production Profile；
- 同一主要 provider / model policy。

## 7.2 Episode A

允许发现：

- metrics 缺失；
- tracing 缺失；
- wall attribution 错误。

只允许修改观测代码。

如果修改了生产业务逻辑：

> Cohort 重新开始。

## 7.3 Episode B / C

禁止：

- 边跑边改代码；
- 手工改 Queue；
- 手工改 Ledger；
- 手工补 Gate；
- 临时换并发策略；
- 临时换 model policy。

必须：

~~~text
create --full-auto
→
PUBLISH_READY
~~~

## 7.4 指标

必须自动产出：

- E2E wall；
- ACTIVE wall；
- HOST_WAIT；
- USER_WAIT；
- IDLE；
- image wall；
- image resource；
- image P50/P90；
- requested/succeeded/failed；
- max image inflight；
- review wall；
- FULL calls；
- PATCH calls；
- reviewed frame count；
- max review inflight；
- repair rounds；
- first-pass yield；
- WEAK_PASS count；
- manual intervention；
- PUBLISH_READY。

## 7.5 输出分层

所有性能报告必须严格区分：

~~~text
Measured Baseline
Target
Budget
~~~

禁止把 95 分钟、10～12 分钟等 Target 写成实测。

## 7.6 统计边界

3 篇 Episode 只能形成：

> Production Baseline V1 / Operational SLO Baseline。

它不足以形成稳定的 Episode-level P90/P95 统计承诺。

第一版可以报告：

- 三篇逐篇 E2E；
- median / range；
- image attempt 级 P50/P90；
- review call 级分布。

当累计达到至少 10 篇代表性 Episode 或形成稳定滚动窗口后，再升级为成熟 SLO 分布。

---

# 8. F3：Conditional Performance Closure

这一阶段不是固定开发项。

只由 F2 measured bottleneck 触发。

## 8.1 Review 仍是瓶颈时

检查：

- W-104 shard 是否真实并发；
- Global Closure 是否变成长尾；
- Host capacity；
- shard imbalance；
- duplicate FULL；
- PATCH fallback reason；
- dirty-root 范围是否错误放大。

## 8.2 Image 重新成为瓶颈时

检查：

- Provider latency；
- inflight；
- throttling；
- technical retry amplification。

## 8.3 规则

> 没有 measured bottleneck，不进入性能改造 backlog。

如果 F3 修改了任何会影响执行时序、并发、Review 或 Provider 调用的生产逻辑：

~~~text
旧 F2 = pre-optimization baseline
新代码 = 新 Production Profile
        ↓
必须重新执行 F1
        ↓
至少重新完成有效 B/C 无代码变更样本
~~~

不能拿修改前的 SLO 作为修改后的正式成绩。

---

# 9. N0：Narrative Fixture Harness

优先级：**Narrative 第一项**

当前已有 25 条：

- Plot；
- Caption；
- Visual Evidence；
- Transition；
- Continuity；
- Reference。

N0 负责：

- Fixture loader；
- schema validation；
- positive / negative / boundary；
- frozen expected；
- provenance；
- design-only 标识；
- deterministic result comparison。

N0 不修改 Production。

---

# 10. N1：Narrative Semantics P0

严格遵循：

StoryOS_VNext_叙事语义增强落地方案_V1.1_Final_Frozen_20260918.md

只做三项。

## 10.1 StoryFact-lite

~~~text
CONFIRMED
UNKNOWN
UNDECIDED
~~~

UNKNOWN = Canon 尚无已确认事实。

## 10.2 Disclosure Boundary

~~~yaml
allowed_to_know:
must_not_reveal:
supports_fact_ids:
~~~

## 10.3 Frame Purpose / Local Exception

~~~yaml
frame_purpose:
local_exceptions:
  - rule:
    action:
    reason:
~~~

## 10.4 Existing Frame Contract Integration

新语义必须进入：

- contract hash material；
- prompt context；
- review context；
- dirty fingerprint。

不得新建第二 Frame Authority。

---

# 11. N2：Narrative Shadow / Real Canary

第一阶段：

~~~text
REPORT ONLY
~~~

不阻断 Production。

## 11.1 性能保护

首版优先：

1. deterministic check；
2. existing reviewer context；
3. existing FULL / PATCH call。

禁止默认新增 per-frame Vision call。

## 11.2 必测

- detected issue；
- false positive；
- false negative；
- fixture agreement；
- review wall delta；
- model call delta；
- token delta。

## 11.3 Real Canary

至少覆盖：

- 成功型 Episode；
- 边界型 Episode；
- 一个历史负例 replay / 同类场景。

---

# 12. N3：Narrative P1 + Golden Regression

只有 N2 数据证明收益后进入。

## 12.1 Reference Semantics

只增加：

~~~text
inherit
ignore
authority
~~~

required anchor execution / receipt / SHA 全部复用。

## 12.2 Transition Assertion

只覆盖：

- recorder；
- device handoff；
- location；
- time；
- key prop state。

不建 Transition Service。

## 12.3 Caption Semantic Metadata

只补：

- role；
- supports；
- must_not_reveal。

## 12.4 Dependency Propagation

接入现有：

- SHA；
- source binding；
- dirty admission；
- stale detection。

## 12.5 Golden Registry

第一版至少：

- 1 个成功完整 Episode；
- 1 个边界完整 Episode。

历史失败主要作为 Fixture / Replay，不强行当“Golden 成片”。

---

# 13. C1：Runtime Coordinator Shadow

依据：

Story_OS_全局调度与Agent运行时最终优化方案_V1.0_20260918.md

只从 S1 Shadow 开始。

实现：

- Episode Registry；
- Discover；
- Scheduling Policy；
- Capacity Snapshot；
- Dispatch Plan；
- stale reconcile plan。

但是：

> 不实际启动 Episode。

C1 可与 Narrative N1/N2 并行，因为只读。

---

# 14. C2：Single Episode Durable Dispatch

对应 Coordinator S2。

第一步固定：

~~~text
max_active = 1
~~~

验证：

- Lease；
- Heartbeat；
- Duplicate Dispatch Prevention；
- Restart Recovery；
- Completion；
- Human Required；
- Blocked；
- Retry。

通过以后才能 Multi Episode。

---

# 15. C3：Multi Episode Capacity

只有 C2 通过才允许：

~~~text
max_active > 1
~~~

然后增加：

- Image Capacity；
- Agent Reasoning Capacity；
- Review Capacity；
- Host Action Capacity；
- Backpressure。

必须保持：

~~~text
Coordinator Global Dispatch State
        ≠
scheduler_core Per-Episode Production Queue
~~~

---

# 16. R1：Retrieval Offline Evaluation

Query Rewrite / Knowledge Router / Hybrid Retrieval / Rerank 已有设计，但 Runtime 接入继续 Deferred。

第一阶段只做 Offline。

## 16.1 数据集来源

优先：

- W-17；
- TECH_FAILED；
- Reference；
- Caption / Disclosure；
- Production Performance；
- Similar Episode；
- Experience Store。

## 16.2 指标

- Precision@K；
- Recall@K；
- MRR / NDCG；
- Correct Source Rate；
- Unsupported Context Rate；
- Context Redundancy；
- Retrieval Latency；
- Grounded Rate。

没有 Offline Evaluation：

> 不进入 Runtime。

---

# 17. R2：Retrieval Runtime Advisory

只有 R1 达标后：

~~~text
Query Planner
→ Knowledge Router
→ Structured Filter
→ Hybrid Retrieval
→ Rerank
→ Context Builder
→ Agent Advisory
~~~

第一版：

~~~text
advisory_only = true
blocks_production = false
~~~

不得覆盖 Canonical Contract。

---

# 18. Go / No-Go Gates

## G0 Storage Ready

必须：

- authority gap = 0；
- Platform full green；
- System full green；
- recovery / rollback evidence；
- production profile frozen。

否则：

**禁止正式 SLO。**

## G1 Production Baseline Accepted

必须：

- 有效 3-Episode cohort；
- B/C 无代码修改；
- provenance 完整；
- PUBLISH_READY；
- Review / Image / Wait 指标完整。

否则：

**禁止宣称稳定 Production SLO。**

## G2 Narrative Shadow Accepted

必须：

- 25 Fixture harness green；
- positive fixture 100% 不被误判为 FAIL；
- negative fixture 100% 符合 frozen expected；
- boundary fixture 100% 不被误判为 hard FAIL；
- real canary false positive 可接受；
- 不能因为开启 Narrative Shadow 新增默认 per-frame external Vision call；
- review wall / model call / token delta 已有对比证据。

否则：

**禁止 Hard Gate。**

## G3 Narrative Production Ready

必须：

- Reference / Transition / Caption P1；
- dependency propagation；
- 至少 2 个 Golden Episode；
- Shadow → Warning → Canary；
- Hard Gate 明确批准。

## G4 Coordinator Shadow Accepted

必须：

- Shadow 与真实 Runtime 行为对账一致；
- 不产生 Production Authority 写入；
- 不产生重复 owner；
- 不产生非法 dispatch plan；
- no second Production Queue。

通过 G4 后才允许进入 C2 主动 Single Episode Dispatch。

## G5 Single Episode Coordinator Accepted

必须：

- C2 单 Episode durable dispatch 稳定；
- lease / heartbeat；
- restart recovery；
- duplicate dispatch prevention；
- Human Required / Blocked / Completion 语义正确；
- 与现有 Resident Driver / Episode Runner 无双 owner。

通过 G5 后才允许 max_active > 1。

## G6 Multi Episode Ready

必须：

- G5 已通过；
- resource metrics 完整；
- 一个 blocked Episode 不拖住其他 Episode；
- single-writer authority 无冲突。

---

# 19. 当前工作区与提交边界

当前工作区存在：

- 大量 Episode 历史删除 / 归档变化；
- 大量 staged persistence 代码；
- 新 persistence / authority tests；
- Narrative docs / Fixture；
- Global Coordinator design；
- 其他并行变更。

后续必须分 Domain。

## Domain A

Persistence / Authority。

## Domain B

Narrative docs / Fixture。

## Domain C

Narrative runtime implementation。

## Domain D

Runtime Coordinator。

## Domain E

Retrieval Intelligence。

禁止：

~~~text
git add .
~~~

禁止把历史 Episode runtime assets 顺手带进源码提交。

---

# 20. 本轮明确 Deferred

- RenderObservation；
- Story Knowledge Graph；
- Graph Database；
- Narrative Platform；
- 第二 ShotContract；
- Transition Service；
- Evidence Platform；
- 第二 Reference Execution Evidence；
- 新 Production Kernel；
- 第二 per-Episode Production Queue；
- Temporal / LangGraph 等强 Runtime 依赖；
- Retrieval Hard Gate；
- Phase10 SaaS。

---

# 21. 最终里程碑

## M0：Authority Stable

完成：

- Persistence / Hot State 收口；
- Production Profile Freeze；
- Full Regression；
- Recovery / Rollback Evidence。

## M1：Measured Production

完成：

- 3 篇有效 Episode；
- E2E / Active / Image / Review / Wait Baseline；
- measured bottleneck 排名；
- current Full Auto 无人值守能力有真实结论。

## M2：Narrative Shadow

完成：

- Fixture Harness；
- StoryFact / Disclosure / Purpose；
- Existing Frame Contract integration；
- Real Canary；
- review wall delta 可接受。

## M3：Narrative QA Production Ready

完成：

- Reference / Transition / Caption；
- Dependency Propagation；
- 至少 2 个 Golden Episode；
- false-positive evidence；
- controlled gate activation。

## M4：Coordinator Production Ready

完成：

- Shadow；
- Single Episode Durable Dispatch；
- Multi Episode Resource-aware Dispatch；
- Recovery drill；
- no second Production Queue。

## M5：Retrieval Intelligence Ready

完成：

- Offline Dataset；
- Retrieval Metrics；
- Runtime Advisory；
- Canonical Contract 不被覆盖。

---

# 22. 最终执行顺序

从当前真实工作区开始严格执行：

~~~text
1. 收口当前 MySQL / Redis / Persistence Authority
2. 跑 Platform/System/Recovery 全量回归
3. 冻结 Production Profile
4. 同一 Profile 连跑 3 篇真实 Episode，形成 SLO
5. 只对 measured bottleneck 做性能修复
6. 自动化 25 条 Narrative Fixture
7. 实施 StoryFact-lite / Disclosure / Frame Purpose
8. Shadow Narrative QA，控制 Review Amplification
9. 实施 Reference / Transition / Caption / Dependency P1
10. 建立 Golden Episode Regression
11. Runtime Coordinator S1 Shadow（可与 7～10 并行）
12. Coordinator S2 Single Episode Durable Dispatch（G4 后）
13. Coordinator S3/S4 Multi Episode Capacity（G5 后）
14. Retrieval Offline Evaluation（Golden / Experience 稳定后，不依赖 C3）
15. Retrieval Runtime Advisory（R1 通过后）
~~~

允许：

- 第 11 步在 7～10 期间并行做只读 Shadow；
- 第 14 步在 Golden / Experience 数据稳定后提前做 Offline。

不允许：

- 主动 Coordinator dispatch 越过 G4；
- Multi Episode 越过 G5；
- Retrieval Runtime 越过 Offline Gate。

---

# 23. 一句话冻结版

> **先把当前正在发生的 MySQL/Redis Authority 迁移收口并冻结真实 Production Profile，再用同一版本连续跑 3 篇 Episode 建立可复现 SLO；随后只补真实剧集已经证明缺失的 StoryFact、Disclosure 和 Frame Purpose，用 25 条 Fixture + Golden Episode 锁住质量；等单 Episode 的“稳、快、懂剧情”都有证据以后，再让 Runtime Coordinator 从 Shadow 逐级接管多 Episode 调度，最后才把 Rewrite / Retrieval / Rerank / RAG 接入 Runtime。**

