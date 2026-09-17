# Story OS PreProduction Intelligence MVP Acceptance Criteria V1.0

更新时间：2026-09-11

状态：Design Only（验收设计，不进入代码实施）

---

# 一、验收目标

确认 Pre Production Intelligence MVP 是否达到可进入开发阶段的条件。

MVP 不验证“是否能创造爆款”，只验证：

- 是否理解故事
- 是否发现历史风险
- 是否提供可解释建议
- 是否形成经验闭环

---

# 二、功能验收

## 1. Story DNA Extraction

输入：

```
Story Lock
```

输出：

```
story_fingerprint.yaml
```

验收：

- 能稳定提取故事结构
- 字段符合 Story DNA Schema
- 不包含评分结论

---

## 2. Similarity Analysis

验收：

能够完成：

```
Current DNA

↓

Historical DNA

↓

Similarity Evidence

↓

Risk Report
```

要求：

- 风险必须有 Evidence
- 不允许无依据判断

---

## 3. Advisor Report

输出：

```
PASS
WARNING
NEEDS_REVISION
```

必须包含：

- risk
- evidence
- recommendation
- confidence

---

# 三、数据验收

检查：

## Story DNA

- Schema 稳定
- 可被 Memory 检索

## Evidence

- 可追溯历史 Episode
- 可解释匹配原因

## Report

- 可供 Console 展示
- 可供 Memory 消费

---

# 四、EP 案例验收

## EP001

作为历史参考样本。

验证：

- DNA 正确生成
- Pattern 可检索

---

## EP003

作为风险案例。

系统应该发现：

- 山地异常相似
- 空间表达接近
- 开头 Hook 风险

输出：

```
WARNING
```

并提供：

- 修改异常机制建议
- 强化开头建议

---

# 五、Shadow Mode 验收

上线初期：

```
Advisor

↓

Report Only

↓

人工查看
```

不影响生产。

---

# 六、通过标准

满足：

1. 不阻塞现有 Production Runtime
2. 不修改 Story Lock 权威状态
3. 不新增第二状态机
4. 风险可解释
5. 建议可执行
6. 经验可沉淀

---

# 七、结论

达到以上标准后，可以进入 MVP 开发阶段。

Pre Production Intelligence 作为 Story OS 创作智能辅助层接入，而不是生产门禁系统。
