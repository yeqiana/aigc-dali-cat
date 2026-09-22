# Story OS PreProduction Intelligence Similarity Analysis 设计方案 V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、定位

Similarity Analysis 是 Pre Production Advisor 的风险分析能力。

目标：

- 发现当前 Story 与历史 Episode 的结构相似风险
- 提供相似证据
- 辅助创作者修改决策

不是：

- 自动判定抄袭
- 自动阻断生产
- 替代创作者判断

---

# 二、整体流程

```
Current Story

↓

Story DNA Extraction

↓

Historical Story DNA Retrieval

↓

Similarity Analysis

↓

Evidence Collection

↓

Risk Report
```

---

# 三、输入输出

## 输入

当前：

```
story_fingerprint.yaml
```

历史：

```
Episode Story DNA Library
```

---

## 输出

示例：

```yaml
similarity_risk: HIGH

related_episode:
  - EP001

matched_dimensions:
  - setting
  - anomaly_mechanism

confidence: MEDIUM

recommendations:
  - redesign_anomaly
```

---

# 四、分析维度

## 1. Setting Similarity

比较：

- 地理环境
- 空间类型
- 时间背景

例如：

山村、废弃建筑、夜晚道路。

---

## 2. Relationship Similarity

比较：

- 人物关系
- 角色身份
- 冲突来源

---

## 3. Anomaly Mechanism Similarity

最高优先级。

比较：

- 异常来源
- 异常规则
- 异常升级方式

避免只看表面元素。

---

## 4. Visual Pattern Similarity

比较：

- 摄影方式
- 视觉母题
- 重复视觉元素

---

# 五、Evidence Model

所有风险必须绑定证据。

结构：

```
Risk
 ↓
Evidence
 ↓
Recommendation
```

示例：

```yaml
evidence:
  - episode: EP001
    matched:
      - mountain_environment
      - fog_anomaly
      - isolated_location
```

---

# 六、风险等级

不使用绝对评分。

使用：

```
LOW
MEDIUM
HIGH
```

含义：

LOW：存在少量相似元素。

MEDIUM：部分结构接近，需要关注。

HIGH：核心机制高度接近，需要重新设计。

---

# 七、与 Memory Integration

流程：

```
Experience Store

↓

Historical DNA Retrieval

↓

Similarity Analysis

↓

Advisor Report
```

Memory 提供经验。

Similarity Analysis 负责分析。

---

# 八、EP003案例

输入：

EP003 Story DNA。

发现：

```
setting:
 mountain

visual:
 fog

anomaly:
 environmental mystery
```

与 EP001 存在：

- 空间表达相似
- 异常氛围相似

输出：

```
WARNING
```

建议：

- 调整异常机制
- 增强第一帧冲突
- 避免重复空间表达

---

# 九、设计原则

1. 证据优先，而不是规则优先。
2. 风险提示，而不是自动否决。
3. 学习历史经验，而不是堆积规则。
4. 服务创作，而不是限制创作。
