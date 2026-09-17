# Story OS PreProduction Intelligence API Contract V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、设计目标

定义 Pre Production Advisor 与 Story OS 现有体系之间的数据交换契约。

目标：

- Story Lock 可以调用 Advisor
- Advisor 输出可以被 Runtime / Console 使用
- Review Report 可以进入 Memory
- 不新增状态机

---

# 二、整体调用关系

```
Story Lock

↓

Pre Production Advisor

↓

Advisor Report

↓

Creator Decision

↓

Memory Integration
```

---

# 三、Advisor 输入契约

输入来源：

```
story-lock
```

示例：

```yaml
story_id:
title:
summary:
characters:
setting:
anomaly:
ending_style:
visual_direction:
```

说明：

输入只描述故事，不包含生产结果。

---

# 四、Story DNA 输出契约

输出：

```
story_fingerprint.yaml
```

包含：

```yaml
story_id:
setting:
relationship:
character:
anomaly:
emotion:
narrative:
visual_pattern:
```

---

# 五、Advisor Report 输出契约

统一输出：

```
PASS
WARNING
NEEDS_REVISION
```

示例：

```yaml
decision: WARNING

risks:
  - type: similarity
    level: HIGH

recommendations:
  - redesign_anomaly_mechanism

confidence: MEDIUM
```

---

# 六、Evidence Contract

风险必须绑定证据。

示例：

```yaml
risk:
  type: similarity
  level: HIGH

evidence:
  related_episode:
    - EP001

  matched_features:
    - mountain_environment
    - fog_anomaly
```

禁止：

- 无依据评分
- 黑盒判断

---

# 七、Memory 写入契约

Advisor 不直接管理 Memory。

流程：

```
Advisor Report

↓

Review Report

↓

Memory Service
```

写入内容：

- Story DNA
- Production Decision
- Final Outcome
- Learning Experience

---

# 八、非目标

当前 API 不负责：

- 修改 Story Lock
- 自动生成剧情
- 自动触发 Production Runtime
- 替代人工审核

---

# 九、设计原则

Pre Production Advisor 是辅助能力层。

不是：

```
Gate
Rule Engine
Decision Maker
```

而是：

```
Understand

Analyze

Recommend

Learn
```
