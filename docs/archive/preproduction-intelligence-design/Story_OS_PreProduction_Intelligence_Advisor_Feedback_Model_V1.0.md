# Story OS PreProduction Intelligence Advisor Feedback Model V1.0

状态：Design Only

## 一、目标

记录 Advisor 建议与人工判断之间的差异，为 Memory 提供经验数据。

## 二、Feedback Schema

```yaml
feedback_id:
episode_id:
advisor_decision:
risks:
creator_decision:
recommendation_adopted:
final_assessment:
notes:
```

## 三、字段说明

advisor_decision:

- PASS
- WARNING
- NEEDS_REVISION

creator_decision:

- accepted
- revised
- ignored

final_assessment:

- useful
- inaccurate
- partial

## 四、边界

Feedback 不修改 Advisor 规则。

只作为后续 Experience Store 输入。
