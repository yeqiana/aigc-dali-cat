# StoryOS VNext 叙事语义增强落地方案 V1.1 Final / Frozen

更新时间：2026-09-18  
状态：**FINAL / FROZEN / DESIGN ONLY**  
适用仓库：StoryOS `story-platform-v3`  
替代版本：此前 `StoryOS_VNext_叙事语义增强落地方案_2026-09-18.md` 草案  
实施状态：**本文件冻结设计，不代表已实施；当前不得据此宣称 VNext 已上线。**

---

# 0. 冻结结论

V1.1 经过真实 Episode 反审后，正式冻结为：

```text
Story Lock / Story Gates
        ↓
StoryFact-lite
        ↓
Existing Resolved Frame Contract
  + Disclosure Boundary
  + Frame Purpose / Local Exception
  + Existing Visual Evidence
  + Existing World / Capture / Temporal / Wardrobe
        ↓
Existing Prompt Compiler / Image Runtime
        ↓
Existing Actual-Pixel Review / Evidence Gate
        ↓
Narrative QA Fixtures / Golden Regression
```

本次冻结的核心不是“再建一套叙事平台”，而是给 StoryOS 已存在的权威链补足三种语义：

1. **什么时候能说**：Disclosure Boundary；
2. **这一帧为什么能例外**：Frame Purpose / Local Exception；
3. **参考图究竟继承什么**：Reference Semantics。

同时只增加一个轻量事实层：

`StoryFact-lite`

用于给上述语义提供稳定 Fact ID。

---

# 1. V1.1 的证据基线

本版本不是依据外部方法论直接设计，而是经过 StoryOS 真实生产证据校准。

## 1.1 真实审计样本

### A. 《婚礼前夜·记忆麻醉》

验证：

- 第一版药物出现过早；
- Frame03-05 解释过明确；
- Frame11 没有新增证据；
- Frame01 通用 POV 规则与首图人物身份职能冲突；
- Frame01 替换后 cover/contact-sheet/snapshot/delivery 的失效传播不足。

结论：

- Disclosure Boundary 是真实 P0；
- Frame Purpose / Local Exception 是真实 P0；
- Dependency Propagation 是 P1。

### B. 《天界普通女生的一天》

验证：

- Frame17 Capture Event / Shot Progression 已切到 P02，但 World State 仍残留 P01 recorder；
- Frame17 改动曾把未变化 Frame05/16 拉回 stochastic re-review；
- environment condition 出现 afternoon/dusk，但 effective time_of_day 仍错误继承 morning。

结论：

- Transition 有真实价值，但 StoryOS 已有 World State / Capture Event / Shot Progression / Temporal；
- 不需要新 Transition Service；
- Dirty Review 应复用现有 SHA-bound admission。

### C. EP003《雾中的另一座生活区》

验证：

- 历史 Episode 缺新 required evidence 时必须 FAIL，不能兼容性伪 PASS；
- W-17 曾真实出现 `required_anchors=[protagonist_identity,P02_face]`，但 worker 实际只收到 P01/group identity；
- 当前 required anchor execution reconciliation、provider receipt、reference SHA、verified evidence 已经闭环；
- Story Semantic Trace / Evidence Gate 也已经存在。

结论：

- 不重复建设 Reference Execution Evidence；
- 不重复建设 Story Semantic Trace；
- 不重复建设 Evidence Platform；
- Reference 下一步只补 `inherit / ignore / authority`。

### D. 《泔水与金牌》

作为当前真实使用 `M00_HEAVEN_WORKER_DAILY_V1` 的幻想世界普通劳动者样本，验证：

- ordinary_life_density；
- available_light；
- unposed_capture；
- not_cinematic；
- camera_authorship_physical；
- 当前帧 required evidence 与画面外 narration 可以被明确区分。

结论：

- StoryOS 已有较成熟的现实感/实际像素审核，不新增第二套“真实感系统”。

## 1.2 Narrative QA Fixture

当前已建立：

`tests/narrative/fixtures/`

共 25 条：

