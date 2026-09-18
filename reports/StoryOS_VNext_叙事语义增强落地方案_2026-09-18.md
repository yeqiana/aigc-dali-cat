# StoryOS VNext 叙事语义增强落地方案

> 版本：V1.0  
> 日期：2026-09-18  
> 适用分支建议：`story-platform-v3` 后续 VNext 迭代分支  
> 参考来源：POV-AI-Storytelling 方法论吸收评审  
> 核心原则：**不新增顶层平台，不重构 Runtime，不改 Scheduler/Agent Orchestrator 主架构，只增强现有 Story Lock、Frame Contract、Reference、Caption、Review、Tests。**

---

## 1. 背景

StoryOS V3 已经具备较完整的平台与生产闭环能力，包括：

- Story / Story Lock
- Storyboard
- Character Contract
- Visual Lock
- Resolved Frame Contract
- Prompt Compiler
- Reference / Identity Anchor
- Async Runtime
- Image Scheduler / Batch Scheduler
- Frame Semantic Review
- Rolling Review / Final Review
- TECH_FAILED 分类与 Repair
- Event / Trace / Artifact
- Memory / Experience Store / Advisor
- Workflow / Agent Runtime

当前主要短板已经不是“平台能力不足”，而是：

> **系统虽然能生产、调度、审核，但对“这一帧为什么存在、应该表达什么、不能提前表达什么、字幕为什么存在、前后两帧为什么能连起来”的结构化理解仍不够强。**

因此本次迭代不再增加新的大平台，而是进行一次“内容语义升级”。

---

# 2. 总体目标

本次升级最终只围绕三类权威结构展开：

```text
Story Canon
权威故事状态

        ↓

Frame Production Contract
权威单帧生产合同

        ↓

Narrative QA
叙事验收
```

最终目标：

```text
Story
 ↓
Story Canon
 ↓
Storyboard
 ↓
Frame Production Contract
 ↓
Prompt Compiler
 ↓
Generation
 ↓
Narrative QA
 ↓
Repair / Reverify
 ↓
Production Passed
```

---

# 3. 非目标

本版本明确不做：

- 不新增 `NarrativePlatform`
- 不新增 `StoryBibleService`
- 不新增新的 Workflow Engine
- 不新增新的 Scheduler
- 不修改 WebCodex / Agent 并发调度机制
- 不新建另一套 Visual Lock
- 不新建独立 Evidence Platform
- 不把 Narrative Graph 做成大型知识图谱
- 不立刻引入复杂向量 RAG
- 不把 Transition 做成独立 Service / Repository / State Machine
- 不推翻现有 Frame Contract
- 不推翻现有 Story Lock

本次原则：

> **增强现有合同，不平行造新系统。**

---

# 4. 最终吸收范围

## 4.1 P0：必须落地

| 编号 | 能力 | 类型 | 落点 |
|---|---|---|---|
| P0-01 | Story Fact 状态 | 增强 | Story Lock / Story Canon |
| P0-02 | Frame Narrative 字段 | 增强 | Resolved Frame Contract |
| P0-03 | Expected Evidence | 增强 | Frame Contract / Reviewer |
| P0-04 | Transition Edge | 轻量新增 | Frame Contract |
| P0-05 | Caption Narrative Role | 增强 | Caption |
| P0-06 | Reference inherit / ignore / authority | 增强 | Reference Resolver |
| P0-07 | Semantic / Render 状态分离 | 增强 | Visual/Review 状态 |

## 4.2 P1：P0 稳定后落地

| 编号 | 能力 | 类型 |
|---|---|---|
| P1-01 | Transition Review | 新增审核维度 |
| P1-02 | Sequence Review 结构化维度 | 增强 |
| P1-03 | Narrative QA 正反例 Fixtures | 新增测试资产 |
| P1-04 | Dirty Set / Affected Frames 扩展 | 增强 |
| P1-05 | Repair Router 根因路由增强 | 增强 |

## 4.3 P1.5 / 条件触发

- Render Observation 独立对象
- 跨 Reviewer 共享观测
- 自动错误统计
- Observation → Experience Store

只有当以下需求真实出现后再升级：

