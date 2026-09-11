# Story OS PreProduction Intelligence 实施方案 V1.1

更新时间：2026-09-11

版本：V1.1

状态：Design Only（方案设计，不进入代码实施）

---

# 一、定位调整

## 原定位

Production Gate

## 新定位

Production Advisor

Pre Production Intelligence 不作为生产阻断系统，而作为生产前智能辅助系统。

第一阶段目标：

- 提前发现故事风险
- 提前发现同质化风险
- 提供创作建议
- 辅助人工决策

不直接阻止 Production Runtime。

输出结果：

```
PASS

WARNING

NEEDS_REVISION
```

说明：

避免评分模型误判导致正常生产被阻塞。

---

# 二、整体架构调整

## 原设计

```
pre_production/

story_evaluator
similarity_detector
storyboard_validator
subtitle_planner
voice_card_engine
frame_constraint_builder
production_gate
```

## V1.1 调整后

```
pre_production/

├── story_dna/
│
├── similarity_analysis/
│
├── narrative_advisor/
│
├── production_hint/
│
└── review_report/
```

设计原则：

- 第一阶段减少模块数量
- 避免规则系统快速膨胀
- 先形成 Advisor 能力，再逐步演化

---

# 三、Story DNA Extraction

新增核心能力：

## Story DNA Extraction

输入：

```
story-lock
```

输出：

```
story_fingerprint.yaml
```

示例：

```yaml
setting:
relationship:
anomaly_type:
emotion:
ending_style:
visual_pattern:
```

用途：

1. 同质化检测
2. Pattern Learning
3. 历史 Episode 比较
4. Experience Store 检索

Story DNA 不负责判断好坏，只负责结构化故事特征。

---

# 四、Risk Assessment 模型

取消绝对评分模型。

不输出：

```
87分
92分
```

避免伪精确。

改为风险评估：

示例：

```yaml
similarity_risk: HIGH
hook_strength: MEDIUM
series_fit: LOW
```

维度：

|字段|含义|
|-|-|
|similarity_risk|与历史内容重复风险|
|hook_strength|开头吸引力风险|
|series_fit|账号系列匹配风险|

最终输出建议，而不是评分结论。

---

# 五、Memory / Experience Store Integration

新增历史经验连接。

流程：

```
历史 Episode

↓

Story DNA

↓

Similarity Analysis

↓

Risk Report
```

说明：

系统不是通过大量固定规则判断。

而是基于历史生产经验辅助判断。

---

# 六、阶段规划

## Phase 1

Story DNA
+
Similarity Analysis

目标：

建立故事结构理解和历史比较能力。

---

## Phase 2

Narrative Advisor

目标：

输出：

- 开头优化建议
- 异常机制建议
- 结尾风险建议

---

## Phase 3

Voice Card Hint
+
Frame Constraint Hint

目标：

辅助：

- 人物行为一致性
- 视觉约束
- 角色表达

---

## Phase 4

Subtitle Intent Planning

目标：

提前规划字幕意图，而不是生成图片后补字幕。

---

## Phase 5

Production Automation

进入正式生产链。

---

# 七、与现有 Story OS 架构关系

不新增独立系统。

挂载位置：

```
Story Lock

↓

Pre Production Advisor

↓

Visual Lock

↓

Production Runtime

↓

Review

↓

Memory
```

Pre Production Advisor 是 Story Lock 与 Production Runtime 之间的智能辅助层。

---

# 八、EP003 案例复盘

## 失败案例

EP003。

提前分析应该发现：

- 山地异常元素重复
- 与 EP001 空间异常存在相似倾向
- 开头 Hook 强度不足

系统输出：

```
WARNING
```

建议：

- 重新设计异常机制
- 提升首帧冲突
- 避免重复空间表达

系统不直接禁止生产。

最终决定仍由创作者确认。

---

# 九、Advisor Output Contract

Pre Production Advisor 输出需要具备机器可消费结构。

示例：

```yaml
advisor_result:
  decision: WARNING

  risks:
    - type: similarity
      level: HIGH
      evidence:
        - EP001
        - EP002

  recommendations:
    - redesign_anomaly
    - strengthen_hook

  confidence: MEDIUM
```

设计原则：

- 输出风险、证据、建议三部分
- 不输出绝对结论
- 不授予生产 PASS 权限

供后续 Runtime、Console、Memory 使用。

---

# 十、Evidence Model

所有 Risk Assessment 必须关联 Evidence。

流程：

```
Risk

↓

Evidence

↓

Recommendation
```

例如：

```
similarity_risk: HIGH

Evidence:

EP001:
- mountain environment
- fog anomaly
- isolated village

EP003:
- mountain environment
- fog anomaly
- isolated village
```

避免黑盒判断。

---

# 十一、Memory 边界设计

Memory / Experience Store：

负责：

- 保存历史 Episode 经验
- 提供历史检索
- 沉淀 Pattern

Pre Production Advisor：

负责：

- 消费 Memory 信息
- 生成风险分析
- 输出创作建议

关系：

```
Memory

↓ retrieve

Pre Production Advisor

↓

Recommendation
```

Advisor 不自己维护规则库。

---

# 十二、人工决策流程

Pre Production Advisor 不替代创作者决策。

流程：

```
Advisor Result

↓

Creator Decision

↓

继续 Story Lock / 修改 Story Lock
```

WARNING 情况：

- 可以接受继续生产
- 可以修改故事
- 可以重新生成候选

---

# 十三、与 Concept Ambition 关系

两者职责不同。

```
Story Idea

↓

Concept Ambition

(判断是否值得做)

↓

Story Lock

↓

Pre Production Advisor

(判断是否存在生产风险)

↓

Visual Lock
```

Concept Ambition 关注价值。

Pre Production Advisor 关注风险。

---

# 十四、非目标范围

Pre Production Advisor 不负责：

- 判断故事一定爆
- 自动替代作者创作
- 自动生成最终剧情
- 阻断 Production Runtime
- 替代人工审核

定位始终是创作辅助智能层。

---

# 十五、最终目标

Pre Production Advisor 不是审核系统。

它是 Story OS 的创作智能层：

```
发现风险

↓

提供建议

↓

辅助决策

↓

沉淀经验

↓

提升下一次生产质量
```