| 分类 | 数量 |
|---|---:|
| Plot | 4 |
| Caption | 4 |
| Visual Evidence | 5 |
| Transition | 4 |
| Continuity | 4 |
| Reference | 4 |
| **合计** | **25** |

这些 Fixture 是 VNext 后续实现的回归事实源之一。

详细审计：

`reports/Story_OS_Narrative_QA_真实剧集审计_20260918.md`

---

# 2. V1.0 → V1.1 主要修订

| V1.0 倾向 | V1.1 Final/Frozen |
|---|---|
| StoryFact 偏完整语义系统 | 收敛为 StoryFact-lite |
| Caption 偏 P0 | 下调为 P1-lite |
| Transition 偏独立能力 | 下调为现有 Contract 的轻量 Edge/Assertion |
| Evidence 偏独立层 | 复用现有 required cues + actual-pixel Reviewer |
| Reference 同时补执行与语义 | 执行链已存在，只补 inherit/ignore/authority |
| RenderObservation 较早进入 | 延后至 P1.5/P2 |
| 可能新增 ShotContract | 明确禁止；增强 Existing Resolved Frame Contract |
| 可能形成 Narrative Platform | 明确禁止 |

---

# 3. 冻结原则

以下原则自 V1.1 起冻结。

## 3.1 单一 Frame Authority

正式生成仍以：

`episodes/_system/frame_contract.py`

编译出的 Resolved Frame Contract 为帧级执行 Authority。

不得再新增：

- ShotContract；
- NarrativeFrameContract；
- PromptContract VNext 并行权威；
- 第二套 per-frame authority。

新的叙事字段必须进入现有 Frame Contract 的 hash/material/prompt/review 链。

## 3.2 Authority 与 Review 分离

StoryFact / Disclosure / Purpose 是 Authority/Contract 语义。

Actual-pixel 检查是 Review Evidence。

Reviewer 不得反向创造 Story Fact，不得用“看起来像”修改 Story Authority。

## 3.3 局部变更优先

StoryOS 已经具备 per-frame SHA、dirty admission、source binding 等能力。

VNext 必须保持：

```text
Frame03 narrative semantics changed
    ↓
only Frame03 contract becomes dirty
    ↓
only dependent review/prompt/assets become dirty
```

不得因为一个 Fact/Disclosure 改动让 20 帧无条件全部重新审核或重新生成。

## 3.4 不伪造历史证据

旧 Episode 没有 VNext 证据：

- 可以继续按旧版本契约解释；
- 不允许自动生成假 evidence；
- 一旦显式迁移到 VNext，缺失的 VNext required evidence 必须真实重建；
- 不能为了兼容历史 PASS 而把新 Gate 自动置 PASS。

---

# 4. VNext-1：合同增强（P0）

VNext-1 是唯一 P0。

范围固定为三项：

1. StoryFact-lite；
2. Disclosure Boundary；
3. Frame Purpose / Local Exception。

不扩范围。

---

# 5. P0-1 StoryFact-lite

## 5.1 目的

解决：

- “他是谁”是否已经被确认；
- “药是否造成红痕”目前只是猜测还是事实；
- “白色轮廓是车”是方向性怀疑还是确认；
- 某帧/字幕引用的是哪一个稳定故事事实。

StoryFact-lite 不是知识图谱。

## 5.2 冻结状态集合

只允许：

```text
CONFIRMED
UNKNOWN
UNDECIDED
```

定义：

### CONFIRMED

Story Authority 已确认，可被后续帧作为事实引用。

### UNKNOWN

Story Canon / 作者侧当前没有可确认的事实值。

`UNKNOWN` **不表示“观众不知道”或“角色不知道”**。

观众是否已经获知某个 `CONFIRMED` Fact，必须由 Disclosure Boundary 单独表达；角色知识如果未来需要正式建模，也必须使用独立 Knowledge State，不得复用 StoryFact 状态。

### UNDECIDED

作品本身故意保持不裁决，例如双解释、开放结尾。

冻结约束：

```text
StoryFact Status
≠
Audience Disclosure
≠
Character Knowledge
```

