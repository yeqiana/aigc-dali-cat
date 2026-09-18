# StoryOS 下一阶段总迭代方案 V1.0 Final

> **SUPERSEDED / 已被替代**：深度评审后的正式基线见 `docs/StoryOS_下一阶段总迭代方案_V1.1_Final_Frozen_20260918.md`。

更新时间：2026-09-18  
适用分支：`story-platform-v3`  
状态：**FINAL / ITERATION BASELINE**  
性质：总迭代路线图；整合生产效率、Narrative QA、VNext 叙事语义和当前 StoryOS 真实架构状态。

---

# 0. 本方案依据

本方案不是重新规划一个“理想 StoryOS”，而是基于当前真实仓库与真实生产证据做下一阶段收敛。

核心输入：

1. `reports/Story_OS_生产效率实测审计报告_20260918.md`
2. `reports/Story_OS_Narrative_QA_真实剧集审计_20260918.md`
3. `docs/StoryOS_VNext_叙事语义增强落地方案_V1.1_Final_Frozen_20260918.md`
4. `reports/Story_OS_V3_Production_Ready_Freeze_20260916.md`
5. `docs/Story_OS_全系统架构与成熟度评审_20260916.md`
6. `docs/Story_OS_生产效率优化方案_V2_Runtime_DAG与智能调度设计.md`
7. 当前 StoryOS 真实代码、测试、Runtime Workspace、Production Ledger 与 Narrative Fixture。

---

# 1. 一句话总判断

StoryOS 已经跨过：

```text
“能不能生产”
```

阶段。

现在进入：

```text
“怎样稳定、快速、无人值守地生产”
          +
“怎样让系统真正理解每一帧为什么存在”
          +
“怎样同时观察和管理多个 Episode”
```

阶段。

因此下一轮**不是 V4 大重构**。

正确方向是：

```text
保护现有 Production Kernel
        ↓
先证明当前全链效率
        ↓
增强 Narrative Contract
        ↓
减少 Review Amplification
        ↓
形成 Golden Regression
        ↓
再扩多 Episode Control Plane / 更强 Memory / RAG
```

---

# 2. 当前 StoryOS 真实状态

## 2.1 V3 主架构已经冻结

当前正式架构：

```text
V2.x Production Kernel
        +
V3 Platform Control Plane
        +
Runtime Workspace
```

Production Kernel 继续拥有：

- Episode Stage；
- Production Ledger；
- Story / Visual / Frame Contract；
- Gate / Evidence；
- Runtime DAG；
- Image Scheduler；
- Review / Repair / Release。

V3 Platform 负责：

- Event / Trace / Artifact；
- Workflow / Agent；
- Platform API；
- RuntimeStatus；
- Experience / Memory；
- Repository；
- Console；
- 治理与观察。

**下一阶段禁止再做 Production Kernel 大迁移。**

---

# 3. 已完成能力：不要再重复开发

以下能力已经进入代码闭环，下一阶段主要任务是**真实生产验证**，不是重新设计。

| 能力 | 当前状态 |
|---|---|
| Runtime DAG | ✅ 已完成 |
| Smart Scheduler / Priority | ✅ 已完成 |
| Resource Awareness | ✅ 已完成 |
| PREIMAGE 并行 Candidate Protocol | ✅ 已完成 |
| Single Writer Authority Commit | ✅ 已完成 |
| Parallel Frame Contract Compile | ✅ 已完成 |
| Image Scheduler 3 路并发 | ✅ 已有真实收益 |
| TECH_FAILED / 内容失败隔离 | ✅ 已完成 |
| WEAK_PASS / 有界低分通过 | ✅ 已完成 |
| Resident Driver 自动续跑 | ✅ 已完成 |
| RuntimeStatusSnapshot | ✅ 已完成 |
| 多 Episode RuntimeStatus API | ✅ 已完成 |
| Runtime Request 三域分层 | ✅ 已完成 |
| PREIMAGE 确定性依赖预物化 | ✅ 已完成 |
| Platform Execution / Experience JSONL 持久化 | ✅ 已完成第一层 |
| MySQL Latest Record Store Adapter | ✅ 已实现，未真实切生产 |
| Memory Advisory 进入 CREATIVE_STORY | ✅ 已完成第一阶段 |
| Runtime Workspace 新 Episode 默认 Queue | ✅ 已完成 |
| Checkpoint / Frame Cache Workspace 化 | ✅ 已完成 |
| Formal Evidence 保留 Episode Authority | ✅ 已冻结 |
| Candidate-aware Final Review PATCH | ✅ 代码/测试闭环 |
| FULL Review 4 shard fan-out | ✅ 代码/测试闭环 |
| Performance ACTIVE / HOST_WAIT / USER_WAIT / IDLE | ✅ 已完成 |

