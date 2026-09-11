# Story OS Pre Production Intelligence MVP技术设计 V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、设计目标

Pre Production Intelligence MVP 目标：

在 Story Lock 与 Visual Lock 之间提供智能辅助能力。

核心链路：

```
Story Lock

↓

Story DNA Extraction

↓

Similarity Analysis

↓

Advisor Report

↓

Creator Decision

↓

Visual Lock
```

不改变现有生产状态机。

---

# 二、模块边界

MVP 包含：

```
pre_production/

├── story_dna/
│
├── similarity_analysis/
│
├── advisor/
│
└── report/
```

不包含：

- 自动生产
- 自动改剧情
- 自动审核
- Production Gate

---

# 三、数据模型设计

## Story DNA

输入：

```
story-lock
```

输出：

```
story_fingerprint.yaml
```

作为历史比较基础。

---

## Similarity Evidence

结构：

```
current_episode

↓

matched_episode

↓

matched_features

↓

risk_level
```

要求：所有风险必须具备证据。

---

## Advisor Report

输出：

```
PASS
WARNING
NEEDS_REVISION
```

包含：

- risks
- evidence
- recommendations
- confidence

---

# 四、与现有架构关系

保持：

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

不创建第二状态机。

---

# 五、Memory 接口边界

Pre Production Intelligence 不管理 Memory。

只消费：

```
Historical Experience
```

并输出：

```
Review Report
```

供 Memory 沉淀。

---

# 六、第一阶段验收标准

1. 可以从 Story Lock 生成 Story DNA。
2. 可以检索历史 Episode。
3. 可以生成 Similarity Evidence。
4. 可以输出 Advisor Report。
5. 不影响现有 Production Runtime。

---

# 七、实施原则

先数据，再算法。

先闭环，再自动化。

先辅助创作，再考虑智能增强。