- Reviewer 重复解析同一图片成本过高
- 多 Reviewer 需要共享同一“成图事实”
- Repair Router 需要依赖结构化成图事实
- Experience Store 需要消费成图观测

## 4.4 P2：后续智能化

- 人物 Knowledge State
- Narrative Dependency Graph 深化
- Structured Retrieval
- Query Rewrite
- Rerank
- Experience RAG
- Similar Episode Retrieval

---

# 5. 核心设计一：Story Canon

## 5.1 当前问题

当前 Story Lock 已经能够冻结故事，但主要仍偏“文本/文档级确定”。

缺少对以下状态的明确表达：

```text
已经确定
尚未决定
明确未知
已确定但暂不能向观众揭示
```

LLM 容易把“没有写”误认为“可以补全”。

---

## 5.2 第一版只做轻量 Fact

不做知识图谱。

建议：

```yaml
story_canon:
  facts:
    - id: FACT_P02_IDENTITY
      value: "P02 是旧照片中的男人"
      state: CONFIRMED

      disclosure:
        audience_status: HIDDEN
        reveal_after_frame: F19
```

允许：

```text
CONFIRMED
UNKNOWN
UNDECIDED
```

不要把 `UNDISCLOSED` 放进 `state`。

原因：

```text
CONFIRMED / UNKNOWN / UNDECIDED
描述作者是否确定

HIDDEN / REVEALED
描述观众是否应该知道
```

两个维度必须分开。

---

## 5.3 建议 Schema

```yaml
fact:
  id: string
  type: CHARACTER | PROP | RELATION | EVENT | WORLD | OTHER

  value: any

  state:
    CONFIRMED | UNKNOWN | UNDECIDED

  disclosure:
    audience_status:
      HIDDEN | REVEALED | NOT_APPLICABLE

    reveal_after_frame:
      optional frame id

  source:
    story_lock | user | runtime_request | accepted_proposal

  allow_agent_inference:
    true | false
```

默认：

```text
UNKNOWN / UNDECIDED
→ allow_agent_inference = false
```

避免 Agent 自动补事实。

---

# 6. 核心设计二：升级 Resolved Frame Contract

## 6.1 原则

不新增平行的 ShotContract。

直接升级：

```text
Resolved Frame Contract
```

让它同时成为：

```text
视觉合同
+
叙事合同
+
证据合同
+
字幕合同
+
Reference 合同
+
Transition 边
```

---

## 6.2 建议结构

```yaml
frame:
  id: F08

  narrative:
    task: "发现旧照片"
    preconditions:
      - FACT_ROOM_ENTERED

    state_change:
      - P01_KNOWS_OLD_PHOTO_EXISTS

    intended_inference:
      - "照片中的男人以前出现过"

  evidence:
    required:
      - id: E01
        description: "男人左手腕存在黑色手绳"

      - id: E02
        description: "照片日期可辨认"

    optional:
      - id: E03
        description: "旧照片存在折痕"

    forbidden:
      - id: E04
        description: "P02 完整正脸不可清晰出现"

  caption:
    role: CLARIFY
    supports:
      - E01

    must_not_reveal:
      - FACT_P02_IDENTITY

  references:
    - ref_id: P02_FACE
      inherit:
        - identity
        - face_shape
        - hair

      ignore:
        - clothes
        - pose
        - background

      authority:
        identity: 100

  transition_in:
    from: F07

    continuity:
      time: CONTINUOUS
      wardrobe: SAME
      location_delta: ROOM_DOOR_TO_DESK

    required_bridge:
      - "P01 已走到桌边"

  transition_out:
    to: F09

    required_bridge:
      - "P01 已拿起照片"
```

---

# 7. Narrative 字段设计

每帧第一版只要求：

```text
task
preconditions
state_change
intended_inference
```

不要第一版就加入复杂：

```text
emotion graph
knowledge graph
multi-agent belief state
causal graph
```

保持轻量。

---

# 8. Evidence Contract

## 8.1 目标

从：

```text
Prompt 写对了
=
故事表达对了
```

升级为：