因此：

> 后续文档和开发任务不得把这些能力再次列成“待从零实现”。

---

# 4. 当前真正未闭环的五件事

经过生产效率与 Narrative QA 两轮真实审计，真正需要进入下一阶段的是：

## 4.1 整篇 Episode E2E 效率还没有正式验收

已经证明：

- 3 路真实图片批次：314s resource → 115s wall；
- speedup = 2.73×；
- 并发效率约 91%；
- 成功图 avg = 101.7s；
- P90 = 118s；
- 图片 backend overlap-aware wall = 20.6 分钟；
- resource time = 46.3 分钟；
- 并发节省约 25.7 分钟。

但是：

> 还不能严谨说“StoryOS 一篇 20 帧稳定 X 分钟完成”。

缺：

- 新 Episode；
- 零人工干预；
- 不边跑边改代码；
- create → PUBLISH_READY；
- E2E / Active Wall / Wait / Review / Repair 全量指标。

## 4.2 Review 已成为主要性能瓶颈

当前瓶颈：

```text
Review Amplification
    >
FULL Review
    >
Image Provider latency
```

历史 FULL Final Semantic：

- candidate ≈20m；
- worker active ≈28m。

所以后续性能优化不能继续只盯生图。

## 4.3 Narrative Contract 还有三个真实缺口

真实审计确认：

1. Disclosure Boundary；
2. Frame Purpose / Local Exception；
3. Reference inherit / ignore / authority。

其中 P0：

- StoryFact-lite；
- Disclosure Boundary；
- Frame Purpose / Local Exception。

## 4.4 Narrative QA 有 Fixture，但还没有 Golden Episode Regression

当前：

`tests/narrative/fixtures/`

已经有 25 条真实/变异 Fixture。

但是：

`reports/golden-episode-registry.json`

仍然：

```json
{"episodes":[]}
```

所以当前只能做局部语义回归，还没有整篇 Golden Episode 回归。

## 4.5 Platform 已能观察，但长期 Control Plane 仍未完全生产化

已完成：

- RuntimeStatusSnapshot；
- 多 Episode API；
- JSONL Execution / Experience；
- MySQL Adapter；
- Memory Advisory。

仍未做：

- MySQL 真实生产 migration / cutover；
- 多 Episode durable production queue；
- Platform → Kernel 完整 command plane；
- 更强 Memory Retrieval / Rerank；
- 长期 Experience weighting。

这些不阻塞当前生产，但属于后续平台化路线。

---

# 5. 总体迭代目标

本轮总迭代只围绕五个目标。

## Goal A：证明“当前系统到底有多快”

建立第一版真实 Production SLO Baseline。

## Goal B：让系统真正理解“这一帧应该说什么”

落地 VNext Narrative Semantics P0。

## Goal C：减少“生图已经好了，却反复重新审核”的浪费

把 Review Patch / FULL Fan-out 的代码闭环转成真实效率证据。

## Goal D：把真实失败沉淀成可重复回归资产

从 25 条 Fixture 扩展到 Golden Episode Regression。

## Goal E：为多 Episode 工厂准备 Control Plane

但不重写 Production Kernel。

---

# 6. 总迭代阶段

建议总迭代拆为：

