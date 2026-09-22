# Story OS PreProduction Intelligence Review Report 设计方案 V1.0

更新时间：2026-09-11

版本：V1.0

状态：Design Only（方案设计，不进入代码实施）

---

# 一、定位

Review Report 是 Pre Production Intelligence 的结果沉淀层。

目标：

- 保存一次 Advisor 分析结果
- 记录风险证据
- 记录创作者决策
- 为 Memory / Experience Store 提供输入

不是：

- 第二套审核系统
- Production Gate
- 自动评分系统

---

# 二、整体流程

```
Episode

↓

Pre Production Advisor

↓

Review Report

↓

Production Result

↓

Experience Store

↓

Future Episode Advisor
```

---

# 三、Report 核心结构

示例：

```yaml
review_id:
episode_id:

advisor_decision:
  PASS
  WARNING
  NEEDS_REVISION

risks:
  - type:
    level:
    evidence:

recommendations:

creator_decision:

final_result:
```

---

# 四、Evidence 沉淀

每个风险必须绑定证据。

例如：

```yaml
risk:
  type: similarity
  level: HIGH

related_episode:
  - EP001

matched_features:
  - mountain_environment
  - fog_anomaly
  - isolated_location
```

避免黑盒判断。

---

# 五、Creator Decision

Advisor 不拥有最终决策权。

流程：

```
Advisor Result

↓

Creator Review

↓

Accept

or

Revise Story Lock
```

记录：

- 接受建议
- 忽略建议
- 修改方向

---

# 六、Memory Integration

Review Report 是 Experience Store 输入。

流程：

```
Review Report

↓

Production Outcome

↓

Audience Feedback

↓

Experience Memory
```

用于未来：

- Similarity Analysis
- Pattern Learning
- Narrative Advisor 优化

---

# 七、EP003 示例

Advisor 输出：

```
WARNING
```

原因：

- 山地异常表达重复
- 与 EP001 空间模式接近
- 开头 Hook 风险较高

Creator Decision：

可能：

A. 接受风险继续生产

B. 修改异常机制

C. 调整开头设计

最终结果进入 Memory。

---

# 八、设计原则

Pre Production Intelligence 闭环：

```
理解故事

↓

发现风险

↓

提供建议

↓

辅助生产

↓

记录结果

↓

提升下一次生产
```
