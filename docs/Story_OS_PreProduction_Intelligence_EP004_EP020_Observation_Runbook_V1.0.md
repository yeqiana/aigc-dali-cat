# Story OS PreProduction Intelligence EP004-EP020 Observation Runbook V1.0

更新时间：2026-09-11

状态：Runbook（执行规范；只描述已有命令，不新增能力，不接入 Runtime）

> 本文是 `Experience_Accumulation_Plan_V1.0.md` 第二节「观察周期」的可执行细化，
> 也是 `Experience_Evaluation_V1.0.md` 单集观察报告模板的操作版。
> 本文不定义新能力、不定义算法、不定义评分，只规定「每一集按什么顺序、跑什么命令、留下什么产物」。
> 全部命令都来自已经实现的 CLI；本文不引入新命令、新字段、新契约。

---

# 一、目标

EP004 – EP020 这一批真实 Episode 只做两件事：

1. **验证 Advisor**：它在真实生产里有没有发现真问题、有没有误报、建议有没有用；
2. **积累 Experience**：把这些真实发生过的事实按统一格式沉淀成可审计的经验记录。

明确不是：

- 不是训练模型：不产训练集、不做自动学习；
- 不是优化 Advisor：本阶段不改规则、不改 Lexicon、不改 Similarity 权重；
- 不是 Pattern Learning：不做归纳、不产出规律、不自动调整任何阈值；
- 不是新的生产门禁：Runbook 里的每一步都不阻断、不替代、不修改生产流程。

## 1.1 三个角色（不变）

```
Advisor     -> 只提供建议（Advisory Only）
Experience  -> 只记录事实（fact store，append-only）
Runtime     -> 继续按原流程生产（本 Runbook 完全不介入）
```

## 1.2 适用范围

| 适用 | 不适用 |
| --- | --- |
| EP004 – EP020 的新集 | EP001 / EP002 / EP003（已作为回归 fixture 定版） |
| 人工触发的观察与记录 | Runtime 自动挂载、后台任务、hook |
| 生产前 / 生产后的人工动作 | 任何生产阶段推进、任何门禁证据 |

---

# 二、Episode 标准流程（固定五步）

```
Step 1  Story Lock
   |
   v
Step 2  Advisor Analysis
   |
   v
Step 3  Observation Record
   |
   v
Step 4  Production Outcome
   |
   v
Step 5  Feedback + Experience Save
```

## Step 1｜Story Lock

- 输入：该集的 Story Lock（已通过原有流程锁定，Runbook 不参与锁定）。
- 动作：确认 Story Lock 文件存在且内容稳定；记录它的 SHA256（后续引用锚点）。
- 产物：无新增产物（Story Lock 属于生产，不属于本层）。
- 失败边界：Story Lock 缺失时本集不进入观察，**不伪造**，也不跳过后续步骤。

## Step 2｜Advisor Analysis

命令：

```
python -m pre_production analyze <episode_dir> --out-dir <episode_dir>/meta/pre-production
```

- 产物：`story_fingerprint.yaml`、`similarity_report.yaml`、`advisor_report.yaml`，写入 `<episode>/meta/pre-production/`。
- 只读性：`analyze` 默认只打印；只有显式给 `--out-dir` 才落盘，且只落这三份产物。
- 失败边界：Advisor 出错不阻断生产；此时本集记为空观察，不编造 decision 与 evidence。

## Step 3｜Observation Record

命令：

```
python -m pre_production observe record --report <episode_dir>/meta/pre-production/advisor_report.yaml
```

- 产物：Episode Observation Ledger 追加一行（默认 `reports/pre-production/observation-ledger.jsonl`）。
- 幂等：同一 Story Lock 版本重复记录返回 REUSED，不重复追加；状态只前向推进。
- 状态机：`OBSERVED` -> `FEEDBACK_PENDING` -> `COMPLETED`（这是 Ledger 自己的观察状态，与 `meta/episode-state.json` **无关**）。
- 失败边界：校验不过就报错退出，不产生半条记录。

## Step 4｜Production Outcome

- 输入：该集最终生产结果（完成 / 归档 / 重做 / 未生产），由人判断，写成自由文本。
- 记录位置：**Experience 记录的 `production_outcome` 字段**，在 Step 5b 写入时一起提交。
- 尚未生产完的集：本步留空，经验记录记为 `incomplete`，等真实结果回来再补一次写入（不补造、不猜测）。
- 可选增强：`audience_feedback` 由发布后数据阶段拥有，本 Runbook 只做原样搬运，不计算任何比率。
- 说明：Observation Ledger 里也有同名字段，Python API（`run_observation(production_outcome=...)`）可写入；CLI 路径不写，因此完整性判定以 Experience 记录为准。