例如：作者已经确认 F007，但当前帧不允许观众知道，应表达为 `status: CONFIRMED` + `must_not_reveal: [F007]`，不得写成 `status: UNKNOWN`。

V1.1 不引入：

- PROBABLE；
- FALSE；
- RETCONNED；
- DERIVED；
- 多层置信度；
- Truth Maintenance System。

需要时以后另开版本。

## 5.3 冻结最小字段

逻辑结构：

```yaml
fact_id: F012
statement: "脚踝存在浅红压痕"
status: CONFIRMED
source:
  kind: story_lock
  ref: "..."
```

必须：

- `fact_id` 稳定；
- `statement` 是人可读语义；
- `status` 使用冻结枚举；
- `source` 可追溯。

## 5.4 存储边界

冻结为：

> StoryFact-lite 属于现有 Story Authority / Story Gates 范围，不新建 StoryFact Service、StoryFact Repository、Story Knowledge Graph。

推荐 canonical 逻辑命名空间：

`story-gates.narrative.story_facts`

实现阶段允许在不改变 Authority 语义的前提下做文件级序列化调整，但不能升级成新的平台服务。

---

# 6. P0-2 Disclosure Boundary

## 6.1 目的

这是 V1.1 最高优先级能力。

真实来源：

《婚礼前夜》第一版实际因为揭露太早而整链返工。

## 6.2 冻结字段

每帧允许：

```yaml
allowed_to_know:
  - F001
  - F004

must_not_reveal:
  - F007
  - F009

supports_fact_ids:
  - F004
```

语义：

### allowed_to_know

当前帧/当前叙述者可以使用的事实。

### must_not_reveal

当前帧不得通过：

- 字幕；
- Prompt；
- 视觉明确证据；
- Review 文案；

提前暴露的事实。

### supports_fact_ids

当前帧负责新增或强化哪些事实。

这是可选字段，但一旦声明，Reviewer 必须能够对其做证据审计。

## 6.3 编译位置

Disclosure Boundary 必须进入 Existing Resolved Frame Contract。

不得只存在于：

- Storyboard Markdown；
- Prompt 文本；
- 人工备注；
- Reviewer prompt。

因为这些位置都无法成为稳定 SHA-bound Contract。

## 6.4 预期 fail codes

冻结语义：

```text
EARLY_REVEAL
UNSUPPORTED_CAUSAL_CLAIM
DISCLOSURE_BOUNDARY_VIOLATION
```

最终 Python 常量命名允许遵循仓库既有风格，但语义不得合并消失。

---

# 7. P0-3 Frame Purpose / Local Exception

## 7.1 真实问题

《婚礼前夜》Frame01：

- 通用 POV 规则：不露脸；
- 该帧真实职责：人物身份锚/首图门面；

导致“全局规则执行正确，但局部叙事职责执行错误”。

《天界普通女生的一天》Frame17：

- 通用 recorder=P01；
- 当前帧真实职责要求 P02 临时持机；

同类问题再次出现。

## 7.2 冻结字段

```yaml
frame_purpose:
  - identity_anchor
  - ordinary_entry

local_exceptions:
  - rule: pov_face_hidden
    action: override
    reason: "Frame01 is the episode identity anchor"
```

最小语义必须包括：

- `frame_purpose`
- `local_exceptions`
- 每个 exception 的 `reason`

不得允许“无理由 override”。

## 7.3 优先级冻结

```text
User Explicit Current Instruction
        >
Frame Local Exception
        >
Frame Purpose Contract
        >
Episode / Series Contract
        >
Global Default
```

注意：

Local Exception 只能覆盖被明确点名的规则。

例如：

Frame01 允许露脸：

不意味着自动允许：

- 海报式摆拍；
- 电影打光；
- 换人物身份；
- 违反 Reality First。

---

# 8. Existing Frame Contract 的 VNext 目标形态

V1.1 不新建合同，只增强当前 `hash_material`。

目标概念结构：