```text
Expected Evidence
↓
实际图片
↓
Reviewer 核对
↓
Evidence Result
```

---

## 8.2 第一版不做完整 Render Observation

Reviewer 直接输出：

```yaml
evidence_result:
  frame: F08

  checks:
    - evidence_id: E01
      result: PASS
      confidence: 0.94

    - evidence_id: E02
      result: FAIL
      reason: "日期不可辨认"

  overall:
    FAIL
```

这已经足够支持 P0。

---

# 9. Transition Contract

## 9.1 为什么必须做

必须区分：

```text
Frame 23 PASS
Frame 24 PASS
```

和：

```text
Frame 23 → Frame 24 PASS
```

单帧正确不代表前后镜头合理。

---

## 9.2 实现原则

Transition 不做独立 Service。

只作为：

```text
Frame N → Frame N+1
```

的关系字段。

建议：

```yaml
transition_out:
  to: F09

  required_bridge:
    - "主角已经停下自行车"

  continuity:
    time_delta: "0-2min"
    wardrobe: SAME
    prop_state: SAME

  spatial:
    from: ROAD
    to: TABLE
```

---

## 9.3 第一版校验项

只检查：

- Action Bridge
- Time
- Location
- Wardrobe
- Key Prop State

不要第一版做复杂空间拓扑。

---

# 10. Caption Contract

## 10.1 当前已有能力保留

现有：

- 左中安全区
- 3 行内
- 口语化
- 不挡关键主体
- Voice Card

全部保留。

---

## 10.2 本次只增加三个语义字段

```yaml
caption:
  role: CLARIFY

  supports:
    - EVIDENCE_03

  must_not_reveal:
    - FACT_12
```

第一版 `role` 可使用：

```text
EMOTION
BRIDGE
CLARIFY
VOICE
TIME
QUESTION
PAYOFF
EXPOSITION
```

但不要求每一帧一定有字幕。

---

## 10.3 重点审核规则

Reviewer 应识别：

```text
画面没有表达成功
↓
字幕是否在替画面解释全部故事
```

典型失败：

```text
EXPOSITION_OVERLOAD
EARLY_REVEAL
CAPTION_VISUAL_DUPLICATION
TEMPORAL_TEXT_CONFLICT
```

---

# 11. Reference Contract

这是本批改造 ROI 最高的能力之一。

---

## 11.1 当前问题

目前已经有：

- Identity Anchor
- Reference Evidence
- Reference Binding
- Required Reference Anchor

但还需要回答：

```text
这张 Reference 到底固定什么？
哪些东西绝对不要继承？
多个 Reference 冲突听谁的？
```

---

## 11.2 Schema

```yaml
reference:
  ref_id: P01_FACE
  artifact: p01_face_v3.png

  inherit:
    - identity
    - face_shape
    - hairstyle

  ignore:
    - pose
    - clothes
    - background
    - lighting

  authority:
    identity: 100
```

其他 Reference：

```yaml
reference:
  ref_id: CLOTHES_F01

  inherit:
    - jacket
    - shirt
    - palette

  ignore:
    - face
    - pose
    - environment

  authority:
    wardrobe: 90
```

---

## 11.3 Prompt Compiler 行为

Prompt Compiler 不再简单：

```text
references = [...]
```

而应该根据：

```text
identity authority
wardrobe authority
location authority
composition authority
```

组装当前 Frame 的最终约束。

---

# 12. Semantic / Render 双状态

避免：

```text
设定已确定
=
成图已正确
```

建议：

```yaml
identity:
  semantic_status:
    LOCKED

  render_status:
    PENDING | MATCHED | DEVIATED | FAILED
```

类似：

```yaml
wardrobe:
  semantic_status: LOCKED
  render_status: MATCHED
```

不新增新的 Lock Service。

仅增强现有对象状态。

---

# 13. Narrative QA

## 13.1 三层审核

```text
Level 1
Single Frame Review

Level 2
Transition Review

Level 3
Sequence Review
```

---

## 13.2 Single Frame Review

检查：

- Narrative Task
- Expected Evidence
- Forbidden Evidence
- Caption
- Reference
- Character
- Wardrobe
- POV
- Prop
- Aspect Ratio
- Visual Style