```text
Iteration 0
当前冻结基线整理
        ↓
Iteration 1
Production SLO 真实验收
        ↓
Iteration 2
Narrative Semantics VNext-1
        ↓
Iteration 3
Narrative QA / Review Enhancement
        ↓
Iteration 4
Golden Episode + E2E Regression
        ↓
Iteration 5
Multi-Episode Control Plane
        ↓
Iteration 6
Memory Retrieval / Rerank / RAG
```

---

# 7. Iteration 0：冻结当前真实基线

优先级：**P0 / 立即**

目标：

> 避免下一轮把当前大量并行改动、运行资产与新功能混在一起。

当前工作区仍然非常 dirty。

因此下一阶段正式开发前必须：

1. 明确当前 HEAD / 已提交功能基线；
2. 精确识别未提交源代码；
3. 运行资产、Episode 历史 evidence 不允许跟源码混提交；
4. 禁止 `git add .`；
5. Narrative Fixture / 总方案 / Frozen 方案独立提交域；
6. 当前生产代码若还有别的会话在改，必须先完成文件级责任边界。

### 输出

- Source Code Baseline；
- Runtime Asset / Episode Asset Boundary；
- 当前测试基线；
- 当前 Performance Baseline。

### 验收

- 无 conflicted files；
- 关键源代码提交边界明确；
- 可以准确回答“接下来 VNext 修改了哪些文件”。

---

# 8. Iteration 1：Production SLO 真实验收

优先级：**P0**

这是下一阶段最应该先做的真实生产工作。

## 8.1 原因

性能优化代码已经很多：

- W-103 Review PATCH；
- W-104 FULL Review fan-out；
- W-105 Wait Attribution；
- Image Scheduler 并发；
- Resident Driver；
- WEAK_PASS。

继续改代码之前，需要先证明现状。

## 8.2 验收方法

连续跑 3 篇全新标准 Episode。

### Episode A

目的：

- 发现最后的 observability / production bug；
- 允许修最后的测量问题；
- 不用于稳定 SLO。

### Episode B / C

要求：

- 不允许中途改代码；
- 不允许人工改 Queue；
- 不允许人工改 Ledger；
- 不允许手工跳 Gate；
- create --full-auto → PUBLISH_READY。

## 8.3 自动采集指标

每篇必须输出：

| 指标 | 用途 |
|---|---|
| E2E wall | 用户真实等待 |
| Active wall | 系统真正工作时间 |
| HOST_WAIT | Host 等待 |
| USER_WAIT | 用户等待 |
| IDLE | 空闲 |
| image wall | 生图 wall |
| image resource | 生图总资源时间 |
| image P50/P90 | Provider 稳定性 |
| image requested/succeeded/failed | 产出率 |
| max image inflight | 图片实际并发 |
| review wall | Review 成本 |
| FULL review calls | 全审次数 |
| PATCH review calls | 增量审次数 |
| reviewed frame count | 实际审帧数 |
| max review inflight | Review 并发 |
| repair rounds | 返修轮数 |
| first-pass yield | 首轮通过率 |
| WEAK_PASS count | 降级止损情况 |
| PUBLISH_READY | 是否闭环 |

## 8.4 当前目标值

这些是**验收目标，不是假装已取得的成绩**：

- 20-frame FULL Review wall：优先验证是否能进入 10～12 分钟级；
- 2 dirty roots PATCH wall：优先验证 3～8 分钟级；
- image 3-way concurrency：保持真实并发收益；
- 不出现“2 帧变更重新审 20 帧”的无意义 amplification。

## 8.5 输出

`Production SLO Baseline V1`

第一次正式回答：

> 一篇标准 StoryOS Episode 在当前真实环境下，大致需要多少 E2E / Active / Review / Image 时间。

---

# 9. Iteration 2：Narrative Semantics VNext-1

优先级：**P0**

基线：

`docs/StoryOS_VNext_叙事语义增强落地方案_V1.1_Final_Frozen_20260918.md`

必须遵循 Frozen Scope。

## 9.1 只做 StoryFact-lite

状态：

