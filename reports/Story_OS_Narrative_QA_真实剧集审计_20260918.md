# Story OS Narrative QA Fixture + 真实剧集审计

日期：2026-09-18  
性质：**研究/需求校准，不实施 VNext 功能代码，不改变任何 Episode 阶段。**

## 1. 本轮目标

本轮完成两件事：

1. 建立剧情、字幕、画面证据、转场、连续性、Reference 的正例/反例/边界 Fixture。
2. 用 StoryOS 自己的真实生产证据反审此前从 POV-AI-Storytelling 吸收出的 VNext 设计，确认哪些是真缺口、哪些已经覆盖、哪些不该重复建设。

Fixture 已落：

`tests/narrative/fixtures/`

当前阶段 Fixture 是**静态回归资产**，不是 Production Gate。

---

# 2. 样本说明

## 2.1 《婚礼前夜·记忆麻醉》

定位：成功生产样本 + 真实内容返工样本。

核心证据：

- Story Lock V2
- 20 张正式分镜 V2
- frame-semantic-review
- caption-image-audit
- 生产问题复盘

最有价值的地方：它不是“理论上可能发生问题”，而是第一版实际因为**揭露顺序、首图人物呈现、依赖失效传播**发生过返工。

## 2.2 《天界普通女生的一天》

定位：真实边界/状态一致性样本。

当前内容资产已迁移，本轮使用 StoryOS 仓库中的真实修复实施记录与 canonical issue evidence。

核心证据：

- Frame17 P02 临时持机 vs World State P01 recorder 冲突
- per-frame SHA-bound Visual admission
- Temporal/Wardrobe 非破坏 rebind
- Environment effective daypart 冲突

## 2.3 EP003《雾中的另一座生活区》

定位：**历史归档样本，不属于当前正式正史，也不能被当作可恢复的正式 Production Episode。**

它同时具有两类价值：

1. 内容语义/字幕/时间连续性的完整历史生产证据。
2. W-17 Reference Anchor 执行链等真实框架负例。

Production Hardening 已明确：历史 Episode 缺少当前 required evidence 时必须 FAIL，不允许走“兼容性 PASS”。

## 2.4 “天界打工人”替代样本说明

当前内容仓库没有独立命名为“天界打工人/天界普通女人”的现役 Episode；存在 `M00_HEAVEN_WORKER_DAILY_V1` 天界生活档案。

本轮额外读取当前真实使用该视觉档案并有完整 production evidence 的：

`17_狮驼岭/01_泔水与金牌`

它用于验证“幻想世界里的普通劳动者生活记录 / 生活优先于奇观”这一视觉与字幕边界。

---

# 3. 审计总表

| 能力 | 婚礼前夜 | 天界普通女生 | EP003 | 当前判断 |
|---|---|---|---|---|
| StoryFact / Canon | 部分 | 部分 | 部分 | **需要轻量增强，不做知识图谱** |
| Disclosure Boundary | **真实缺口** | 非主要问题 | 有 storyboard 级限制 | **P0-lite** |
| Frame Narrative / required cues | 已较强 | 已较强 | 已较强 | **增强现有 Frame Contract，不新建 ShotContract** |
| Transition | 有连续性规则 | **曾暴露 recorder 冲突，已修** | temporal continuity 完整 | **P1-lite，不建 TransitionService** |
| Caption | pixel audit 强 | 非主要缺口 | pixel audit 强 | **从原 P0 下调 P1-lite** |
| Visual Evidence | critic/required cues 强 | Visual admission 强 | frame semantic 强 | **扩展现有 Reviewer，不建 Evidence 平台** |
| Reference execution | 非主要样本 | 非主要样本 | **W-17 真负例，已修** | 执行证据已强；仅 `inherit/ignore/authority` 仍是设计增强 |
| Render Observation | 无独立对象 | 无必要证据 | 无必要证据 | **继续延后 P1.5/P2** |
| Dirty propagation | cover 等仍有缺口 | per-frame dirty 已强 | 归档 evidence 有 relocation | **P1，复用现有 SHA/dirty 体系** |
| 正反例回归资产 | 缺 | 缺 | 缺 | **本轮已开始补齐** |

---

# 4. 《婚礼前夜》审计

## 4.1 真缺口 A：逐帧揭露边界没有进入权威 Frame Contract

生产复盘明确记录：

- 第一版药物出现太早；
- Frame03-05 解释过明确；
- Frame11 没有新增证据；
- 最终不得不改 Story、Storyboard、字幕、逐帧合同和 Prompt，再按影响范围重跑。

V2 通过人工写入：

`本帧允许知道：...`

才把问题收敛。

### 判断

这是本轮最强的 P0 证据。

应该吸收：

`DisclosureBoundary / allowed_to_know / must_not_reveal`

但落点应是**现有 Resolved Frame Contract 的字段增强**，不是新建 Narrative Platform。

## 4.2 真缺口 B：特殊帧职能缺少局部例外优先级