```yaml
hash_material:
  ...

  narrative_semantics:
    frame_purpose:
      - identity_anchor

    allowed_to_know:
      - F001
      - F004

    must_not_reveal:
      - F007

    supports_fact_ids:
      - F004

    local_exceptions:
      - rule: pov_face_hidden
        action: override
        reason: "identity anchor"

  frame_directive:
    narrative_role: ...
    frame_mode: ...
    impact_level: ...
    required_visual_cues: ...

  capture_event: ...
  world_state: ...
  shot_progression: ...
  temporal_state: ...
  wardrobe: ...
  references: ...
```

VNext narrative semantics 必须参与 contract SHA。

原因：

“当前帧允许知道什么”改变后，即使像素目标不变，也已经不是同一个生产合同。

---

# 9. VNext-2：审核增强（P1）

P1 固定为：

1. Reference Semantics；
2. Transition Edge / Assertion；
3. Caption Semantic Fields；
4. Dependency Propagation；
5. Existing Evidence Reviewer Enhancement。

---

# 10. P1-1 Reference Semantics

## 10.1 已经存在的能力

当前 StoryOS 已经具备：

- required anchor 声明；
- `validate_required_anchor_execution()`；
- image scheduler 执行前 fail-close；
- provider receipt；
- reference SHA；
- execution evidence；
- current Episode Pixel Master > Series > Historical reference 的 authority 顺序。

因此 VNext 禁止再实现第二套 Reference Execution Evidence。

## 10.2 真正新增语义

冻结：

```yaml
reference:
  source: "..."
  authority: episode_pixel_master

  inherit:
    - face_identity

  ignore:
    - background
    - wardrobe
    - pose
```

### authority

这张 reference 在当前帧扮演什么权威。

### inherit

允许模型继承的视觉属性。

### ignore

必须主动忽略的参考图属性。

## 10.3 核心规则

一张用于身份的图片：

```text
reference ≠ entire image authority
```

例如：

```text
inherit:
  face_identity

ignore:
  background
  old_clothing
  pose
```

防止参考图把旧环境、旧衣服、旧构图一起污染当前帧。

---

# 11. P1-2 Transition Edge / Assertion

## 11.1 冻结定位

不建 Transition Service。

不建 Transition Repository。

不新增 Transition 状态机。

Transition 是对两个 Existing Resolved Frame Contract 的轻量一致性检查。

## 11.2 首批检查范围

只冻结五类：

```text
recorder
active_device / handoff
location
time
key_prop_state
```

可以从现有：

- World State；
- Capture Event；
- Shot Progression；
- Temporal；
- Wardrobe；
- Frame Contract；

直接派生。

## 11.3 典型错误

```text
RECORDER_STATE_CONFLICT
ACTION_BRIDGE_MISSING
SPATIAL_TRANSITION_UNEXPLAINED
PROP_STATE_DISCONTINUITY
```

## 11.4 非目标

V1.1 不要求：

- 任意两个 Frame 做完整自然语言推理；
- Scene Graph；
- 全局动作模拟器；
- Motion Planner。

---

# 12. P1-3 Caption Semantic Fields

## 12.1 为什么从 P0 下调

真实审计确认 StoryOS 当前已经有：

- Voice Contract；
- 第一人称口语；
- knowledge-boundary test；
- delete-subtitle test；
- read-aloud；
- clue-payoff；
- caption-image actual-pixel audit；
- subtitle SHA binding；
- `safe_zone_override_reason`。

因此没有必要建立 Caption Platform。

## 12.2 只补三个字段

```yaml
role: reaction

supports:
  - F004

must_not_reveal:
  - F007
```

### role

字幕功能，例如：

- setup
- reaction
- clarification
- emotional_turn
- payoff

不需要大枚举，首版只用于 QA。

### supports

字幕主要支持哪些 StoryFact。

### must_not_reveal

字幕层的明确防提前揭露边界。

## 12.3 边界

Caption 不要求：

> 每一句话都必须由当前图片直接证明。

允许：

- 画面外旁述；
- 主观感受；
- 当前角色已知背景。

禁止的是：

> 把画面外旁述伪装成当前帧已经确认的视觉事实。

---

# 13. P1-4 Existing Evidence Reviewer Enhancement

## 13.1 已存在