```text
CONFIRMED
UNKNOWN
UNDECIDED
```

不做知识图谱。

不做 StoryFact Service。

不做 Graph Database。

## 9.2 Disclosure Boundary

增加：

```yaml
allowed_to_know:
must_not_reveal:
supports_fact_ids:
```

真实目标：

让 StoryOS 能阻止：

- 药物过早出现；
- 未证明因果被字幕宣布；
- 结尾事实提前泄露；
- 模糊证据被强行解释成确认事实。

## 9.3 Frame Purpose / Local Exception

增加：

```yaml
frame_purpose:
local_exceptions:
  - rule:
    action:
    reason:
```

解决：

- Frame01 身份锚；
- 特殊 recorder；
- 特殊视觉职责；
- 局部例外和全局规范冲突。

## 9.4 必须进入 Existing Frame Contract

禁止新建 ShotContract。

新字段必须进入：

- frame hash material；
- prompt package；
- review context；
- dirty detection。

## 9.5 首阶段只 Shadow

```text
Unit
→ Fixture
→ Shadow
```

不直接 Hard Gate。

---

# 10. Iteration 3：Narrative QA + Review Enhancement

优先级：**P1**

在 VNext-1 稳定后做。

## 10.1 Reference Semantics

只增加：

```yaml
inherit:
ignore:
authority:
```

现有：

- required anchor；
- execution evidence；
- provider receipt；
- reference SHA；

全部复用。

禁止再造第二套 Reference Execution 系统。

## 10.2 Transition Assertions

不建 Transition Service。

只检查：

- recorder；
- device handoff；
- location；
- time；
- key prop state。

复用：

- World State；
- Capture Event；
- Shot Progression；
- Temporal；
- Wardrobe。

## 10.3 Caption Semantics

当前 Caption 体系已经很强。

只增加：

```yaml
role:
supports:
must_not_reveal:
```

不建 Caption Platform。

## 10.4 Evidence Reviewer

不建 Evidence Platform。

让现有 Reviewer 额外检查：

- disclosure respected；
- frame purpose satisfied；
- required evidence；
- forbidden evidence；
- reference scope。

## 10.5 Dependency Propagation

复用现有：

- SHA；
- source binding；
- dirty admission；
- stale detection。

补足：

- StoryFact 改变；
- Disclosure 改变；
- Reference semantic 改变；
- Frame Purpose 改变；

时的 affected frames / dependent assets。

重点修复历史：

`Frame01 changed → cover/contact-sheet/snapshot/delivery stale`

这类失效传播。

---

# 11. Iteration 4：Golden Episode Regression

优先级：**P1**

当前 25 条 Narrative Fixture 只能证明“局部规则”。

下一阶段需要把真实完整 Episode 纳入 Golden Regression。

## 11.1 建议 Golden 分三类

### Golden A：成功内容样本

例如：

《婚礼前夜·记忆麻醉》

用于防：

- 新规则误杀成功内容；
- Caption/POV/Disclosure 回归。

### Golden B：边界样本

例如：

幻想劳动者生活样本。

用于防：

- 画面外旁述被误判；
- 低置信 evidence 被强行确定；
- 非电影化真实感被新模型破坏。

### Golden C：历史负例

例如：

EP003 W-17、天界普通女生 recorder conflict。

用于保证：

- 修过的生产漏洞不复发。

## 11.2 Golden Regression 不等于 Fixture

```text
Fixture
→ 规则级

Golden Episode
→ 整篇生产/审核行为级
```

## 11.3 最终目标

以后任何：

- Story Agent；
- Storyboard Agent；
- Prompt Compiler；
- Reviewer；
- Reference Resolver；

升级，都能得到：

```text
Code Tests
+
Narrative Fixtures
+
Golden Episodes
```

三层回归。

---

# 12. Iteration 5：多 Episode Control Plane

优先级：**P2**

这一阶段才是真正为“内容工厂”准备。

## 12.1 不新增新的主生产调度器

当前已经有：

- Runtime DAG；
- Smart Scheduler；
- Resident Driver；
- RuntimeStatusSnapshot；
- multi Episode status API。