---

## 13.3 Transition Review

检查：

- 动作是否跳变
- 时间是否冲突
- 地点是否跳变
- 衣服是否连续
- 关键道具状态是否连续

---

## 13.4 Sequence Review

检查：

- 因果
- 信息增量
- 重复
- 节奏
- 伏笔
- 回收
- Reveal Timing
- Ending Payoff

第一版不要求全部自动阻断。

可先：

```text
PASS
WARNING
FAIL
```

---

# 14. Repair Router 增强

现有 Repair 能力保留。

新增根因分类：

```text
REFERENCE_REBIND
PROMPT_RECOMPILE
REGENERATE
LOCAL_EDIT
CAPTION_REPAIR
STORYBOARD_REPAIR
CROP
OUTPAINT
ACCEPT_DEVIATION
```

示例：

```text
身份锚没绑定
→ REFERENCE_REBIND

Prompt 约束缺失
→ PROMPT_RECOMPILE

人物严重漂移
→ REGENERATE

字幕时间错
→ CAPTION_REPAIR

23 → 24 行为跳跃
→ STORYBOARD_REPAIR

比例错但可裁切
→ CROP

背景路人不影响剧情
→ ACCEPT_DEVIATION
```

---

# 15. Narrative QA Fixtures

## 15.1 目的

以后改：

```text
Story Agent
Storyboard Agent
Prompt Compiler
Reviewer
```

除了普通测试：

```text
tests passed
```

还要能跑：

```text
Narrative Regression
```

---

## 15.2 目录建议

```text
tests/
  narrative/
    plot/
      positive/
      negative/

    caption/
      positive/
      negative/

    evidence/
      positive/
      negative/

    transition/
      positive/
      negative/

    reference/
      positive/
      negative/
```

---

## 15.3 Fixture 基本格式

```yaml
case_id: CAPTION_001

input:
  frame: ...

expected:
  result: FAIL
  issue_type:
    EARLY_REVEAL

bad_example:
  "原来他就是一直偷拍我的那个人。"

reason:
  "该事实必须在 F19 后才能揭示"
```

---

# 16. 第一批真实 Fixture 来源

优先把 StoryOS 已经暴露过的问题沉淀进去：

- Required Reference Anchor 未正确注入
- P02 face / group identity 绑定问题
- TECH_FAILED 与内容失败分类混淆
- network error 被 100x100 覆盖
- Frame03 accepted issue
- 连续帧身份漂移
- 字幕补绑问题
- Reference 存在但继承语义错误
- Frame 单独正确但前后跳跃
- Caption 提前剧透
- Caption 机械重复画面

原则：

> 已经踩过的坑，不再只存在报告里，逐渐转成回归资产。

---

# 17. Dependency / Dirty Set

P1 增强。

当以下对象变化：

```text
Story Fact
Reference
Caption Rule
Visual Profile
Frame Contract
```

需要计算：

```text
Affected Frames
Affected Transitions
Affected Review Gates
```

例如：

```text
P01_FACE changed
↓
F01 / F03 / F06 / F19 dirty
↓
对应 Transition dirty
↓
重新 Prompt Compile
↓
重新 Review
```

复用现有：

- SHA
- Contract Binding
- Artifact Fingerprint
- Approval Invalidation

不重新做一套依赖平台。

---

# 18. 与 RAG / Memory 的边界

必须明确：

```text
Canonical Contract
>
Retrieved Experience
```

即：

```text
Hard Truth
→ Story Canon / Frame Contract

Soft Experience
→ Memory / Experience Store / RAG
```

例如：

```text
Frame Contract：
P01 穿蓝色外套
```

即使 Experience Store 召回：

```text
相似剧集通常穿红色更醒目
```

也不能覆盖权威合同。

RAG 后续主要负责：

- 历史失败经验
- 相似 Episode
- 相似 Story DNA
- 生产经验
- Prompt 修复经验
- Reviewer 经验

不用于替代确定性 Story Fact。

---

# 19. 与 Agent 调度升级的关系

本方案与正在规划的：