StoryOS 当前已经有：

- `required_visual_cues`；
- frame semantic review；
- actual-pixel critic；
- caption-image audit；
- visual profile review；
- evidence gate；
- Story Semantic Trace；
- Story DNA Trace。

所以不建 Evidence Platform。

## 13.2 VNext 增强

Reviewer 只增加消费：

- `supports_fact_ids`
- `must_not_reveal`
- `frame_purpose`
- `local_exceptions`
- Reference inherit/ignore

并输出：

```text
required evidence observed?
forbidden evidence observed?
disclosure boundary respected?
frame purpose satisfied?
reference scope respected?
```

## 13.3 不引入新 Authority

Review observation 是 evidence。

不允许 Reviewer 输出成为新的 Story Authority。

---

# 14. P1-5 Dependency Propagation

## 14.1 复用现有能力

StoryOS 已有：

- Frame Contract SHA；
- source binding；
- Visual Lock admission SHA；
- dirty-only review；
- candidate binding；
- stale detection。

VNext 只把新增语义纳入现有 fingerprint。

## 14.2 冻结 dirty 规则

### StoryFact statement/status 改变

只 invalidate：

- 引用该 Fact 的 frames；
- 依赖这些 frames 的 caption/review/prompt/output。

### Frame disclosure 改变

只 invalidate 当前 frame 及明确 dependent artifacts。

### Frame purpose/local exception 改变

当前帧 Contract 必须 dirty。

### Reference inherit/ignore 改变

所有使用该 reference semantic binding 的帧 dirty。

## 14.3 已知现存问题

《婚礼前夜》曾暴露：

Frame01 更新后：

- cover；
- contact-sheet；
- snapshot；
- delivery；

没有自动全部失效。

这仍属于 P1 dependency propagation 闭环范围。

---

# 15. VNext-3：智能化（P1.5 / P2）

VNext-3 不进入第一轮实现。

---

# 16. RenderObservation 延后

## 16.1 V1.1 决策

**DEFERRED**

当前不增加独立：

```text
image
  ↓
RenderObservation Object
  ↓
Evidence Verifier
```

## 16.2 原因

当前 actual-pixel Reviewer 已足以直接检查：

- required cue；
- visual evidence；
- anatomy；
- caption support；
- profile fidelity；
- reference execution。

真实 Episode 没有证明独立 Observation Object 是当前 P0/P1 必需。

## 16.3 未来重新开启条件

满足任一项再重新评审：

1. 多 Reviewer 需要共享同一套像素事实；
2. Observation 要进入 Experience Store；
3. Repair Router 需要稳定结构化 observation；
4. 同一图片被多个 downstream gate 重复 Vision 读取，成本明显失控。

在此之前不实现。

---

# 17. RAG / Recall / Rerank 的位置

此前讨论过：

- 问题重写；
- 路由策略；
- 数据结构化；
- 召回；
- 重排。

V1.1 冻结结论：

这些属于**以后 Agent / Memory / Experience 的智能检索层**，不是 Narrative Contract P0。

StoryFact-lite 不依赖向量数据库。

Disclosure Boundary 不依赖 RAG。

Frame Purpose 不依赖 RAG。

因此当前不把复杂 RAG 引入 VNext-1 / VNext-2。

---

# 18. Narrative QA Fixture 策略

## 18.1 当前 Fixture 是回归事实，不是生产 Gate

路径：

`tests/narrative/fixtures/`

它们负责防止：

- 修复后重新退化；
- 新规则误杀真实正例；
- 边界例被粗暴二值化。

## 18.2 三种 Fixture

### positive

应该通过。

防止新规则过严。

### negative

应该失败。

优先来自历史真实故障。

### boundary

不能机械判失败。

用于降低误报。

## 18.3 Fixture 不可反向迁就实现

规则冻结：

> 不能为了让新实现测试全绿，随意修改真实 Fixture 的 expected。

如果实现与真实历史事实冲突：

先修实现。

---

# 19. Golden Episode Regression

当前：

`reports/golden-episode-registry.json`

仍为：

```json
{
  "episodes": []
}
```