所以“主调度线程”应该理解为：

> **让现有 Control Plane 持久化地调度多个 Episode，而不是重新写一个 Orchestrator。**

## 12.2 多 Episode Durable Queue

当前多 Episode Queue 仍主要停留在设计。

未来需要：

```text
Episode A
Episode B
Episode C
     ↓
Platform Task Queue
     ↓
Global Resource Policy
     ↓
existing Kernel Runner / Scheduler
```

## 12.3 Platform 只调度，不抢生产 Authority

```text
Platform
    → start / pause / resume / retry

Kernel
    → Story/Frame/Gate/Ledger authority
```

## 12.4 MySQL / Redis

当前 Adapter 已具备。

真实生产 migration / cutover 必须单独执行：

1. schema apply；
2. backup；
3. dual/read validation；
4. canary；
5. rollback；
6. 才考虑默认切换。

不得和 Narrative Semantics 同一个大提交上线。

---

# 13. Iteration 6：Memory Retrieval / Rewrite / Rerank / RAG

优先级：**P2 / P3**

这部分保留为下一版智能化方向，但不抢当前主线。

## 13.1 当前已有

- Experience Store；
- Story DNA；
- Similarity；
- Advisor；
- Failure Memory；
- Runtime Memory Advice；
- Creative Story advisory。

## 13.2 后续需要

```text
Query / Need
   ↓
Rewrite
   ↓
Structured Filter
   ↓
Retrieve
   ↓
Rerank
   ↓
Experience Advice
```

## 13.3 Hard Truth 与 Soft Experience 必须分开

```text
StoryFact / Frame Contract
        >
Memory / Experience / RAG
```

Memory 永远不能覆盖：

- 当前人物身份；
- 当前衣服；
- 当前 Story Lock；
- 当前 Disclosure；
- 当前 Frame Contract。

## 13.4 RAG 主要用来找

- 历史相似 Episode；
- 失败案例；
- Prompt 修复经验；
- 传播经验；
- 视觉经验；
- 账号 Pattern。

不用于决定：

> “这一帧人物到底穿什么。”

---

# 14. 总优先级重新排序

## P0：现在做

| 顺序 | 项目 |
|---:|---|
| 1 | 当前代码/资产基线收敛 |
| 2 | 3 篇新 Episode Production SLO 验收 |
| 3 | StoryFact-lite |
| 4 | Disclosure Boundary |
| 5 | Frame Purpose / Local Exception |
| 6 | Frame Contract SHA / Shadow integration |

## P1：P0 后做

| 顺序 | 项目 |
|---:|---|
| 1 | Reference inherit/ignore/authority |
| 2 | Transition assertions |
| 3 | Caption semantic metadata |
| 4 | Evidence Reviewer enhancement |
| 5 | Dependency propagation |
| 6 | Golden Episode Registry / Regression |

## P2：平台生产化

| 顺序 | 项目 |
|---:|---|
| 1 | Multi Episode Durable Queue |
| 2 | Platform → Kernel Command Plane |
| 3 | MySQL/Redis 真实受控切换 |
| 4 | Multi Episode Resource Scheduling |

## P3：智能检索

| 顺序 | 项目 |
|---:|---|
| 1 | Experience Retrieval |
| 2 | Query Rewrite |
| 3 | Structured Recall |
| 4 | Rerank |
| 5 | RAG / Long-term Memory weighting |

---

# 15. 推荐并行实施方式

为了避免一个阶段等另一个阶段，建议最多 4 个独立写入域。

## Track A：Production Benchmark

负责：

- 真实 Episode；
- 性能指标；
- SLO Baseline；
- Review wall 验证。

## Track B：Narrative Contract

负责：

- StoryFact；
- Disclosure；
- Frame Purpose；
- Frame Contract。

## Track C：Narrative QA

负责：

- Fixture loader；
- Shadow Reviewer；
- Golden Registry；
- Regression。

## Track D：Platform Read/Control

只做：

