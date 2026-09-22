# Story OS PreProduction Intelligence Experience Accumulation Plan V1.0

更新时间：2026-09-11

状态：Design + Read-only Tooling（只读统计已实现；不接入 Runtime，不修改生产链）

> 关系说明：本文是 `Story_OS_PreProduction_Intelligence_Shadow_Observation_Plan_V1.0.md` 的延续。
> Shadow Observation Plan 定义「观察什么」；Experience Store Integration 定义「经验怎么存」；
> 本文定义「怎么积累、积累到什么程度才算够」。
> 本文不定义评分模型，不定义算法，不定义 Advisor 改动。

---

# 一、目标

当前阶段目标：**收集真实 Episode 数据，验证 Advisor 是否有效。**

本条明确写下「不是」什么：

- 不是优化模型：不调参、不改规则、不改 Lexicon、不改 Similarity 权重。
- 不是扩展 AI 能力：不引入 Pattern Learning、自动训练、RAG、Embedding。
- 不是给 Advisor 打分：不产出准确率、不产出百分比、不产出等级换算。

成功判据（本阶段唯一判据）：

1. 有足够多的**完整** Episode Experience（四要素齐全，见第五节）；
2. 每一条都带**人工反馈**（人写的判断，不是系统推断）；
3. 这些经验可以被只读地统计出来，用作后续人工评审的输入。

失败判据也很明确：如果积累下来的经验缺引用、缺人工反馈，那么再多条记录也不算「有经验」。

## 1.1 三个角色的职责（不重复设计，只确认）

| 角色 | 职责 | 本阶段是否改变 |
| --- | --- | --- |
| Experience Store | 事实记录：存引用、存计数、存标签 | 否，Runtime MVP 已实现 |
| Advisor | 只读消费者：在需要时才读经验 | 否，本阶段仍不读取经验 |
| Feedback | 经验来源：人写的判断 | 否，仍为人工入口 |

一句话：本阶段只增加「采集与统计」，不增加「推理与决策」。

---

# 二、观察周期

## 2.1 第一批观察集

**EP004 – EP020（共 17 集）** 作为第一批观察集。

为什么不从 EP001 开始：

- EP001 / EP002 是当前系列的在制样本，EP003 已归档；三者已作为回归 fixture 定版，
  继续改动它们会让「历史经验」失去参照意义。
- EP003（雾中的另一座生活区）已归档，只能作为回归锚点，不能再作为「边生产边积累」的样本。
- 因此真实积累从**下一个新 Episode（EP004）**开始。

## 2.2 分三段观察

| 段位 | 范围 | 关注点 |
| --- | --- | --- |
| 接入段 | EP004 – EP008 | 链路是否跑通：Advisor 能否出报告、人能否写反馈、经验能否落库 |
| 中期段 | EP009 – EP014 | 反馈是否成规模：风险类型是否重复出现、误报是否成模式 |
| 收敛段 | EP015 – EP020 | 是否够进入第六节定义的前置条件 |

段位只是评审节奏，不是阶段门禁；任何一段都不阻断生产。

## 2.3 每集固定动作

1. Story Lock 之前/之后运行 Advisor（`shadow` 或 `analyze`），得到 `advisor_report.yaml`；
2. 用 `observe record` 把这次观察记进 Episode Observation Ledger；
3. 人阅读报告，用 `observe feedback` 写下判断（是否认可风险 / 是否采纳建议 / 修改方向 / 最终效果）；
4. 生产结束后，人把结果写成 `production_outcome`；
5. 用 `experience save` 落库；可选 `--similarity` 把每条 Similarity Evidence 落成一条 Risk Pattern。

约束：

- 每集只写一次经验；重复 ingest 是幂等的，返回 `REUSED`，不产生第二份记录。
- 生产结果还没出来时不补造：先落 observation + feedback，`production_outcome` 留空，
  该条在统计里记为 `incomplete`，等结果回来再补一次真实写入。
- 本 checkout 里不存在的 Episode 不伪造数据；缺集就是缺集。

---

# 三、Episode Experience 生命周期

NaN
Episode
   |
   v
Advisor Report          -> advisor_report.yaml（人读的那份报告）
   |
   v
Observation             -> Episode Observation Ledger（append-only 事实）
   |
   v
