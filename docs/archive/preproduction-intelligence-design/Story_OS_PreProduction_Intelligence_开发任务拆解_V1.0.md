# Story OS PreProduction Intelligence 开发任务拆解 V1.0

更新时间：2026-09-11

状态：Design Only

---

# 一、开发目标

基于已冻结设计，实现 Pre Production Advisor MVP。

目标：

```
Story Lock

↓

Story DNA

↓

Similarity Analysis

↓

Advisor Report

↓

Memory
```

不影响现有 Production Runtime。

---

# 二、Task 拆解

## Task 1 Story DNA Engine

目标：

实现故事结构提取能力。

输入：

```
story-lock
```

输出：

```
story_fingerprint.yaml
```

验收：

- Schema 符合 V1.0
- 可重复生成
- 不包含评分字段

---

## Task 2 Similarity Analyzer

目标：

基于历史 Episode DNA 发现相似风险。

输入：

- Current Story DNA
- Historical Story DNA

输出：

- Similarity Evidence
- Risk Level

验收：

- 风险必须有 Evidence
- 支持 EP001/EP003 验证

---

## Task 3 Advisor Report Generator

目标：

将风险转换为创作建议。

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

## Task 4 Memory Adapter

目标：

连接 Experience Store。

能力：

- 查询历史经验
- 保存 Review Report 引用

边界：

不维护规则。

---

## Task 5 Test Suite

测试：

- DNA Schema Test
- Similarity Evidence Test
- Report Contract Test
- EP003 Regression Test

---

## Task 6 Shadow Mode Integration

目标：

先观察，不影响生产。

流程：

```
Story Lock

↓

Advisor

↓

Report Only

↓

Human Review
```

---

# 三、开发顺序

推荐：

```
Story DNA

↓

Similarity Analysis

↓

Advisor Report

↓

Memory Adapter

↓

Shadow Integration
```

---

# 四、禁止范围

MVP 阶段禁止：

- 修改 Story Lock
- 修改 Runtime 状态机
- 阻断 Production
- 自动重写剧情
- 自动生成分镜

---

# 五、完成标准

MVP 完成条件：

1. 能理解 Story Lock
2. 能生成 Story DNA
3. 能发现历史相似风险
4. 能输出解释型建议
5. 能沉淀经验
6. 不影响现有生产链
