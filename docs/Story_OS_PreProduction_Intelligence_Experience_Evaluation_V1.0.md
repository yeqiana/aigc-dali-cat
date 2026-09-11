# Story OS PreProduction Intelligence Experience Evaluation V1.0

更新时间：2026-09-11

状态：Design Only（只定义人工评估方法与报告结构；不实现算法）

> 本文回答一个问题：**积累了经验之后，怎么判断 Advisor 到底有没有用。**
> 本文定义的是**人工评估流程与报告结构**，不是算法、不是评分模型、不是自动判定。
> 相关文档：`Experience_Accumulation_Plan_V1.0.md`（积累什么）、
> `Experience_Store_Integration_V1.0.md`（经验怎么存）、
> `Shadow_Observation_Plan_V1.0.md`（观察什么）。

---

# 一、目标与边界

## 1.1 目标

在经验积累期内，用**人工评审**回答四个问题：

1. Advisor 报出的风险，人认可吗；
2. 有没有误报，误报是什么形态；
3. Advisor 的建议，人采纳了吗，采纳后有用吗；
4. 最终生产效果如何，和 Advisor 当初的判断有没有关系。

## 1.2 明确不做

- **不实现算法**：不写自动评估代码，不写打分函数，不做统计推断。
- **不产出数字结论**：不计算准确率、命中率、采纳率；可以引用条目计数，但结论必须是定性的。
- **不自动调整 Advisor**：评估结论只用于人决定要不要改 Advisor；改动永远是人工显式修改。
- **不影响生产**：评估不写 `meta/episode-state.json`、不写 `meta/story-gates.json`、不阻断任何流程。

---

# 二、评估对象

| 评估什么 | 看哪个字段 | 由谁提供 |
| --- | --- | --- |
| Advisor 的判断 | `advisor_report.yaml` 的 `decision / risks / confidence` | Advisor |
| Advisor 的证据 | Similarity Evidence（`evidence_id / matched_features / risk_level / explanation`） | Similarity Analysis |
| 人的裁决 | Advisor Feedback（`risk_acknowledged / creator_decision / recommendation_result`） | 人 |
| 结果 | `production_outcome`（可选 `audience_feedback`） | 人 / 发布后数据阶段 |

注意：评估对象里**没有**「Advisor 分数」这一项，因为不存在这个字段，也不允许生成。

---

# 三、评估链路

NaN
Episode
   |
   v
Advisor Decision          WARNING / NEEDS_REVISION / PASS
   |
   v
Human Judgment            认可 / 误报 / 采纳 / 不采纳（写在 Advisor Feedback）
   |
   v
Outcome                   改稿后效果 / 最终生产结果（写在 production_outcome）
   |
   v
观察报告                  人写的定性结论 + 条目引用（本阶段唯一产出）
NaN

每一步的输入输出：

| 步骤 | 输入 | 输出 | 谁做 |
| --- | --- | --- | --- |
| 1 | Episode + Story Lock | Advisor Report | Advisor（人触发） |
| 2 | Advisor Report | Advisor Feedback（PFB-*） | 人 |
| 3 | 生产结果 / 复盘 | `production_outcome` | 人 |
| 4 | 上述引用 + 只读统计 | 观察报告 | 人 |

链路里没有任何自动环节，也没有任何环节回写前一步。

---

# 四、观察报告结构（人工填写）

观察报告是**自由文本文档**，本阶段不做机器契约；下面给出统一结构，便于横向对比。

NaN
# 观察报告：EP0xx

## 0. 引用
- advisor_report: <advisor_report.yaml 路径 / report_id>
- similarity_evidence: <用到的 evidence_id 列表>
- feedback: <PFB-* 路径 / feedback_id>
- experience: <EXP-* / CDE-* 记录 id>
- production_outcome: <自由文本>
- 统计快照: <python -m pre_production experience stats 的输出时间与要点>

## 1. Advisor 说了什么
- decision: WARNING / NEEDS_REVISION / PASS
- risks: 逐条列出（等级 + 摘要 + evidence_id）
- recommendations: 逐条列出

