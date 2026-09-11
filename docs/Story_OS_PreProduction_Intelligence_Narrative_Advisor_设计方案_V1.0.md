# Story OS PreProduction Intelligence Narrative Advisor 设计方案 V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、定位

Narrative Advisor 是 Pre Production Advisor 的创作建议层。

目标：

将 Similarity Analysis 发现的风险，转换为可执行的创作建议。

不是：

- 自动改写故事
- 替代作者决策
- 判断故事一定成功
- 阻断生产

输出：

```
PASS
WARNING
NEEDS_REVISION
```

---

# 二、整体流程

```
Story Lock

↓

Story DNA

↓

Similarity Analysis

↓

Risk Report

↓

Narrative Advisor

↓

Creative Recommendation

↓

Creator Decision
```

---

# 三、核心能力

## 1. Hook Advisor

分析：

- 第一帧冲突
- 开场信息密度
- 用户停留可能性

输出示例：

```yaml
hook_risk: MEDIUM

recommendation:
  - strengthen_first_frame_conflict
  - introduce_character_goal_earlier
```

---

## 2. Anomaly Mechanism Advisor

分析：

- 异常是否独特
- 是否与历史 Episode 重复
- 升级路径是否成立

输出示例：

```yaml
anomaly_risk: HIGH

reason:
  - similar_anomaly_pattern_found

recommendation:
  - redesign_anomaly_mechanism
```

---

## 3. Ending Advisor

分析：

- 结尾是否解释过度
- 是否缺少余韵
- 是否符合账号风格

输出：

```yaml
ending_risk: LOW
```

---

# 四、Advisor 输出模型

```yaml
advisor_result:

decision: WARNING

risks:
  - type: hook
    level: MEDIUM

recommendations:
  - improve_opening_scene

confidence: MEDIUM
```

---

# 五、与人工决策关系

Advisor 不做最终决定。

流程：

```
Advisor

↓

Creator Review

↓

Accept

or

Revise Story Lock

↓

Visual Lock
```

---

# 六、EP003 示例

如果接入 Narrative Advisor：

输入：

```
Similarity Risk
HIGH
```

输出：

```
WARNING
```

建议：

- 避免继续使用山地+雾异常组合
- 提升第一帧人物冲突
- 增加新的异常机制

不会直接禁止生产。

---

# 七、边界

Narrative Advisor 不负责：

- 自动生成最终剧情
- 替代 Story Lock
- 自动决定爆款概率
- 替代人工创作判断

---

# 八、未来演进

```
Narrative Advisor

↓

Experience Store

↓

Pattern Learning

↓

更强创作建议能力
```