Human Feedback          -> PFB-*.json（人写的判断，唯一主观来源）
   |
   v
Experience Store        -> experience-records.jsonl / risk-patterns.jsonl / creator-decisions.jsonl
   |
   v
Evaluation              -> 只读统计 + 人工观察报告（本阶段唯一产出，不回写任何一环）
NaN

| 环节 | 产物 | 谁触发 | 是否写生产事实 |
| --- | --- | --- | --- |
| Episode | Story Lock 版本 | 生产流程 | 是（属于生产，不由本层写） |
| Advisor Report | `advisor_report.yaml` | 人或 Runtime 运行 Advisor | 否 |
| Observation | `observation-ledger.jsonl` 一行 | 人工入口 | 否 |
| Human Feedback | `advisor-feedback/PFB-*.json` | 人工入口 | 否 |
| Experience Store | 三个 append-only JSONL | 人工入口 `experience save` | 否 |
| Evaluation | 只读统计输出 + 人工报告 | 人运行 `experience stats` | 否 |

关键约束：

- 生命周期里**没有自动环节**：每一步都由人触发，没有 hook，没有后台任务。
- Evaluation 是**只读终点**：它读三份 JSONL，不写任何文件，不改任何状态。
- 整条链不碰 `meta/episode-state.json`、不碰 `meta/story-gates.json`、不碰 Runtime。

---

# 四、采集指标

## 4.1 定位：指标是「人复核时回答的问题」，不是自动计算的分数

下面四个指标定义「积累期要关注什么」，不定义公式、不定义阈值、不定义等级换算。
只读统计工具只做**标签计数**：数一数各类标签出现了多少条，绝不把计数折算成百分比或评级。
契约层面直接拒收 `score / rating / percent / percentage / points / grade / rank / stars / threshold` 这类键名。

## 4.2 四个指标

### 1) Risk Hit Rate

问题：Advisor 给出的 `WARNING` / 高风险条目，**是否被人工认可**。

事实来源：Advisor Feedback 的 `risk_acknowledged` 与 `creator_decision`。
只读统计输出：相应标签的**计数**（例如 `creator_action={"ACCEPT": 3, "IGNORE": 1}`）。
不输出：命中率百分比。

### 2) False Positive Rate

问题：Advisor 报出的风险里，**哪些是误报**。

事实来源：`risk_acknowledged=false` 与 `recommendation_result=NOT_USEFUL` 的条目。
只读统计输出：误报标签的计数，以及对应 Episode / Risk Pattern 的引用。
不输出：误报率百分比。

### 3) Recommendation Adoption Rate

问题：Advisor 的建议**是否被采纳**。

事实来源：Advisor Feedback 的 `creator_decision`（`ACCEPT / REVISE / IGNORE`）。
只读统计输出：三个标签各自的计数（在 Creator Decision Experience 与统计的 `distribution` 中）。
不输出：采纳率百分比。

### 4) Outcome Feedback

问题：**最终生产效果如何**。

事实来源：已生产 Episode 的 `production_outcome`（自由文本）与可选的 `audience_feedback`（平台原始数据，由发布后阶段拥有）。
只读统计输出：该字段是否有值（决定经验是否 complete），不解释、不加工、不折算。
不输出：任何效果评分。

## 4.3 与既有 Shadow Observation 指标的关系（避免第二套口径）

| Shadow Observation Plan V1.0 | 本文 | 关系 |
| --- | --- | --- |
| Risk Hit Rate | Risk Hit Rate | 沿用同名，只补「用哪个已存字段回答」 |
| False Positive Rate | False Positive Rate | 沿用同名 |
| Recommendation Adoption Rate | Recommendation Adoption Rate | 沿用同名 |
| Creator Feedback Quality | （并入 Human Feedback 字段本身） | 不新增第三套词表：反馈质量由 `creator_decision / recommendation_result / notes` 承担 |
| — | Outcome Feedback | 本文新增：把「生产结果」纳入经验完整性 |

## 4.4 硬性禁止

- 不定义评分模型：没有权重、没有归一化、没有阈值、没有总分。
- 不产出「Advisor 准确率 xx%」这类结论：百分比必须由人读完条目后自行判断，且只能写在人工报告里，
  不落进 Experience Store，也不落进契约。