- status；
- monitoring；
- command/control design；
- MySQL migration preparation。

### Single Writer 原则

以下核心文件域必须 single-writer：

- `frame_contract.py`；
- Story Gates schema；
- Production Ledger；
- Queue Store；
- Episode State。

并行 Agent 不得同时修改同一 Authority。

---

# 16. 预计工作量

以下仅用于迭代排期，不是生产耗时承诺。

| 阶段 | 预计工程量 |
|---|---:|
| Iteration 0 基线整理 | 1～2 人天 |
| Iteration 1 E2E SLO 验收与报告 | 2～4 人天 + 实际 Episode 运行时间 |
| Iteration 2 Narrative VNext-1 | 4～7 人天 |
| Iteration 3 Narrative QA / P1 | 4～8 人天 |
| Iteration 4 Golden Regression | 2～4 人天 |
| Iteration 5 Multi Episode Control Plane | 5～10 人天 |
| Iteration 6 Retrieval / Rerank Prototype | 4～8 人天 |

建议不要一次把 P0～P3 全部开工。

第一阶段只投入：

```text
Iteration 0
+
Iteration 1
+
Iteration 2
```

完成后再重新评审。

---

# 17. 第一个正式里程碑

名称：

## M1：Production + Narrative Baseline

必须同时满足：

### Production

- 3 篇新 Episode 已完成验收；
- 至少后 2 篇不边跑边改代码；
- E2E / Active / Image / Review / Wait 指标完整；
- W-103 / W-104 收益得到真实证据；
- 可以形成 Production SLO Baseline V1。

### Narrative

- StoryFact-lite schema ready；
- Disclosure Boundary ready；
- Frame Purpose / Local Exception ready；
- 25 条 Fixture 可自动加载；
- Shadow Review 不影响 Production；
- existing Frame Contract Authority 不被破坏。

### Regression

- Platform/System 全量无新增失败；
- Narrative positive 不误杀；
- Narrative negative 能识别；
- boundary case 不被机械 FAIL。

达到 M1 后，才进入 Reference / Transition / Caption P1。

---

# 18. 第二个正式里程碑

名称：

## M2：Narrative QA Production Ready

必须满足：

- Reference semantics 完成；
- Transition assertions 完成；
- Caption semantic metadata 完成；
- dependent artifacts dirty propagation 完成；
- Golden Episode Registry 至少有 2 个真实 Episode；
- Shadow → Warning 已完成；
- false positive 有明确统计；
- Narrative QA 不显著放大 Review wall。

---

# 19. 第三个正式里程碑

名称：

## M3：Multi-Episode Production Control

必须满足：

- RuntimeStatus 多 Episode 已稳定；
- durable global task queue；
- Platform 可发 start/pause/resume/retry；
- Kernel authority 不变；
- 资源调度不会让多个 Episode 争抢同一个 authority；
- MySQL/Redis 如切生产已有 rollback；
- Console 不再直接理解底层几十份 JSON。

---

# 20. 当前明确不应该做的事情

下一阶段禁止：

1. 重写 `episodes/_system`；
2. 新建第二个 Production Kernel；
3. 新建 Narrative Platform；
4. 新建 ShotContract 第二 Authority；
5. 新建 Transition Service；
6. 新建 Evidence Platform；
7. 新建第二套 Reference Execution Evidence；
8. 在 E2E 性能没验收前继续大量优化 Mock；
9. 在 StoryFact/Disclosure 还没稳定前上复杂 RAG；
10. 把 MySQL 实际切生产和 Narrative P0 同一轮上线；
11. 为了多 Episode 再写一个和现有 Runtime DAG 重叠的“大总调度器”；
12. 把历史 Episode 缺失的 evidence 自动补成 PASS；
13. 让 Console 自己解释底层 Runtime 文件；
14. 让 transient runtime 文件继续无限污染 Git 工作树。

---

# 21. 总体验收指标

以后 StoryOS 下一阶段不能只用：

```text
pytest passed
```

证明完成。

必须同时看四类指标。

## 21.1 Stability

