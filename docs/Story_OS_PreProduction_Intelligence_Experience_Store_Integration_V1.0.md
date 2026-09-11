# Story OS PreProduction Intelligence Experience Store Integration V1.0

更新时间：2026-09-11

状态：Design Only（设计与接口准备，不进入自动学习，不接入 Runtime）

---

# 一、Experience Store 定位

Experience Store 是 Pre Production Intelligence 的**经验存储层**。

它把已经发生过的事实（Advisor 说了什么、创作者怎么决定、生产结果如何）**原样保存**，
供未来检索使用。它本身不思考。

## 1.1 不负责

- **不判断故事**：不做风险判定，不产出 PASS / WARNING / NEEDS_REVISION。
- **不修改规则**：不改 Advisor 规则、不改 Lexicon、不改 Similarity 权重。
- **不自动学习**：不做模式挖掘、不做参数更新、不做模型训练。
- **不阻断生产**：不写 `meta/episode-state.json`，不写 `meta/story-gates.json`，不参与门禁。
- **不引入评分**：不保存相似度百分比，不保存 87/92 这类伪精确分数，不保存阈值。

## 1.2 负责

- **保存历史经验**：把 Observation Ledger 与 Advisor Feedback 的内容落成可长期存放的经验记录。
- **提供检索上下文**：按 Episode / Story DNA / risk_type 返回历史案例，作为 Advisor 的输入。
- **支撑 Advisor**：为 Advisor 提供「以前发生过什么」，而不是「这次应该判定什么」。

## 1.3 三角色关系

```
Feedback   = 经验来源（人写的判断）
    |
    v
Experience Store = 经验存储（只存，不判）
    |
    v
Advisor    = 经验消费者（读了经验后，自己判断）
```

一句话：Experience Store 提供经验，Advisor 消费经验；两者之间只有数据流，没有控制流。

---

# 二、数据模型设计

三种实体：Episode Experience（一次完整经验）、Risk Pattern（可复现的风险形态）、
Creator Decision（人对 Advisor 的裁决记录）。

契约文件（唯一来源）：

```
pre_production/contracts/experience_record.schema.json
pre_production/contracts/risk_pattern.schema.json
pre_production/contracts/creator_decision_experience.schema.json
```

## 2.1 Episode Experience

一次 Episode 的完整经验切片，全部字段都是**引用或事实**，没有判断。

```yaml
schema: experience_record
schema_version: 1
experience_id: EXP-10-03-<8 位锚点摘要>
record_kind: episode_experience
episode_id: 10-03
story_dna_reference: story_dna:10-03@<story_lock sha8>
advisor_report_reference: advisor_report:PPA-10-03-<sha8>
observation_reference: OBS-10-03-<sha8>
feedback_reference: PFB-PPA-10-03-<sha8>
production_outcome: <自由文本；未生产时为 null>
audience_feedback: <平台原始数据映射；无数据时为 null>
created_time: <ISO8601>
advisory_only: true
blocks_production: false
authority: derived_non_authority
```

字段来源：

| Experience 字段 | 来源产物 | 说明 |
| --- | --- | --- |
| `story_dna_reference` | Story DNA / story_fingerprint | 只存引用，不复制 DNA 正文 |
| `advisor_report_reference` | Advisor Report | 只存引用 |
| `observation_reference` | Episode Observation Ledger | `observation_id` |
| `feedback_reference` | Advisor Feedback | `feedback_id` |
| `production_outcome` | 创作者 / 生产复盘 | 结果性描述，自由文本 |
| `audience_feedback` | Phase 9.6.1 Episode Data Collection | 平台原始数据，原样存放 |

`audience_feedback` 只做**搬运与存放**：本层不计算完播率、不计算转化、不生成任何评分字段。
具体平台字段（`view_count` / `like_count` / `completion_rate` 等）由 Phase 9.6.1 定义并拥有。

## 2.2 Risk Pattern Entity

保存「什么样的结构反复出现」，用于未来检索同类历史案例。它不是规则，不触发任何动作。

