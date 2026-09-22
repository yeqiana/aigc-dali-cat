# Story OS PreProduction Intelligence Story DNA Schema V1.0

更新时间：2026-09-11

版本：V1.0

状态：Design Only（方案设计，不进入代码实施）

---

# 一、目标

Story DNA 是 Pre Production Advisor 的基础结构化能力。

目标：

- 将 Story Lock 转换为可比较的故事指纹
- 支撑历史 Episode 相似性分析
- 支撑 Memory / Experience Store 检索
- 支撑 Pattern Learning

Story DNA 不负责判断故事好坏。

它只回答：

> 这个故事是什么？它具有什么结构特征？

---

# 二、数据流

```
Story Lock

↓

Story DNA Extraction

↓

story_fingerprint.yaml

↓

Similarity Analysis

↓

Risk Report
```

---

# 三、Schema 设计

```yaml
story_id:

setting:
  location:
  environment:
  time_period:
  social_context:

relationship:
  protagonist:
  companion:
  relationship_type:

character:
  protagonist_profile:
  ordinary_level:
  motivation:

anomaly:
  anomaly_type:
  anomaly_mechanism:
  anomaly_visibility:
  escalation_pattern:

emotion:
  primary_emotion:
  secondary_emotion:
  audience_feeling:

narrative:
  hook_type:
  conflict_type:
  ending_style:

visual_pattern:
  camera_style:
  environment_pattern:
  recurring_visual_elements:

series_fit:
  account_style:
  audience_expectation:
```

---

# 四、字段说明

## setting

描述故事发生环境。

示例：

```yaml
location: 县城
environment: 山区村落
time_period: 现代夏季
```

用途：

检测空间重复。

---

## relationship

描述人物关系。

例如：

- 情侣
- 朋友
- 家人
- 陌生人

用途：

判断情感结构是否重复。

---

## anomaly

描述异常机制。

重点字段：

```
anomaly_type
anomaly_mechanism
escalation_pattern
```

用途：

比单纯地点相似更准确判断故事重复。

---

## visual_pattern

描述视觉表达。

例如：

- 第一人称手机拍摄
- 旧数码相机
- 监控视角
- 生活记录感

用途：

辅助视觉 Pattern Learning。

---

# 五、与 Memory 关系

Memory 保存：

```
Episode

Story DNA

Production Result

Audience Feedback
```

Advisor 查询：

```
Current Story DNA

↓

Historical DNA Retrieval

↓

Similarity Evidence

↓

Risk Recommendation
```

---

# 六、明确非目标

Story DNA 不负责：

- 判断爆款概率
- 自动修改剧情
- 自动生成故事
- 替代创作者决策
- 直接阻断生产

---

# 七、后续演进

Phase 1:

Schema Freeze

↓

Phase 2:

Story DNA Extraction

↓

Phase 3:

Similarity Analysis

↓

Phase 4:

Pattern Learning