- tests/platform；
- tests/system；
- Production gates；
- Resume / Recovery；
- stale / SHA；
- authority single writer。

## 21.2 Efficiency

- E2E wall；
- active wall；
- image wall；
- review wall；
- wait time；
- repair rounds；
- first-pass yield。

## 21.3 Narrative Quality

- Fixture pass；
- disclosure violations；
- evidence missing；
- transition conflicts；
- reference scope；
- false positive。

## 21.4 Automation

- manual interventions；
- USER_DECISION_REQUIRED 次数；
- WEAK_PASS 次数；
- auto-recovery rate；
- PUBLISH_READY completion rate。

---

# 22. StoryOS 下一阶段最终架构定位

```text
┌─────────────────────────────────────────────────────────────┐
│                       StoryOS Console                       │
│ Status / Multi Episode / Alerts / Commands / SLO           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  V3 Platform Control Plane                  │
│ RuntimeStatus / Workflow / Agent / Experience / Repository │
│ Multi Episode Queue / Resource Policy / Memory             │
└─────────────────────────────┬───────────────────────────────┘
                              │ command / projection
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Production Kernel                        │
│                                                             │
│ StoryFact-lite                                               │
│ Story / Character / World / Environment                     │
│ Resolved Frame Contract                                      │
│  ├─ Narrative Semantics                                     │
│  ├─ Disclosure Boundary                                     │
│  ├─ Frame Purpose / Local Exception                         │
│  ├─ Visual / Reference / Temporal / Wardrobe                │
│ Runtime DAG / Scheduler / Image Runtime                     │
│ Review / Evidence / Repair / Ledger / Release               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Episode Asset Layer                       │
│ Story / Storyboard / Images / Captions / Evidence          │
└─────────────────────────────────────────────────────────────┘
```

核心原则：

> **Platform 管任务、观察、资源和治理；Kernel 管生产事实、合同和成片。**

---

# 23. 下一步实际执行顺序

从现在开始建议严格按：

```text
Step 1
收敛工作区 / 确认代码基线

Step 2
跑 3 篇全新 Episode
形成 Production SLO Baseline

Step 3
实现 VNext Narrative P0
StoryFact / Disclosure / Frame Purpose

Step 4
25 Fixture 自动化
Shadow Narrative QA

Step 5
Reference / Transition / Caption / Dependency P1

Step 6
建立 Golden Episode Registry

Step 7
再跑真实 Episode 做 Narrative + Efficiency 双验收

Step 8
进入 Multi Episode Control Plane

Step 9
最后再进入 Retrieval / Rerank / RAG
```

---

# 24. 最终结论

StoryOS 当前的主要风险已经不是“功能太少”，而是：

> **功能已经很多，如果继续无序扩张，会把现有已经成熟的 Production Kernel 稀释掉。**

下一轮真正应该追求的不是模块数量，而是三个结果：

### 结果 1

一句话创建 Episode 后：

> **系统能自己跑到底，并且我们能准确知道它花了多少时间、时间花在哪里。**

### 结果 2

系统不只知道：

> “Frame08 要画什么。”

还知道：

> “Frame08 现在允许观众知道什么、为什么存在、什么不能提前说。”

### 结果 3

以后改 Agent / Prompt / Reviewer 时：

> **有代码测试 + Narrative Fixture + Golden Episode 三层回归，而不是靠下一次真实跑批重新踩坑。**

这三个结果完成后，再扩：

- Multi Episode；
- MySQL/Redis 正式控制面；
- Query Rewrite；
- Retrieval；
- Rerank；
- RAG；

才是正确顺序。

---

# 25. 一句话版本

> **下一阶段先用 3 篇真实 Episode 把当前 StoryOS 的生产效率和无人值守能力验明白，再给现有 Frame Contract 补 StoryFact、Disclosure Boundary 和 Frame Purpose 三个真正缺失的叙事语义，用 25 条 Fixture + Golden Episode 把它锁住；等“快、稳、懂剧情”三件事都成立后，再做多 Episode Control Plane 和 RAG。**