- Planner
- Router
- Agent Orchestrator
- 主调度
- 问题重写
- 召回
- 重排

保持解耦。

关系：

```text
Agent Runtime
负责：
谁执行 / 何时执行 / 怎么调度

Narrative Semantic Layer
负责：
执行时到底什么才算正确
```

两个方向可以并行设计。

本方案不要求修改当前 Scheduler。

---

# 20. 实施版本拆分

## VNext-1：合同增强

目标：

> 把“创作意图”变成机器可理解的数据。

实施：

1. Story Fact state
2. Disclosure
3. Frame narrative task
4. Expected Evidence
5. Forbidden Evidence
6. Caption role
7. Reference inherit / ignore / authority
8. Transition edge
9. Semantic / Render 双状态

### 验收

- 老 Episode 不迁移也能继续跑
- 新字段全部 optional
- 新 Episode 可生成增强 Frame Contract
- Prompt Compiler 可消费 Reference Semantics
- Reviewer 可核对 Expected Evidence
- 不影响当前全自动生产主流程

---

# 21. VNext-2：审核增强

目标：

> 从“图片看起来没问题”升级为“故事正确表达”。

实施：

1. Transition Review
2. Sequence Review 结构化
3. Caption Semantic Review
4. Evidence Review
5. Narrative QA Fixtures
6. Repair Root Cause 分类

### 验收

能自动识别至少以下问题：

- 单帧正确但前后跳镜
- Caption 提前剧透
- Caption 与时间冲突
- Evidence 缺失
- Forbidden Evidence 泄露
- Reference 继承错误
- Story Fact UNKNOWN 被 AI 擅自补全

---

# 22. VNext-3：智能化

目标：

> 利用前两版的结构化事实做自动决策。

候选：

- Render Observation
- Dependency Propagation
- 自动 Repair Router
- Structured Retrieval
- Query Rewrite
- Rerank
- Experience RAG
- Similar Episode Retrieval

本阶段不提前实施。

---

# 23. 数据兼容策略

所有新增字段第一版必须：

```text
optional
```

原则：

```text
旧 Episode
→ 继续按旧逻辑生产

新 Episode
→ 生成增强合同

旧 Episode 被重新编辑
→ 按需增量升级
```

禁止：

```text
全量强制迁移
```

第一版只做兼容读取。

---

# 24. Feature Flag

建议：

```yaml
narrative_semantics:
  enabled: false

  story_fact:
    enabled: true

  frame_evidence:
    enabled: true

  transition_review:
    enabled: false

  caption_semantics:
    enabled: true

  reference_semantics:
    enabled: true
```

先：

```text
Shadow
↓
Warning
↓
Soft Gate
↓
Hard Gate
```

不要直接阻断生产。

---

# 25. Shadow 验证

推荐先用真实 Episode 做 Shadow：

```text
现有生产决策
vs
新 Narrative QA 决策
```

记录：

```text
false_positive
false_negative
missed_issue
new_issue_detected
```

Shadow 阶段新规则：

```text
只记录
不阻断
```

达到稳定阈值后再逐步启用 Gate。

---

# 26. 推荐验证样本

建议至少选三类：

## A. 已成功生产 Episode

用于检查：

```text
新规则是否误杀
```

## B. 历史暴露过问题的 Episode

用于检查：

```text
是否能重新发现真实问题
```

## C. 新 Episode

用于检查：

```text
新合同是否影响正常生产效率
```

---

# 27. 测试策略

除现有：

```text
Unit
Integration
System
Regression
```

增加：

```text
Narrative Positive
Narrative Negative
Boundary Case
False Positive
False Negative
```

每条新规则必须至少有：

```text
1 正例
1 反例
1 边界例
```

高风险规则建议：

```text
2+ 正例
3+ 反例
```

---

# 28. 验收门槛

## VNext-1

必须满足：

- 现有 production pipeline 无回归
- 旧 Episode 可继续运行
- Frame Contract 新字段可选
- Reference Resolver 可解析 inherit / ignore / authority
- Reviewer 可消费 Expected Evidence
- UNKNOWN 不被自动补事实
- tests/platform 全绿
- tests/system 全绿

## VNext-2