## Step 5｜Feedback + Experience Save

Step 5a 写人工反馈：

```
python -m pre_production observe feedback --report <episode_dir>/meta/pre-production/advisor_report.yaml ^
    --creator-decision ACCEPT|REVISE|IGNORE ^
    --recommendation-result USEFUL|PARTIAL|NOT_USEFUL ^
    --risk-acknowledged yes|no ^
    [--revision-direction TEXT] [--final-effect TEXT] [--notes TEXT]
```

Step 5b 落库经验：

```
python -m pre_production experience save ^
    --feedback reports/pre-production/advisor-feedback/PFB-<report_id>.json ^
    --observation <OBS id 或 observation.json> ^
    --similarity <episode_dir>/meta/pre-production/similarity_report.yaml ^
    --production-outcome "<Step 4 的结果文本>"
```

- 产物：`PFB-*.json`（人工反馈）、`creator-decisions.jsonl` 一条 Creator Decision Experience、`experience-records.jsonl` 一条 Episode Experience，以及每个 Similarity Evidence 对应的 `risk-patterns.jsonl` 记录。
- 幂等：重复 `experience save` 返回 REUSED，不产生第二份记录，不覆盖历史。
- 只存引用：不复制 Advisor Report / Story DNA 正文。
- 失败边界：校验不过抛明确异常，不吞错、不留下半条记录；失败不影响 Advisor，也不影响生产。

## 2.1 时序说明（两种合法写法）

| 写法 | 顺序 | 适用 |
| --- | --- | --- |
| 一次写完 | 生产结束后再执行 Step 5a + 5b，此时 Step 4 结果已知 | 推荐：经验记录一次就是 complete |
| 分两次写 | 读完报告立刻写 Step 5a 反馈；结果出来后再 `experience save` 带 `--production-outcome` | 需要尽早留下人工判断时 |

两种写法都不改变「无自动环节」这一前提：每一步都由人执行。

---

# 三、每集必须产出（Required Artifacts）

| # | Artifact | 路径 | 由谁产生 | 缺失后果 |
| --- | --- | --- | --- | --- |
| 1 | story_fingerprint.yaml | `<episode>/meta/pre-production/` | Step 2 | 无 Story DNA 引用，经验无法 complete |
| 2 | similarity_report.yaml | `<episode>/meta/pre-production/` | Step 2 | 无 Risk Pattern 可落库，风险不可回溯 |
| 3 | advisor_report.yaml | `<episode>/meta/pre-production/` | Step 2 | Step 3 / Step 5a 无法执行 |
| 4 | observation record | `reports/pre-production/observation-ledger.jsonl` | Step 3 | 无观察事实，事后无法复盘该集 |
| 5 | feedback record | `reports/pre-production/advisor-feedback/PFB-*.json` | Step 5a | 经验缺人工判断，直接判为 incomplete |
| 6 | experience record | `reports/pre-production/experience-store/experience-records.jsonl` | Step 5b | 该集不进入经验积累样本 |

三份 YAML 的契约校验：

```
python -m pre_production validate <yaml> --kind dna|similarity|advisor
```

产物缺失时的处理：**如实记为 incomplete**，不伪造，也不用别的集的数据顶替。

---

# 四、观察周期

```
EP004 - EP008   接入验证阶段   目标：确认链路稳定
EP009 - EP014   中期观察阶段   目标：观察误报与建议质量
EP015 - EP020   收敛阶段       目标：评估是否具备 Pattern Learning 前置条件
```

| 阶段 | 范围 | 每段结束时回答 | 产出 |
| --- | --- | --- | --- |
| 接入验证 | EP004 – EP008 | 五步是否都能跑通？六项产物是否每集齐全？ | 接入小结（链路问题清单） |
| 中期观察 | EP009 – EP014 | 误报是什么形态？建议有没有被采纳、采纳后有没有用？ | 中期小结（风险形态 + 误报形态） |
| 收敛 | EP015 – EP020 | 完整经验够不够？是否反复出现同一 Pattern？ | 批次评审（是否进入 Pattern Learning） |

每次小结用只读统计取事实快照：

```
python -m pre_production experience stats
python -m pre_production experience list --kind all --json
```

两条命令都只读：不写文件、不改 JSONL、不评分、不下结论。

阶段只是评审节奏，**不是门禁**：任何阶段都不阻断生产，也不改变 episode 状态。