```yaml
schema: risk_pattern
schema_version: 1
pattern_id: PAT-similarity-<8 位摘要>
risk_type: similarity          # similarity | hook
pattern_description: "mountain_environment + fog_anomaly + isolated_location"
related_episode: ["10-01", "10-02"]
evidence: ["SIM-...", "SIM-..."]   # 指回 Similarity Evidence
risk_level: HIGH               # LOW | MEDIUM | HIGH，沿用既有风险等级
created_time: <ISO8601>
advisory_only: true
blocks_production: false
authority: derived_non_authority
```

要求：

- `pattern_description` 用 **token 组合**描述形态，例如 `mountain + fog + isolated location`；
- `evidence` 至少一条，且能指回真实 Similarity Evidence；
- 不保存相似度数值、不保存阈值、不保存「命中即拦截」之类的判定语义。

## 2.3 Creator Decision Entity

保存「人对 Advisor 的裁决」，用于未来回答「这类建议历史上被采纳吗、有没有用」。

```yaml
schema: creator_decision_experience
schema_version: 1
decision_experience_id: CDE-10-03-<8 位摘要>
episode_id: 10-03
feedback_reference: PFB-PPA-10-03-<sha8>
advisor_decision: WARNING                # PASS | WARNING | NEEDS_REVISION
creator_action: REVISE                   # ACCEPT | REVISE | IGNORE
recommendation_result: USEFUL            # USEFUL | PARTIAL | NOT_USEFUL
final_assessment: "按建议重做异常机制后，与历史篇目差异明显"
created_time: <ISO8601>
advisory_only: true
blocks_production: false
authority: derived_non_authority
```

枚举归属说明：

- `creator_action` 对应 Advisor Feedback 里的 `creator_decision`（`ACCEPT / REVISE / IGNORE`），只换字段名不改语义；
- `recommendation_result` 对应 Advisor Feedback 里的 `recommendation_result`（`USEFUL / PARTIAL / NOT_USEFUL`）；
- 既有设计文档《Advisor Feedback Model V1.0》里的 `final_assessment: useful|inaccurate|partial` 词表
  已由实现中的 `recommendation_result` 承载，因此本层不再复制第二套三值枚举；
  `final_assessment` 保持**自由文本**，用于写最终效果，避免制造第二套评分口径。

---

# 三、Read Path

未来读取流程（本阶段**只定义接口**，不实现智能检索算法）：

```
New Story
    |
    v
Story DNA
    |
    v
Experience Retrieval        <- ExperienceStoreRepository.get_related_experience()
    |                          <- ExperienceStoreRepository.query_pattern()
    v
Advisor Context
    |
    v
Recommendation
```

约定：

1. 检索输入是 **Story DNA + 查询条件**，不是完整故事正文；
2. 检索输出是**候选历史经验列表**（含引用与证据），不是「答案」；
3. 判断仍然发生在 Advisor：Experience Store 不产出风险等级，也不产出建议；
4. 查不到历史经验时返回空列表，Advisor 按「无历史上下文」的正常路径工作；
5. 本阶段**不实现**排序算法、相似度计算、向量检索、RAG。

```
Experience Retrieval (接口)
    |
    +-- get_related_experience(story_dna=..., episode_id=..., limit=...)
    |        -> [experience_record, ...]
    |
    +-- query_pattern(risk_type=..., tokens=..., limit=...)
             -> [risk_pattern, ...]
```

---

# 四、Write Path

写入流程同样**只定义接口**：

```
Observation Ledger
    |
    v
Advisor Feedback
    |
    v
Experience Store        <- ExperienceStoreRepository.save_experience()
```

保存内容：

| 保存什么 | 数据来源 |
| --- | --- |
| 观察结果 | Episode Observation Ledger 的最新快照 |
| 人工反馈 | Advisor Feedback 记录（`PFB-*.json`） |
| 生产结果 | 创作者填写的 `production_outcome` |

写入原则：

1. 追加写入，旧经验不覆盖、不删除；
2. 只存引用与事实，不复制 Story DNA / Advisor Report 正文；
3. 写入由人触发（沿用 Shadow Observation 的人工入口），Runtime 不调用；
4. 写入失败不得影响 Advisor 与生产流程（沿用既有 `blocks_production=false` 约定）。

