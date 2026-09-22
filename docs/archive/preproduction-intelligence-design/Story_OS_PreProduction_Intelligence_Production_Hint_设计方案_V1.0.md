# Story OS PreProduction Intelligence Production Hint 设计方案 V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、定位

Production Hint 是 Pre Production Advisor 面向 Production Runtime 的建议输出层。

目标：

- 将故事风险转化为生产提示
- 提前约束视觉、角色、字幕表达
- 降低生产阶段返工概率

不是：

- Production Gate
- 自动生成器
- 替代 Visual Lock
- 替代 Frame Contract

---

# 二、整体流程

```
Story Lock

↓

Story DNA

↓

Similarity Analysis

↓

Narrative Advisor

↓

Production Hint

↓

Visual Lock / Production Runtime
```

---

# 三、Hint 分类

## 1. Voice Card Hint

目标：

保持人物表达一致。

输入：

- Character Contract
- Story DNA
- Narrative Risk

输出：

```yaml
voice_hint:
  emotion:
  speaking_style:
  personality:
```

示例：

避免：

"专业调查员式表达"

建议：

"普通返乡青年视角"

---

## 2. Frame Constraint Hint

目标：

辅助视觉生产。

输出：

```yaml
frame_hint:
  avoid:
    - repeated_visual_pattern

  emphasize:
    - character_relationship
    - ordinary_life_context
```

注意：

Hint 不替代 Frame Contract。

---

## 3. Subtitle Intent Hint

目标：

让字幕服务叙事，而不是解释图片。

输出：

```yaml
subtitle_hint:
  intent:
  emotion:
  information_level:
```

---

# 四、与 Runtime 边界

Production Hint：

提供建议。

Production Runtime：

负责执行。

关系：

```
Advisor

↓ recommendation

Runtime

↓ execution

Review
```

---

# 五、EP003 示例

Advisor 发现：

```
similarity_risk: HIGH
```

Production Hint 输出：

```yaml
frame_hint:
  avoid:
    - mountain_fog_generic_scene

  emphasize:
    - character_relationship
    - unique_anomaly_mechanism
```

目的：

不是禁止 EP003。

而是在生产阶段降低重复表达。

---

# 六、设计原则

1. Hint 是建议，不是规则。
2. Hint 不创建第二套生产标准。
3. 最终生产权威仍然是：

```
Story Lock
Frame Contract
Visual Lock
Production Runtime
```

4. 所有 Hint 必须可追溯来源。

```
Risk
 ↓
Evidence
 ↓
Hint
```
