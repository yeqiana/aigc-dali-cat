# Story OS PreProduction Intelligence Runtime Integration 设计方案 V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、定位

Pre Production Intelligence 不作为新的 Runtime 系统。

它作为 Story OS 现有生产链中的智能辅助层。

核心原则：

- 不新增状态机
- 不替代 Story Lock
- 不阻断 Production Runtime
- 不改变现有 Episode 生命周期

---

# 二、整体接入流程

```text
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

---

# 三、与 Story Lock 集成

Story Lock 是唯一故事冻结入口。

Advisor 读取：

- story summary
- character contract
- setting
- anomaly design
- ending direction

生成：

```text
Story DNA

+

Advisor Report
```

不修改 Story Lock 原始内容。

---

# 四、与 Workflow 集成

Pre Production Advisor 作为 Workflow 中的辅助节点。

不是新的 Workflow。

流程：

```text
Workflow

↓

Advisor Task

↓

Report Artifact

↓

Continue Production
```

---

# 五、与 Memory Service 集成

读取：

```text
Historical Experience
```

输出：

```text
Advisor Result
```

生产完成后：

```text
Review Report

↓

Memory Update
```

形成学习闭环。

---

# 六、与 Production Runtime 边界

Advisor 提供：

- Risk
- Evidence
- Recommendation
- Hint

Runtime 负责：

- Image Generation
- Frame Execution
- Review
- Release

二者通过 Artifact 交互。

---

# 七、禁止事项

禁止：

- Advisor 修改 Runtime 状态
- Advisor 直接触发生产失败
- Advisor 创建第二状态机
- Advisor 替代人工创作决策

---

# 八、MVP 接入目标

第一阶段只实现：

```text
Story Lock

↓

Advisor

↓

Report

↓

Creator Decision
```

不接入复杂自动化。