## 2. 人怎么看
- 认可的风险: <逐条，引用 risks 与 evidence_id>
- 误报: <逐条，写清为什么是误报>
- 漏报: <Advisor 没提但人认为存在的风险，自由文本>
- 建议采纳情况: ACCEPT / REVISE / IGNORE（逐条）
- 建议有用性: USEFUL / PARTIAL / NOT_USEFUL（逐条）

## 3. 结果
- 是否按建议改稿: 是 / 否 / 部分
- 修改方向: <自由文本>
- 最终效果: <自由文本>
- 与 Advisor 判断的关系: <自由文本，是否与当初的风险方向一致>

## 4. 结论（定性，不含数字）
- 本次 Advisor: 证据支持 / 证据不足 / 样本不足（只能选这三类词）
- 值得记入 Risk Pattern 的形态: <token 组合>
- 下一步: <自由文本>
NaN

填写原则：

- **逐条引用**：每条判断都要指向 `evidence_id` 或 `feedback_id`，不允许无引用结论。
- **允许说不知道**：样本不足时写「样本不足」，不猜。
- **不做算术**：不要写「准确率 80%」这类表述；要写就写「8 条里 6 条认可，2 条误报」并保留条目清单。

---

# 五、评审节奏

| 时机 | 范围 | 产出 |
| --- | --- | --- |
| 每集生产结束后 | 单集 | 一份单集观察报告（第四节模板） |
| 每 5 集 | EP004-EP008 / EP009-EP013 / EP014-EP018 … | 一份阶段小结：重复出现的风险形态 + 误报形态 |
| 第一批观察集结束时 | EP004-EP020 | 一份批次评审：是否达到 Pattern Learning 前置条件（数量 + 人工反馈覆盖） |

节奏只是评审计划，不是门禁；漏做一次评审不影响任何生产步骤。

评审使用只读统计作为事实快照，例如：

NaN
python -m pre_production experience list --kind all --json
python -m pre_production experience stats --json
NaN

两条命令都只读：counts / labels / 引用，不写文件、不排序、不评分。

---

# 六、结论词表（定性，禁止分数）

观察报告只允许使用下面三类定性结论，避免制造伪精确：

| 结论 | 含义 | 触发条件（人工判断，非自动） |
| --- | --- | --- |
| 证据支持 | 人工认可的条目明显多于被否定的条目，且建议产生了可见的修改 | 人读完后自己下的判断 |
| 证据不足 | 样本太少、或结论互相矛盾，还看不出方向 | 同上 |
| 样本不足 | 该形态在经验库里条数还不够，不足以讨论 | 同上 |

禁止的表达：任何百分比、任何换算等级（A/B/C）、任何总分、任何阈值比较结果。

---

# 七、与 Experience Store / Advisor 的关系

NaN
观察报告（人写）  --引用-->  Experience Store（只存事实）
        |                            |
        |                            +-- 不改变 Advisor
        |
        +-- 结论供人决定是否改 Advisor（人工评审后显式修改）
NaN

- Experience Store **提供**事实：给出历史条目与标签计数，不产出结论。
- 观察报告 **消费**事实：人把条目读成定性结论。
- Advisor **不被自动影响**：观察报告不会修改规则、词表、权重；本阶段也不存在自动回路。

---

# 八、冻结边界（本阶段）

- 不修改 Runtime，不修改 `meta/episode-state.json`，不修改 `meta/story-gates.json`。
- 不自动调整 Advisor，不自动修改 Lexicon，不自动修改 Similarity 规则 / 权重。
- 不引入 Pattern Learning、自动训练、RAG、Embedding。
- 不引入评分系统；不把 Feedback 变成硬规则。
- 所有失败保持 `blocks_production=false`。

本文件为设计文档，不附带实现；配套的只读统计见
NaNStory_OS_PreProduction_Intelligence_Experience_Accumulation_Plan_V1.0.md` 与 CLI `experience stats`。