旧 Frame01 按通用 POV 规则生成：

- 主角只露手/袖/鞋；
- 不露清晰正脸。

从通用合同看它是“执行正确”的，但从账号首图职能看它是错的，因为第一张承担人物身份锚/门面展示。

后来通过“Frame01 是全篇唯一允许清晰正脸的留影帧”显式例外才修正。

### 判断

需要的不是再加一个“自拍规则”，而是：

- `frame_purpose`
- `local_exception`
- `override_reason`
- 明确局部合同优先于通用规则的优先级。

## 4.3 Caption：已有能力比预估强

当前实际已有：

- 字幕 Voice Card
- “此刻知道什么/不知道什么”
- 删字幕测试
- caption-image actual-pixel audit
- subtitle unobstructed
- caption SHA binding

所以不应新建大型 Caption System。

第一版只需要给现有字幕结构增加可选：

`role / supports / must_not_reveal`

## 4.4 Visual Evidence：已有 Reviewer 基础

Frame03 铁链、Frame05 红痕、Frame11 铁栏都已经可以被 actual-pixel critic 验证。

真正需要补的是把“这一帧预期必须提供什么新证据”更稳定地放入 Frame Contract，再由现有 Reviewer 消费。

因此：

**EvidenceVerifier = 改造现有 Review，不新增独立服务。**

## 4.5 仍开放但不属于本次 P0：跨资产失效传播

Frame01 替换后 cover/contact-sheet/snapshot/delivery 没有自动失效，属于真实问题。

它应进入 P1 Dependency Propagation，而不是混进 Narrative Contract。

---

# 5. 《天界普通女生的一天》审计

## 5.1 Transition 不等于“系统完全没有”

Frame17 曾出现：

- Capture Event：P02 摄影
- Shot Progression：P02 摄影
- persistent World State：仍是 P01

这是一个真实的相邻状态/摄影者权威冲突。

但修复已经通过：

- Frame17 recorder=P02；
- active device 仍属于 P01；
- Frame18 显式归还设备并恢复 P01 recorder；
- 重编 20-frame contract PASS。

### 判断

StoryOS 已经有：

- World State
- Capture Event
- Shot Progression
- Temporal
- Frame Contract

所以 Transition 的正确落地是：

> 在现有 Frame Contract/相邻状态验证上增加轻量 edge/assertion。

**不要建 TransitionService / TransitionRepository / 新状态机。**

## 5.2 Dirty Review：当前已有比 POV 方法论更强的工程能力

Frame17 变化后，旧实现曾把 Frame05/16 未变像素拉回 stochastic re-review。

现已形成：

- per-frame asset SHA
- Frame Contract SHA
- Profile SHA
- dirty-only review
- 有效 PASS 不重新随机评审

### 判断

VNext 不应重复做一套 dependency framework；只应把 StoryFact/Disclosure/Reference 等新字段纳入现有 dirty 判定。

## 5.3 Environment 有效状态冲突是非常好的 Continuity 负例

真实问题：

- condition 写 midday/afternoon/dusk；
- effective `time_of_day` 却仍继承 morning。

这证明：

> 文本里“出现了正确词”不等于最终有效合同状态正确。

该案例已固化进 continuity Fixture。

---

# 6. EP003 审计

## 6.1 先纠正定位

EP003 已归档并废弃，不是当前可恢复正式 Episode。

因此任何新 Gate 审计都不能因为“历史上曾经 PASS”就让它兼容通过。

Production Hardening 已正确表现为：

- 缺 Story DNA Trace → FAIL
- 缺 Visual Reality Score → FAIL
- 缺 Reference Execution Receipt → FAIL
- 不写新的 approval/gate PASS

这本身就是一个重要边界 Fixture：

> **历史资产存在 ≠ 当前证据完整。**

## 6.2 Reference Execution：原缺口已经闭环

W-17 的真实负例非常典型：

`required_anchors=[protagonist_identity,P02_face]`

但实际 worker 只收到 P01/group identity。

这证明：

`declared reference != executed reference`

后来已经补：

- required anchor execution reconciliation
- identity reference 优先
- scheduler 执行前 missing anchor fail-close
- provider receipt / reference SHA / verified evidence

### 判断

**不要再新增 Reference Execution Evidence 系统。**

下一版 Reference 真正值得增强的是更细的语义：

`inherit / ignore / authority`

例如“P01 face reference 只负责 identity，不默认继承背景和服装”。

## 6.3 Story Semantic Trace / Evidence Gate 也已经不是空白

统一问题清单已记录：

- W-78 Story Semantic Trace：已修复
- W-79 Reference Execution Evidence：已修复
- W-83 Evidence Gate 只验证文件存在：已修复

因此：

- 不新建 Story Semantic Trace 2.0
- 不新建 Evidence Platform
- 不新建第二套执行证据链

只增强现有 Contract/Reviewer 的输入语义。

---