必须满足：

- Transition Review 可发现已知跳镜 fixture
- Caption Review 可发现提前揭示
- Evidence Review 可发现关键证据缺失
- Narrative Fixture 回归稳定
- 误报率在可接受范围
- Shadow 结果有证据报告

---

# 29. 风险评审

## 风险 1：Schema 膨胀

控制：

```text
第一版字段必须少
不做知识图谱
不做复杂人物认知状态机
```

## 风险 2：Reviewer 误报增加

控制：

```text
Shadow → Warning → Gate
```

## 风险 3：Prompt 过长

控制：

```text
Frame Context Resolver
只注入当前镜头相关事实
```

## 风险 4：状态互相打架

控制：

严格分离：

```text
Fact State
Disclosure State
Semantic Status
Render Status
Review Status
```

不混进一个枚举。

## 风险 5：重复建设

控制：

不新增：

```text
Narrative Platform
Story Bible Service
Evidence Service
Transition Service
```

优先扩展现有模块。

---

# 30. 文件影响范围建议

实际实施前先扫描工作区确认真实路径。

预期主要影响：

```text
story/
story_lock/
storyboard/
frame_contract/
prompt/
reference/
review/
caption/
tests/
```

以及相关：

```text
schema
serializer
validator
CLI
report
```

不应大面积修改：

```text
runtime scheduler
workflow engine
agent registry
memory core
platform repository
```

---

# 31. 推荐任务拆分

## Task 1
Story Canon / Fact Schema

## Task 2
Frame Contract Narrative + Evidence

## Task 3
Reference Semantics

## Task 4
Caption Semantic Fields

## Task 5
Transition Edge

## Task 6
Reviewer Evidence Check

## Task 7
Narrative Fixtures

## Task 8
Shadow Validation

其中：

```text
Task 1 → Task 2
Task 3 / 4 / 5 可并行
Task 6 依赖 2/3/4/5
Task 7 可与开发并行
Task 8 最后执行
```

---

# 32. 并发实施建议

遵循当前项目工作方式：

```text
最多 6 路并发
读 / 审计 / 测试尽量并行
权威写入 single-writer
```

建议分槽：

```text
Slot 1
Schema / Contract 主写

Slot 2
Reference 审计与测试

Slot 3
Caption 审计与 Fixtures

Slot 4
Transition 审计与 Fixtures

Slot 5
Reviewer / Evidence 测试

Slot 6
回归 / 文档 / 风险审计
```

涉及同一核心 Schema 的写操作保持 single-writer。

---

# 33. 完成定义

本次迭代完成不是：

```text
代码写完
```

而是：

```text
Schema 完成
+
旧数据兼容
+
生产链消费
+
Reviewer 消费
+
正反例测试
+
Shadow 验证
+
无现有跑批回归
```

最终状态：

```text
StoryOS 不仅知道：
“这一帧要生成什么”

还知道：
“这一帧为什么存在”
“观众应该看到什么”
“什么不能提前看到”
“字幕承担什么作用”
“它和上一帧为什么能连起来”
“图片实际上有没有完成叙事任务”
```

---

# 34. 最终结论

本方案不是新的平台重构。

它是一轮：

> **StoryOS 内容语义增强。**

最终只强化三层：

```text
Story Canon
        ↓
Frame Production Contract
        ↓
Narrative QA
```

先把：

```text
Hard Truth
权威事实
```

建准确，

再进入后续：

```text
Memory
Experience
Retrieval
Rerank
RAG
Agent 智能决策
```

避免 StoryOS 在事实尚未结构化之前过早依赖模糊召回。

---

# 35. 推荐实施顺序

```text
P0-1 Story Fact
        ↓
P0-2 Frame Narrative / Evidence
        ↓
P0-3 Reference Semantics
        ↓
P0-4 Caption Semantics
        ↓
P0-5 Transition Edge
        ↓
Narrative Fixture
        ↓
Shadow Review
        ↓
P1 Transition / Sequence QA
        ↓
P1 Repair Router
        ↓
P2 Retrieval / RAG
```

**原则：先建立事实，再建立验收；先建立验收，再增加智能。**