---

# 五、Repository / Interface 设计

接口定义在 `pre_production/memory_adapter/`，只定义签名，不实现数据库。

```
pre_production/memory_adapter/
├── adapter.py              MemoryAdapter（既有读取 facade，本阶段不改行为）
├── experience_schema.py    Experience / Risk Pattern / Creator Decision 契约与校验
├── experience_store.py     ExperienceStoreRepository 接口 + 记录构造器
└── tests/                  契约测试（schema / interface / backward compatibility）
```

```python
class ExperienceStoreRepository(ABC):
    """Pre Production Experience Store 的读/写接口（仅接口，不含数据库实现）。"""

    @abstractmethod
    def save_experience(self, record: dict) -> dict:
        """追加保存一条 experience_record；返回保存结果（含保存位置）。"""

    @abstractmethod
    def get_related_experience(self, *, story_dna: dict | None = None,
                              episode_id: str | None = None,
                              limit: int | None = None) -> list:
        """返回相关历史 experience_record 候选；不排序打分，不做智能检索。"""

    @abstractmethod
    def query_pattern(self, *, risk_type: str | None = None, tokens=(),
                      limit: int | None = None) -> list:
        """返回匹配的 risk_pattern 候选；匹配语义由未来实现定义。"""
```

接口约束：

- 三个方法都只处理「经验数据」，不返回风险等级、不返回建议、不返回 PASS/FAIL；
- 不做写回：接口里没有任何修改 Advisor 规则 / Lexicon / 权重的入口；
- `MemoryAdapter` 保持既有行为不变（读历史 Story Lock、写 Review Reference），
  未来 Experience Store 实现替换在 `MemoryAdapter` **之后**，调用方无感知。

---

# 六、Memory 与 Advisor 边界

```
Memory 提供经验            Advisor 消费经验
    |                          |
    +---- 数据 --------------->+
    |                          |
    +<--- 新经验（人工反馈）----+   （仅通过人手动写入路径，不是 Advisor 自动回写）
```

- Memory 提供经验：只读地给出历史案例与模式，不改变 Advisor 的判断逻辑。
- Advisor 消费经验：把历史上下文纳入提示，但最终判断仍由 Advisor 基于当前 Evidence 产出。
- **Memory 不改变 Advisor**：不写规则、不调权重、不改 Lexicon。
- **Advisor 不修改 Memory**：Advisor 运行时不写经验库；经验只由人工反馈路径沉淀。
- 没有任何自动化回路：本阶段不存在「Advisor 读取经验 → 自动调整 → 再影响下一次判断」的闭环。

---

# 七、未来演进

当前阶段**不实现**，仅登记演进方向：

```
Experience Store
    |
    v
Pattern Learning        （多 Episode 归纳规律；需独立评审）
    |
    v
Advisor Improvement     （规则/词表/权重的人工评审后调整）
```

演进前置条件（缺一不可）：

1. Experience Store 已有足够真实样本，且样本全部来自人工确认的反馈；
2. Pattern Learning 产出必须可解释、可回溯到 Evidence；
3. 任何 Advisor 改动都必须是**人工评审后显式修改**，不允许由经验库自动改写；
4. 仍然不得引入评分系统，不得引入生产阻断。

本阶段明确不做：自动学习、自动调参、自动改规则、自动阻断、复杂知识图谱。

---

# 八、冻结边界（本阶段）

- 不修改 Runtime，不修改生产链。
- 不修改 `meta/episode-state.json`、`meta/story-gates.json`。
- 不自动调整 Advisor 规则，不自动修改 Lexicon，不自动修改 Similarity 权重。
- 不引入评分系统，不把 Feedback 变成硬规则。
- 只新增文档、契约与接口；一切失败必须保持 `blocks_production=false`。

对应产物：

- 文档：本文件。
- 契约：`contracts/experience_record.schema.json`、`contracts/risk_pattern.schema.json`、
  `contracts/creator_decision_experience.schema.json`。
- 接口：`pre_production/memory_adapter/experience_store.py` 的 `ExperienceStoreRepository`。
- 测试：`pre_production/memory_adapter/tests/`。
