# Story OS PreProduction Intelligence 实施路线设计 V1.0

更新时间：2026-09-11

版本：V1.0

状态：Design Only（方案设计，不进入代码实施）

---

# 一、目标定位

PreProduction Intelligence 不作为生产 Gate。

定位：

```
Pre Production Advisor
```

作用：

- 提前发现故事风险
- 提供创作建议
- 利用历史经验辅助决策
- 帮助提升下一次生产质量

不负责：

- 阻断 Production Runtime
- 判断故事一定爆
- 替代创作者决策
- 自动修改最终剧情

---

# 二、总体演进路线

```
Story Idea

↓

Concept Ambition

↓

Story Lock

↓

Pre Production Advisor

↓

Creator Decision

↓

Visual Lock

↓

Production Runtime

↓

Review

↓

Memory
```

Pre Production Advisor 位于 Story Lock 与 Visual Lock 之间。

---

# 三、Phase 0：Design Freeze

目标：冻结架构边界。

确认：

- Advisor 非阻断
- 不修改现有 Runtime
- 不修改 Episode 状态机
- 不新增 Gate
- 不建立第二套规则系统

输出：

设计冻结文档。

---

# 四、Phase 1：Story DNA MVP

目标：让系统理解故事结构。

输入：

```
story-lock
```

输出：

```
story_fingerprint.yaml
```

初始 Schema：

```yaml
setting:
relationship:
character:
anomaly_type:
emotion:
ending_style:
visual_pattern:
```

能力：

- 故事结构抽取
- 历史 Episode 索引
- Pattern Learning 基础数据

暂不包含：

- 自动评分
- 自动改稿
- 风险阻断

---

# 五、Phase 2：Similarity Analysis

目标：建立历史内容比较能力。

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

输出示例：

```yaml
similarity_risk: HIGH

related_episode:
  - EP001

matched_features:
  - mountain_setting
  - fog_anomaly
  - isolated_environment
```

核心原则：

风险必须绑定 Evidence。

---

# 六、Phase 3：Narrative Advisor

目标：提供叙事建议。

输出：

- Hook 建议
- 异常机制建议
- 节奏建议
- 结尾风险建议

示例：

```yaml
decision: WARNING

risk:
  hook_strength: LOW

recommendation:
  strengthen_first_frame
```

注意：

WARNING 不代表失败。

---

# 七、Phase 4：Production Hint

目标：辅助视觉生产前准备。

包含：

## Voice Card Hint

辅助：

- 人物行为一致性
- 情绪表达
- 角色关系

## Frame Constraint Hint

辅助：

- 场景约束
- 视觉重点
- 禁止遮挡区域

不替代：

- Visual Lock
- Frame Contract

---

# 八、Phase 5：Subtitle Intent Planning

目标：字幕前置设计。

原则：

不是图片生成后补字幕。

流程：

```
Story Intent

↓

Frame Intent

↓

Subtitle Intent

↓

Production
```

保证：

- 字幕服务剧情
- 图片与文字一致
- 避免后期硬贴

---

# 九、Phase 6：Memory Integration

目标：形成经验闭环。

流程：

```
Episode Production

↓

Review

↓

Story DNA

↓

Experience Store

↓

Future Advisor
```

Memory 负责：

- 保存经验
- 提供检索
- 支撑 Pattern Learning

Advisor 负责：

- 使用经验
- 输出建议

---

# 十、MVP 实施优先级

推荐顺序：

```
1. Story DNA Schema

2. Evidence Model

3. Similarity Analysis

4. Risk Report

5. Narrative Advisor

6. Production Hint
```

原因：

先建立理解能力，再建立建议能力。

---

# 十一、EP003 验证案例

用于验证 Advisor 是否有效。

输入：

EP003 Story Lock

分析：

发现：

- 山地异常元素重复
- 与 EP001 空间表达相似
- 首帧冲突不足

输出：

```yaml
advisor_result:
  decision: WARNING
```

建议：

- 调整异常机制
- 强化开头 Hook
- 避免重复视觉 Pattern

系统不阻止生产。

---

# 十二、与现有生产链关系

当前生产链保持：

```
Story Lock

↓

Visual Lock

↓

Production Runtime
```

未来增加：

```
Story Lock

↓

Pre Production Advisor

↓

Creator Decision

↓

Visual Lock
```

属于增强层，不属于替换层。

---

# 十三、实施原则

1. 小步演进。
2. 不提前设计复杂规则。
3. 不追求绝对评分。
4. 所有风险必须有 Evidence。
5. 所有建议保留人工决策权。
6. 优先沉淀经验，而不是堆规则。

最终目标：

```
规则系统

↓

经验驱动系统

↓

创作智能辅助系统
```