- 不把计数当结论：计数说明「有多少条这样的记录」，不说明「Advisor 好不好」。

---

# 五、经验质量标准

## 5.1 Good Experience

一条 Episode Experience 只有在**四要素齐全**时才算 Good（统计字段 `quality.complete`）：

1. Story DNA 引用（`story_dna_reference`）；
2. Advisor Report 引用（`advisor_report_reference`）；
3. Human Feedback 引用（`feedback_reference`）；
4. Production Outcome（`production_outcome`）。

标准原文以字符串形式登记在只读统计中：`QUALITY_STANDARD = "story_dna + advisor_report + human_feedback + production_outcome"`。

## 5.2 Bad Experience

**缺少任一关键引用**即为 Bad（统计字段 `quality.incomplete`），并按字段列出缺什么：

NaN
quality.incomplete               # 不完整条数
quality.missing_by_field         # 例如 {"production_outcome": 3}
quality.complete_episodes        # 四要素齐全的 episode_id
NaN

Bad Experience 的处理原则：

- **不删除**：它仍是真实发生过的观察事实，append-only 不可覆盖。
- **不补造**：缺 `production_outcome` 就等真实结果，用真实值补一条（重复保护会正确处理）。
- **不入样本集**：不完整的记录不进入未来 Pattern Learning 的样本集（见第六节）。

## 5.3 完整性不等于正确性

完整只说明「记录齐不齐」，不说明「Advisor 说得对不对」。
准不准由人工反馈字段（`risk_acknowledged / creator_decision / recommendation_result / notes`）承载，
由人在观察报告里做定性判断（见 Experience Evaluation V1.0），不由统计输出下结论。

## 5.4 audience_feedback 的位置

NaNaudience_feedback` 是**可选增强**，不参与 complete / incomplete 判定：
它由发布后数据阶段拥有，只做原样搬运，不计算完播率、不计算转化、不生成任何派生分数字段。

---

# 六、Pattern Learning 前置条件

## 6.1 数量与质量门槛

进入 Pattern Learning 之前必须同时满足：

1. 至少 **30 – 50 条 complete Episode Experience**；
2. 每一条都带**人工反馈**（`feedback_reference` 非空且指向真实 PFB 记录）；
3. 样本覆盖多个 Episode，且不是同一集的重复 ingest。

## 6.2 工具只登记事实，不自动判定

只读统计把该门槛登记为一条**字符串事实**，只展示现状，不做判定：

NaN
pattern goal: documented=30-50 complete Episode Experience, all with human feedback
              complete_experiences=0 with_feedback_reference=3
NaN

- `documented`：人写的门槛原文，工具不解析、不比较。
- `complete_experiences`：当前完整经验条数（计数）。
- `with_feedback_reference`：带人工反馈引用的条数（计数）。
- 工具**不输出**「是否达标」，也**不会**因为数字到了就切换阶段。是否进入 Pattern Learning 由人另行评审决定。

## 6.3 其他前置条件（沿用 Experience Store Integration 第七节）

- Pattern Learning 的产出必须可解释、可回溯到 Evidence；
- 任何 Advisor 改动都必须是**人工评审后显式修改**，不允许由经验库自动改写；
- 仍然不得引入评分系统，不得引入生产阻断。

## 6.4 本阶段明确不做

自动学习、自动训练、自动调参、自动改规则、RAG、Embedding、向量检索、生产阻断。

---

# 七、冻结边界（本阶段）

禁止：

1. 修改 Runtime 执行链；
2. 修改 `meta/episode-state.json`；
3. 修改 `meta/story-gates.json`；
4. 自动调整 Advisor；
5. 自动修改 Lexicon；
6. 自动修改 Similarity 规则；
7. 引入 Pattern Learning；
8. 引入自动训练；
9. 引入 RAG；
10. 引入 Embedding。

保持：Experience Store = 事实记录；Advisor = 只读消费者；所有失败 `blocks_production=false`。

本阶段产物：

- 文档：本文、`Story_OS_PreProduction_Intelligence_Experience_Evaluation_V1.0.md`；
- 只读统计实现：`pre_production/memory_adapter/experience_stats.py` 与 CLI `experience stats`；
- 测试：`pre_production/memory_adapter/tests/test_experience_stats.py`。