---

# 五、人工复盘模板（每集五问）

每集生产结束后，人回答下面五个问题；答案写进 `docs/templates/episode_observation_template.md`。

| # | 问题 | 依据 |
| --- | --- | --- |
| 1 | Advisor 是否发现问题？ | `advisor_report.yaml` 的 `decision / risks / confidence` |
| 2 | 风险是否真实？ | 逐条对照 `evidence_id` 与人工判断 |
| 3 | 建议是否采用？ | `creator_decision`（ACCEPT / REVISE / IGNORE）+ `recommendation_result` |
| 4 | 最终结果如何？ | `production_outcome` + 可选 `audience_feedback` |
| 5 | 哪些经验值得保存？ | 本次 Risk Pattern 的 token 组合 + 备注 |

填写要求：

- 每条判断都要指向具体 `evidence_id` 或 `feedback_id`，不接受无引用结论；
- 允许写「样本不足」，不允许猜；
- 禁止百分比、禁止换算等级、禁止总分：要写就写「8 条里 6 条认可，2 条误报」并保留条目清单；
- 结论只允许三类定性词：证据支持 / 证据不足 / 样本不足。

---

# 六、Experience 完整性检查

## 6.1 Good Experience（四要素齐全）

```
Story DNA Reference
      +
Advisor Report Reference
      +
Human Feedback Reference
      +
Production Outcome
      =
Good Experience (complete)
```

## 6.2 缺任一要素即 incomplete

```
python -m pre_production experience stats

quality : standard=story_dna + advisor_report + human_feedback + production_outcome
          complete=0 incomplete=3 missing={production_outcome: 3}
```

- `incomplete` 记录**保留**：它仍是真实发生过的观察事实，append-only 不可覆盖、不可删除；
- **禁止补造**：缺 `production_outcome` 就等真实结果，用真实值重写一次（重复保护会正确处理）；
- 不完整的记录**不进入**未来的 Pattern Learning 样本集；
- 完整性只说明「记录齐不齐」，**不说明 Advisor 说得对不对**：准不准由人工反馈字段承载。

## 6.3 每集收尾检查清单

1. 三份 YAML 是否都落盘，且 `validate` 通过；
2. 观察记录是否已在 `observe list` 中出现；
3. 反馈文件是否已写入 `reports/pre-production/advisor-feedback/`；
4. `experience list --episode <id>` 是否能查到该集；
5. `experience stats` 中该集是否 complete；若为 incomplete，写明缺什么、什么时候补；
6. 本集复盘模板是否填写完毕。

---

# 七、Pattern Learning 进入条件

## 7.1 不自动进入

本 Runbook **不会**因为数字到了就切换阶段。只读统计只展示现状：

```
pattern goal: documented=30-50 complete Episode Experience, all with human feedback
              complete_experiences=0 with_feedback_reference=3
```

`documented` 是人写的门槛原文，工具不解析、不比较、不判定。

## 7.2 人工评审的三个条件

进入 Pattern Learning 必须由人评审通过，且同时满足：

1. **30 – 50 条完整 Experience**：每条四要素齐全，且不是同一集的重复 ingest；
2. **重复 Pattern**：同一 Risk Pattern 形态（token 组合）在多个不同 Episode 上反复出现；
3. **人工确认有效**：人确认这些重复形态是真实风险，而不是 Advisor 的误报惯性。

## 7.3 评审时的附加约束

- 结论必须可回溯到 `evidence_id` 与 `feedback_id`；
- 任何 Advisor 改动都必须是人工评审后**显式修改**，不允许由经验库自动改写；
- 仍然不得引入评分系统，不得引入生产阻断；
- 本阶段明确不做：自动学习、自动训练、自动调参、RAG、Embedding、向量检索。

---

# 八、冻结边界（本阶段）

禁止：

1. 修改 Runtime；
2. 修改 `meta/episode-state.json`；
3. 修改 `meta/story-gates.json`；
4. 修改 Advisor 规则；
5. 修改 Lexicon；
6. 修改 Similarity 权重；
7. 实现 Pattern Learning；
8. 自动学习；
9. 自动调整推荐。

保持：Advisor 只提供建议；Experience 只记录事实；所有失败 `blocks_production=false`。

本阶段产物：

- 本文；
- `docs/templates/episode_observation_template.md`（每集复盘模板）；
- README 使用说明（`pre_production/README.md`）。

本 Runbook 不新增代码、不新增契约、不新增命令；它只规定人怎么用已有能力。