因此 V1.1 区分：

```text
Narrative Fixtures
    ≠
Golden Episode Registry
```

Fixture 可以先用于局部语义回归。

整集 Golden Regression 需另行闭环 W-10。

本 VNext 文档不擅自填充 Golden Registry。

---

# 20. 明确不做

V1.1 Final/Frozen 明确禁止在本版本范围内建设：

1. Narrative Platform；
2. Story Bible Service；
3. StoryFact Repository / Graph Database；
4. ShotContract 第二 Authority；
5. Transition Service；
6. Transition Repository；
7. Evidence Platform；
8. 第二套 Story Semantic Trace；
9. 第二套 Reference Execution Evidence；
10. 第二套 Visual Reality System；
11. 立即实现 RenderObservation；
12. 立即引入复杂 RAG；
13. 为 VNext 单独新建 Workflow Engine；
14. 为 VNext 单独新建 Scheduler；
15. 为 VNext 改写现有 Production Ledger Authority。

如果实施中出现以上方向，必须视为超出 V1.1 Frozen Scope，重新做架构评审。

---

# 21. 分阶段实施冻结

原 VNext 三阶段结构保留，但内容收敛。

## VNext-1：Contract Enhancement

优先级：P0

只实现：

```text
StoryFact-lite
Disclosure Boundary
Frame Purpose / Local Exception
Resolved Frame Contract integration
SHA / dirty integration
```

### 首阶段默认模式

`SHADOW / REPORT ONLY`

不能第一天就直接成为 Production hard gate。

---

## VNext-2：Review Enhancement

优先级：P1

实现：

```text
Reference inherit / ignore / authority
Transition assertions
Caption role / supports / must_not_reveal
Evidence Reviewer consumes VNext semantics
Dependency propagation
```

---

## VNext-3：Intelligence

优先级：P1.5/P2

候选：

```text
RenderObservation
Experience Store observation ingestion
failure-to-repair routing
semantic recall/rerank
RAG
```

必须由真实生产成本/缺陷证据触发，不因“架构看起来完整”而实施。

---

# 22. 实施准入条件

在开始 VNext-1 代码实施前，必须满足：

## 22.1 设计准入

- 本 V1.1 文档保持 Final/Frozen；
- `reports/Story_OS_Narrative_QA_真实剧集审计_20260918.md` 不存在相反结论；
- 25 条 Fixture 仍可读取且 expected 无冲突。

## 22.2 工作区准入

由于当前 StoryOS 工作区存在大量并行修改：

实施前必须：

- 明确当前代码基线；
- 不混入无关 staged/unstaged 改动；
- 不执行 reset/restore/clean 覆盖其他并行工作；
- VNext 改动应按独立提交域处理。

## 22.3 架构准入

实现方案必须证明：

- 没有新建第二套 Frame Authority；
- 没有新建第二套 Evidence Authority；
- 没有绕过 Production Ledger；
- 没有让一个 frame 的语义修改无条件 invalidate 全 Episode；
- 没有破坏旧 Episode 的 versioned compatibility。

---

# 23. VNext-1 测试验收冻结

未来实施 VNext-1 时，最低验收必须包括：

## 23.1 Schema Tests

- StoryFact 三状态合法；
- 非法状态 fail-close；
- Fact ID 唯一；
- frame 引用不存在 Fact ID 时 FAIL；
- local exception 没 reason 时 FAIL。

## 23.2 Disclosure Tests

至少覆盖：

- 《婚礼前夜》早揭露负例；
- 因果尚未确认却被字幕宣布；
- UNKNOWN 不得作为 CONFIRMED 使用；
- UNDECIDED 不得被 Reviewer 强行裁决；
- allowed_to_know 正例。

## 23.3 Frame Purpose Tests

至少覆盖：

- Frame01 身份锚局部露脸例外；
- exception 只覆盖目标规则；
- exception 不得顺带放开 Reality First / Identity 等其他约束；
- recorder 局部切换。

## 23.4 Contract Hash Tests

