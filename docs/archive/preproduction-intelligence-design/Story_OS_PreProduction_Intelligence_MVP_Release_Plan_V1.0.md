# Story OS PreProduction Intelligence MVP Release Plan V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、发布目标

Pre Production Intelligence MVP 发布目标：

建立 Story OS 的生产前智能辅助能力。

不是：

- Production Gate
- 自动审核系统
- 生产阻断系统

目标：

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

# 二、发布阶段

## Phase 0 Design Freeze

冻结：

- Story DNA Schema
- Similarity Evidence Model
- Advisor Report Contract
- Runtime Integration Boundary

禁止：

- 新增规则引擎
- 修改 Runtime 状态机

---

## Phase 1 Shadow Mode

流程：

```
Story Lock

↓

Advisor

↓

Report Only

↓

人工查看
```

特点：

- 不影响生产
- 不修改状态
- 不参与决策

目标：

验证 Advisor 输出质量。

---

## Phase 2 Advisor Mode

正式接入：

```
Story Lock

↓

Pre Production Advisor

↓

Creator Decision

↓

Visual Lock
```

Advisor 输出作为创作参考。

---

# 三、发布检查项

## 数据检查

- Story DNA 可生成
- Schema 稳定
- Evidence 可追溯

## 流程检查

- 不影响 Production Runtime
- 不修改 Episode State
- 不产生第二状态机

## 质量检查

- EP001 回归通过
- EP002 风格识别通过
- EP003 风险识别通过

---

# 四、风险控制

禁止：

- WARNING 自动阻断
- AI 自动修改 Story Lock
- 用评分替代证据
- 用规则替代经验

---

# 五、成功标准

MVP 发布成功：

1. 能生成 Story DNA
2. 能发现历史相似风险
3. 能提供解释性建议
4. 能进入 Memory 学习闭环
5. 不破坏现有生产链

---

# 六、后续演进

MVP 后：

```
Experience Store

↓

Pattern Learning

↓

更强 Advisor 能力
```

但保持核心原则：

Pre Production Intelligence 是创作智能层，而不是生产控制层。
