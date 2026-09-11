# Story OS PreProduction Intelligence Final Architecture V1.0

更新时间：2026-09-11

状态：Design Freeze

---

# 一、最终定位

Pre Production Intelligence 是 Story OS 的创作智能辅助层。

不是：

- Production Gate
- 审核系统
- 自动决策系统
- 生产阻断系统

核心目标：

```
理解故事

↓

发现风险

↓

提供建议

↓

沉淀经验
```

---

# 二、最终架构

```
Story Idea

↓

Concept Ambition

↓

Story Lock

↓

Pre Production Advisor

  ├── Story DNA
  │
  ├── Similarity Analysis
  │
  ├── Narrative Advisor
  │
  ├── Production Hint
  │
  └── Review Report

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

---

# 三、核心模块冻结

## Story DNA

职责：

- 故事结构提取
- 历史比较基础
- Memory 检索基础

不负责评分。

---

## Similarity Analysis

职责：

- 历史 Episode 对比
- Evidence 生成
- 风险识别

输出：

LOW / MEDIUM / HIGH

---

## Narrative Advisor

职责：

风险转建议。

例如：

```
重复风险

↓

建议调整异常机制
```

---

## Production Hint

职责：

将建议传递给生产环节。

包括：

- Voice Hint
- Frame Hint
- Subtitle Intent Hint

---

## Review Report

职责：

保存：

- Advisor 结果
- Evidence
- Creator Decision
- Production Outcome

进入 Memory。

---

# 四、与现有 Story OS 关系

保持：

- episode-state 唯一状态源
- story-gates 继续负责门禁证据
- Runtime 继续负责生产执行

Pre Production Intelligence 不创建第二套状态体系。

---

# 五、MVP 第一阶段范围

实现：

1. Story DNA
2. Similarity Analysis
3. Advisor Report
4. Memory Adapter
5. Shadow Mode

暂不实现：

- 自动改剧情
- 自动生产
- 自动阻断
- 复杂规则系统

---

# 六、EP003 验证目标

系统应提前发现：

- 山地异常重复
- 与 EP001 空间表达接近
- 开头 Hook 风险

输出：

```
WARNING
```

并提供修改建议。

---

# 七、设计冻结结论

Pre Production Intelligence 可以进入 MVP 开发阶段。

实施原则：

```
Advisor 提醒

Creator 决策

Runtime 执行

Memory 学习
```