- 当前帧 narrative semantics 变化 → 当前 Contract SHA 变化；
- 无关帧 Contract SHA 不变；
- prompt package 使用新 Contract SHA；
- stale review/candidate 不得继续 PASS。

## 23.5 Fixture Regression

25 条 Narrative Fixture：

- positive 不被误杀；
- negative 能被识别；
- boundary 不被粗暴强制 FAIL。

---

# 24. VNext-2 测试验收冻结

## 24.1 Reference

- `protagonist_identity` required anchor 仍必须真实执行；
- `P02_face` 缺失仍 FAIL；
- inherit=face_identity 时不得继承旧背景；
- ignore=wardrobe 时不能因为 reference 旧衣服覆盖当前 Wardrobe Contract；
- authority 顺序不回退。

## 24.2 Transition

- Frame17 P02 recorder / Frame18 P01 recorder 正例；
- Capture Event 与 World State recorder 冲突负例；
- device handoff 正例；
- 无动作桥的大空间跳转负例；
- time/prop state continuity。

## 24.3 Caption

- 画面外 narration 正例；
- unsupported causal claim 负例；
- visual duplication warning；
- knowledge boundary 不回退；
- caption/image support 继续有效。

## 24.4 Dirty Propagation

- 改一个 reference semantic → 只影响使用它的 frames；
- 改一个 disclosure → 只影响相应 frame/dependencies；
- 未变化的 SHA-bound PASS 不进行 stochastic re-review；
- cover/snapshot/delivery stale 能被显式发现。

---

# 25. Production Gate 激活条件

VNext 不允许直接从“代码写完”跳到 Production hard gate。

必须经过：

```text
1. Unit / Fixture
        ↓
2. Shadow
        ↓
3. Real Episode Audit
        ↓
4. False Positive Review
        ↓
5. Canary
        ↓
6. Hard Gate
```

## 25.1 Shadow 阶段

只生成：

- issue code；
- frame；
- expected / observed；
- advisory；

不阻塞生产。

## 25.2 Hard Gate 最低条件

至少满足：

- 25 条 Fixture 全部符合 frozen expected；
- 《婚礼前夜》真实早揭露能被拦截；
- 天界普通女生 recorder conflict 能被拦截；
- EP003 required reference 回归不倒退；
- 《泔水与金牌》boundary case 不被误杀；
- 当前 tests/platform + tests/system 全量回归不产生 VNext 引入的新失败；
- real Episode false positive 达到可接受水平后再人工批准激活。

---

# 26. Versioned Compatibility

VNext 必须 version-gated。

推荐规则：

```text
new Episode with VNext semantics
    → VNext required

legacy Episode
    → legacy contract remains interpretable

legacy Episode explicitly migrated
    → VNext evidence must be real
    → no fake compatibility PASS
```

不得批量回写历史 StoryFact/Disclosure 来“补齐格式”。

历史没有真实证据就是：

`Historical Evidence Missing`

而不是 PASS。

---

# 27. 与现有 Agent / Runtime / Scheduler 的关系

V1.1 不改变 StoryOS 平台大架构。

## Agent

未来 Story/Storyboard Agent 负责生成候选 StoryFact / Disclosure / Purpose。

但最终必须写入现有 Authority 后才能生效。

## Runtime

Runtime 只执行已冻结 Contract。

不在 Runtime 中重新解释剧情。

## Scheduler

Scheduler 不理解“故事好不好”。

只消费：

- dirty frame；
- dependencies；
- gate result；
- retry/repair action。

## Reviewer

Reviewer 负责判断实际输出是否满足 Contract。

Reviewer 不成为新 Authority。

---

# 28. Frozen Data Flow

```text
User Intent
   ↓
Story Lock
   ↓
StoryFact-lite
   ↓
Storyboard
   ↓
Story Gates / Frame Narrative Semantics
   ↓
Existing Resolved Frame Contract
   ├─ environment
   ├─ capture event
   ├─ world state
   ├─ character visual
   ├─ shot progression
   ├─ temporal
   ├─ wardrobe
   ├─ references
   └─ narrative semantics   ← VNext
         ├─ frame_purpose
         ├─ allowed_to_know
         ├─ must_not_reveal
         ├─ supports_fact_ids
         └─ local_exceptions
   ↓
Prompt Package
   ↓
Image / Media Model
   ↓
Existing Actual-Pixel Review
   ↓
Evidence / Ledger / Gate
   ↓
Release
```

