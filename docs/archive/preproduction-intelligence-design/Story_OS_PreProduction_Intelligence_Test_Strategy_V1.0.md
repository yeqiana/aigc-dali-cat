# Story OS PreProduction Intelligence Test Strategy V1.0

更新时间：2026-09-11

状态：Design Only

---

# 一、测试目标

验证 Pre Production Intelligence 能够：

- 正确理解 Story Lock
- 生成稳定 Story DNA
- 发现历史相似风险
- 输出可解释 Advisor Report
- 不影响 Production Runtime

不测试：

- 是否爆款
- 自动创作能力
- 自动阻断生产

---

# 二、测试分层

## 1. Unit Test

验证单模块能力。

包含：

- Story DNA Extraction
- Schema Validation
- Similarity Calculation
- Evidence Builder
- Report Generator

---

## 2. Contract Test

验证数据契约。

检查：

- Story DNA Schema
- Advisor Report Schema
- Evidence Model

要求：

上下游字段稳定。

---

## 3. Integration Test

验证完整链路：

```
Story Lock

↓

Story DNA

↓

Similarity Analysis

↓

Advisor Report
```

---

# 三、Episode 回归测试

## EP001

作为历史基准样本。

验证：

- DNA 提取
- Pattern 保存
- Memory 检索

---

## EP002

验证：

- 系列风格识别
- Visual Pattern 提取

---

## EP003

作为风险案例。

预期：

输出：

```
WARNING
```

原因：

- 山地异常重复
- 空间表达接近 EP001
- Hook 强度不足

---

# 四、Shadow Mode 验证

流程：

```
Advisor

↓

Report Only

↓

人工评审
```

要求：

- 不修改生产流程
- 不改变状态
- 不影响发布

---

# 五、MVP 发布检查

必须满足：

1. Story DNA 可稳定生成
2. Similarity Evidence 可解释
3. Advisor Report 可消费
4. Memory 可接收结果
5. Runtime 无侵入

---

# 六、测试原则

Pre Production Intelligence 是辅助系统。

测试重点：

```
可靠

可解释

可回溯

可学习
```

而不是：

```
绝对正确
```
