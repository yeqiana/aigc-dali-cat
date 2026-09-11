# Story OS PreProduction Intelligence Repository Structure V1.0

更新时间：2026-09-11

状态：Design Only（方案设计，不进入代码实施）

---

# 一、设计目标

定义 Pre Production Intelligence MVP 的代码组织边界。

原则：

- 不新增独立系统
- 不侵入 Production Runtime
- 不复制 Story Lock 状态
- 不建立第二套规则引擎

---

# 二、推荐目录结构

```text
pre_production/

├── story_dna/
│   ├── extractor
│   ├── schema
│   └── validator
│
├── similarity_analysis/
│   ├── analyzer
│   ├── evidence
│   └── retrieval
│
├── advisor/
│   ├── risk_assessor
│   ├── recommendation
│   └── report_generator
│
├── memory_adapter/
│
├── contracts/
│
└── tests/
```

---

# 三、模块职责

## story_dna

负责：

- Story Lock 解析
- Story Fingerprint 生成
- Schema 校验

不负责：

- 风险判断
- 生产决策

---

## similarity_analysis

负责：

- 历史 Episode 检索
- DNA 比较
- Evidence 生成

输出：

Similarity Evidence

---

## advisor

负责：

- 风险汇总
- 建议生成
- Report 输出

输出：

PASS / WARNING / NEEDS_REVISION

---

## memory_adapter

负责连接：

Experience Store

不负责：

- 保存规则
- 修改经验数据

---

# 四、与现有 Story OS 关系

```text
Story Lock

↓

pre_production

↓

Visual Lock

↓

Production Runtime
```

Pre Production Intelligence 是中间辅助层。

---

# 五、禁止事项

禁止：

- 创建新的 Episode 状态机
- 替代 story-gates
- 修改 Runtime 流程
- 自动阻断生产
- 在模块内维护隐式规则

---

# 六、MVP 实施顺序

1. story_dna
2. similarity_analysis
3. advisor
4. memory_adapter
5. shadow integration