---

# 29. V1.1 冻结后的实现顺序

未来真正开始开发时，固定顺序：

1. **Fixture loader / schema validation**
2. **StoryFact-lite**
3. **Disclosure Boundary**
4. **Frame Purpose / Local Exception**
5. **Frame Contract hash integration**
6. **Shadow reviewer**
7. **Reference Semantics**
8. **Transition assertions**
9. **Caption semantic metadata**
10. **Dependency propagation closure**
11. **Canary / Gate activation**

不能先做：

- RenderObservation；
- RAG；
- 新 Agent Router；
- 新数据库；

再回来补 P0 合同。

---

# 30. Frozen Acceptance Definition

VNext V1.1 的“完成”不是代码文件存在。

最终定义：

```text
同一个故事事实
从 Story
→ Frame
→ Prompt
→ Pixel
→ Caption
→ Review

都能回答：

1. 这是什么事实？
2. 这一帧现在允许知道它吗？
3. 这一帧为什么承担这个职责？
4. 画面实际提供了什么证据？
5. Reference 哪些属性有权继承？
6. 修改它后，真正受影响的是哪些帧？
```

并且这些答案：

- 不依赖人工记忆；
- 不依赖 Prompt 临时文字；
- 不创建第二套 Authority；
- 能进入 SHA / Evidence / Dirty / Review 链；
- 能被真实 Fixture 回归。

达到以上条件，才视为 VNext Narrative Semantics 完整闭环。

---

# 31. Final / Frozen 决策表

| 项目 | 决策 | 优先级 | 是否新建独立系统 |
|---|---|---:|---|
| StoryFact-lite | 实施 | P0 | 否 |
| Disclosure Boundary | 实施 | P0 | 否 |
| Frame Purpose / Local Exception | 实施 | P0 | 否 |
| Existing Frame Contract 增强 | 实施 | P0 | 否 |
| Reference inherit/ignore/authority | 实施 | P1 | 否 |
| Transition assertions | 实施 | P1-lite | 否 |
| Caption role/supports/must_not_reveal | 实施 | P1-lite | 否 |
| Evidence Reviewer enhancement | 实施 | P1 | 否 |
| Dependency Propagation | 实施 | P1 | 否 |
| RenderObservation | 延后 | P1.5/P2 | 暂不 |
| RAG / Recall / Rerank | 延后 | P2 | 暂不 |
| Narrative Platform | 不做 | - | 禁止 |
| ShotContract 第二权威 | 不做 | - | 禁止 |
| Transition Service | 不做 | - | 禁止 |
| Evidence Platform | 不做 | - | 禁止 |
| 第二套 Reference Execution Evidence | 不做 | - | 禁止 |

---

# 32. 冻结声明

自本文起：

`StoryOS_VNext_叙事语义增强落地方案_V1.1_Final_Frozen_20260918.md`

作为本轮 VNext Narrative Semantics 的正式设计基线。

后续：

- 小的字段实现细节可在不改变语义的情况下调整；
- P0/P1 优先级不得无证据重排；
- 不得新增第二套 Authority；
- 不得扩大为 Narrative Platform；
- 新增大模块必须有新的真实生产问题证据并重新评审；
- RenderObservation / RAG 默认保持 Deferred。

本文件冻结的是：

**架构边界、能力范围、优先级、核心语义、实施顺序和验收原则。**

不是冻结 Python 内部函数名或代码组织细节。

---

# 33. 一句话最终方案

> **VNext 不重做 StoryOS，而是在现有 Resolved Frame Contract 上补齐“事实、揭露边界、帧职能例外、Reference 继承语义”，再让现有 Reviewer、SHA dirty 和 Evidence Gate 消费这些语义；先把 25 条真实 Fixture 跑稳，再决定是否进入生产硬门禁。**