# 7. “幻想世界普通劳动者”补充审计：《泔水与金牌》

该篇实际使用：

`M00_HEAVEN_WORKER_DAILY_V1`

并且 Visual Profile Review 已明确验证：

- ordinary_life_density
- available_light
- unposed_capture
- not_cinematic
- camera_authorship_physical
- moment_capture_credibility

这说明“生活优先于奇观”已经进入当前 Visual Profile QA，不需要因 POV 仓库研究另建一套真实感系统。

两个值得留下的边界例：

1. Frame01 水面倒影能看清人物身份，但“巡”字读不清仍可 PASS，因为该文字不是本帧 required pixel evidence。
2. Frame06/08 字幕可以讲画面外的上层事实，只要 Reviewer 明确区分 off-frame narration 与当前像素证据。

---

# 8. 对此前 VNext 优先级的校准

## 8.1 P0 / 下一版合同增强

### P0-1 Disclosure Boundary

直接进入现有 Frame Contract：

- `allowed_to_know`
- `must_not_reveal`
- 可选 `supports_fact_ids`

理由：婚礼前夜已有真实返工证据。

### P0-2 Frame Purpose / Local Exception Priority

用于处理：

- 首图人物锚
- 唯一露脸帧
- 特殊摄影者
- 特殊画幅/构图职责

理由：婚礼 Frame01 和天界普通女生 Frame17 都证明“通用规则正确但局部职能更高优先级”是真问题。

### P0-3 StoryFact-lite

只做轻量：

- CONFIRMED
- UNKNOWN
- UNDECIDED
- disclosure 独立维度

不做 Knowledge Graph。

主要作用：给 Disclosure Boundary 一个稳定事实 ID，而不是马上建设复杂推理系统。

## 8.2 P1

### Reference Semantics

`inherit / ignore / authority`

原因：执行证据链已经补齐，下一步才是解决“参考图究竟继承什么”。

### Transition Edge

只做现有 Frame/World/Temporal 之间的一致性边：

- recorder
- device handoff
- location
- time
- key prop state

不建独立服务。

### Caption Semantic Fields

只增加：

- role
- supports
- must_not_reveal

现有 Caption QA 已很强，因此从此前 P0 下调。

### Dependency Propagation

把新增 StoryFact/Disclosure/Reference 字段接入已有 SHA/dirty/invalidation。

## 8.3 P1.5 / P2

### RenderObservation

继续延后。

真实样本没有证明必须马上引入独立：

`image → observation object → verifier`

当前 actual-pixel reviewer 直接核对 Expected Evidence 足以支持第一版。

只有未来出现：

- 多 Reviewer 共享同一像素事实
- Observation 进入 Experience Store
- Repair Router 依赖结构化观察

再独立 RenderObservation。

---

# 9. 正反例 Fixture 本轮成果

当前新增：

| 类别 | 文件 | 重点 |
|---|---|---|
| 剧情 | `plot.json` | 揭露顺序、因果、克制型高潮 |
| 字幕 | `caption.json` | 早泄露、画面外旁述、机械复述 |
| 画面 | `visual_evidence.json` | required evidence、低置信证据、像素边界 |
| 转场 | `transition.json` | recorder handoff、动作桥 |
| 连续性 | `continuity.json` | daypart、衣着/道具、dirty/invalidation |
| Reference | `reference.json` | declared-vs-executed、authority、future inherit/ignore |

本轮同时发现现有：

`reports/golden-episode-registry.json`

仍为空：

`episodes=[]`

因此 Narrative Fixture 建立后，下一阶段如果要真正形成整集 Golden Regression，应单独处理 W-10；本轮不擅自修改 Golden Registry。

---

# 10. 最终结论

真实 Episode 反审以后，VNext 应进一步收敛：

```text
Story Canon-lite
    ↓
Existing Resolved Frame Contract
    + disclosure boundary
    + frame purpose / local exception
    + expected evidence
    + reference semantics
    + light transition assertions
    ↓
Existing Review / Evidence Gate
    + consume the new fields
    ↓
Narrative QA Fixtures
```

明确不做：

- Narrative Platform
- 新 Story Bible Service
- 新 Evidence Platform
- 新 Transition Service
- 第二套 Reference Execution Evidence
- 立即实现 RenderObservation
- 立即上复杂 RAG

**真实验证后的核心优先级不是“加更多模块”，而是把已经存在的 StoryOS 权威链再补三种语义：什么时候能说、这一帧为什么例外、参考图究竟继承什么。**

---

# 11. 本轮变更边界

本轮只新增：

- `tests/narrative/fixtures/*`
- 本审计报告

没有修改：

- Runtime
- Scheduler
- Agent Orchestrator
- Workflow
- Production Gate
- Episode state
- 内容资产

下一步应先评审/冻结这些 Fixture 与审计结论，再决定是否修订 VNext 方案为 Final/Frozen，**不建议直接开始实现 VNext 代码**。

