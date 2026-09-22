# Story OS PreProduction Intelligence Shadow Observation 阶段设计 V1.0

更新时间：2026-09-11

状态：Design + MVP Implemented（人工影子观察层，不接入 Runtime）

> 状态更新（2026-09-11）：本文件描述的 `pre_production/shadow_observation/` 模块已由
> `pre_production/observation/`（schema / ledger / feedback / observation runner）取代，
> 权威设计见 `docs/Story_OS_PreProduction_Intelligence_Shadow_Observation_Plan_V1.0.md`、
> `..._Advisor_Feedback_Model_V1.0.md`、`..._Episode_Observation_Ledger_V1.0.md`、
> `..._Human_Feedback_Entry_V1.0.md`。本文件保留为设计演进记录（Design History），
> 不作为当前实现契约。

---

# 一、定位

Shadow Observation 是 Pre Production Intelligence 的**人工影子观察层**，
位置在 MVP Release Plan 的 Phase 1 Shadow Mode 之内、Phase 2 Advisor Mode 之前。

它不产生新的判断能力，只负责把 Shadow Mode 已经产生的报告**留下痕迹**：

- 客观事实：这一次观察看到了什么（Episode Observation Ledger）。
- 主观判断：人认为这次 Advisor 说得对不对（Advisor Feedback）。

一句话：Shadow Mode 负责“说”，Shadow Observation 负责“记下来说了什么、以及人怎么看”。

---

# 二、目标与不做的事

本阶段目标：

1. 提供 Shadow Observation 文档（本文）。
2. 定义 Advisor Feedback 数据结构。
3. 定义 Episode Observation Ledger。
4. 提供人工反馈入口（命令行）。

本阶段明确不做：

- 不接入 Runtime，不修改任何 Runtime 代码或流程。
- 不阻断生产，不新增 Production Gate。
- 不修改 `meta/episode-state.json` 状态机，不新增第二状态机。
- 不修改 `meta/story-gates.json` 的权威职责。
- 不做自动判断、自动评分、自动改进。
- 不把任何观察结果回写成生产事实。

---

# 三、与现有 MVP 的关系

```
Story Lock
   |
   v
Story DNA Extraction      -> story_fingerprint.yaml
   |
   v
Similarity Analysis       -> similarity_report.yaml
   |
   v
Evidence Generation
   |
   v
Advisor Report            -> advisor_report.yaml
   |
   v
Memory Adapter            -> Review Reference
   |
   v
Shadow Mode               -> 只出报告，继续原生产流程
   |
   v
Shadow Observation        -> 人工记账 + 人工反馈（本阶段，纯附加）
```

Shadow Observation 不改上面任何一环，只在 Shadow Mode 之后增加两个可选的人工动作。

---

# 四、Episode Observation Ledger

## 4.1 定位

append-only JSONL，一行一次影子观察。它是**派生经验记录**，不是 episode authority。

默认路径：`reports/pre-production/observation-ledger.jsonl`。
契约：`pre_production/contracts/observation_ledger_entry.schema.json`。

## 4.2 去重规则

去重键：`(run_mode, episode_id, story_lock_sha256)`。

- 同一个 Story Lock 版本重复观察 -> 返回 `REUSED`，不重复追加。
- Story Lock 内容变化（SHA 变化）-> 视为新观察，追加新行。

这样账本天然绑定 Story Lock 版本，而不是记录“观察次数”。

## 4.3 字段

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `schema` | str | 固定 `observation_ledger_entry` |
| `schema_version` | int | 固定 `1` |
| `observation_id` | str | `OB-<episode>-<sha8>` |
| `recorded_at` | str | 本地时区 ISO 时间 |
| `run_mode` | str | 固定 `shadow` |
| `episode_id` | str | 集标识 |
| `title` | str | 标题 |
| `advisor_report_id` | str | 对应 Advisor Report id |
| `story_lock_sha256` | str | 被观察的 Story Lock 版本 |
| `rule_version` | str | Advisor 规则版本 |
| `decision` | str | `PASS / WARNING / NEEDS_REVISION` |
| `confidence` | str | `LOW / MEDIUM / HIGH` |
| `risk_count` | int | 风险条数（真实计数） |
| `evidence_count` | int | 证据条数（真实计数） |
| `highest_risk_level` | str | `HIGH / MEDIUM / LOW / NONE` |
| `matched_dimensions` | list | 命中的 Story DNA 维度 |
| `recommendations` | list | 建议 token |
| `artifact_dir` | str/null | 三份产物的落盘目录 |
| `feedback_id` | str/null | 关联的人工反馈 id |
| `advisory_only` | bool | 必须为 `true` |
| `blocks_production` | bool | 必须为 `false` |
| `mutates_episode_state` | bool | 必须为 `false` |
| `mutates_story_gates` | bool | 必须为 `false` |
| `authority` | str | 固定 `derived_non_authority` |

契约对 `blocks_production / mutates_episode_state / mutates_story_gates` 强制为 `false`，
对 `advisory_only` 强制为 `true`；校验不过就不允许写入。

---

# 五、Advisor Feedback 数据结构

## 5.1 定位

记录“人怎么看这份 Advisor 报告”。这是本阶段**唯一**存放人工判断的地方。

默认路径：`reports/pre-production/advisor-feedback/PFB-<report_id>.json`。
契约：`pre_production/contracts/advisor_feedback.schema.json`。

## 5.2 绑定精确报告版本

反馈记录 `advisor_report_sha256`，绑定的是**当时那一版报告**。报告重新生成后，
旧反馈不会被误当成本次判断。

## 5.3 字段

| 字段 | 取值 | 含义 |
| --- | --- | --- |
| `feedback_id` | `PFB-<report_id>` | 反馈标识 |
| `advisor_report_id` | str | 被判断的报告 |
| `advisor_report_sha256` | str | 被判断的报告版本 |
| `episode_id` | str | 集标识 |
| `advisor_decision` | str | 报告当时的 decision |
| `judgement_source` | `human` | 只允许人工 |
| `creator_decision` | `pending/accepted/revised/ignored` | 作者是否采纳 |
| `advisor_accuracy` | `correct/partially_correct/incorrect/unknown` | 人工准确度标签 |
| `confirmed_evidence` | list | 被证实的 `evidence_id` |
| `refuted_evidence` | list | 被推翻的 `evidence_id` |
| `missed_risks` | list | Advisor 漏掉的风险（自由文本） |
| `notes` | str | 人工备注 |
| `review_reference_id` | str/null | 指向 Memory Adapter 的经验记录 |
| `created_time` | str | 本地时区 ISO 时间 |

契约强制 `judgement_source = human`，准确度只能取四个人工标签，
并禁止 `score / rating / percent / percentage / points / grade / rank / stars` 等键名。

## 5.4 引用了不存在的证据怎么办

反馈里的 `confirmed_evidence / refuted_evidence` 如果引用了报告没有声明的 `evidence_id`，
入口只给 warning，不拒绝、不阻断，也不自动改写报告。

---

# 六、人工反馈入口设计

入口只有一个：命令行 `python -m pre_production observe ...`。纯手动，无自动触发。

## 6.1 子命令

```powershell
# 记录一次影子观察：只读分析 + 追加一行账本（可 --dry-run 只预览）
python -m pre_production observe record <episode_dir> [--ledger PATH] [--out-dir DIR] [--dry-run]

# 写下人工判断：把一份 advisor_report.yaml 变成一条 Advisor Feedback
python -m pre_production observe feedback --report <advisor_report.yaml> `
    [--store DIR] [--decision D] [--accuracy A] `
    [--confirmed ID]... [--refuted ID]... [--missed TEXT]... [--notes TEXT] [--dry-run]

# 回看账本：打印汇总与逐行记录（可 --json，可按集过滤）
python -m pre_production observe list [--ledger PATH] [--episode ID] [--json]
```

## 6.2 反馈流程（全人工）

1. 人运行 `shadow` 或 `analyze` 得到 `advisor_report.yaml`。
2. 人阅读报告，决定是否采纳、准不准、哪条证据成立。
3. 人运行 `observe feedback` 写下判断（写入前可用 `--dry-run` 预览）。
4. 人运行 `observe record` 把本次观察记进账本。

没有任何一步由 Runtime 触发，也没有任何一步影响生产阶段。

## 6.3 失败边界

- 写账本校验不过 -> 报错退出，不产生半条记录（校验在追加之前）。
- 报告文件读不出来 -> 报错退出，不写反馈。
- 账本里有坏行 -> `observe list` 报告坏行位置，其余有效行照常展示。

---

# 七、冻结边界（再次声明）

- **不改 Runtime**：本阶段不修改 `episode-state.json`、`story-gates.json`、
  `story_os.py`、Runtime DAG、Scheduler 或任何生产脚本。
- **不自动接入**：没有 hook、没有 import 到生产链、没有后台触发。
- **不阻断**：账本与反馈都在生产之外，失败也不影响生产。
- **无伪评分**：只记等级、计数、decision；不记相似度百分比或分值。
- **可删除**：删除 `reports/pre-production/` 只丢失经验历史，
  不丢失任何生产事实。

---

# 八、目录结构

```
pre_production/
  shadow_observation/
    __init__.py               导出账本与反馈 API
    ledger.py                 Episode Observation Ledger（append-only）
    feedback.py               Advisor Feedback（人工判断）
    README.md                 人工反馈入口说明
  contracts/
    observation_ledger_entry.schema.json
    advisor_feedback.schema.json
  tests/
    test_shadow_observation.py
```

---

# 九、EP003 观测示例

归档 EP003（`episodes/_archive/*EP003*`，雾中的另一座生活区）在 Shadow Mode 下：

```
decision              : WARNING
highest_risk_level    : MEDIUM/HIGH（以真实证据为准）
风险                  : mountain_environment / fog_anomaly / isolated_location
建议                  : 重新设计异常机制
```

记录进账本后，一行 `observation_ledger_entry` 即成为可回看的经验锚点；
人工写下反馈后，`feedback_id` 指向 `PFB-<report_id>`，
`advisor_accuracy` 用四个标签之一表达“这次 Advisor 说对了没有”。

---

# 十、验收标准

1. 能生成 `observation_ledger_entry` 且契约校验通过。
2. 同一 Story Lock 重复观察返回 `REUSED`，不重复追加。
3. Advisor Feedback 的 `judgement_source` 恒为 `human`。
4. 反馈/账本中不出现任何分数、百分比、星级键。
5. EP003 观测记录的 `decision` 为 `WARNING`，并带 similarity evidence。
6. 删除 `reports/pre-production/` 不影响任何生产事实与状态。

---

# 十一、演进（不在本阶段实施）

只有当人工反馈积累到一定量、且 Creator Decision 与 Advisor Accuracy 的关系被人工复核后，
才讨论进入 Phase 2 Advisor Mode。进入条件不在本文承诺内，也不由本层自动触发。

Shadow Observation 的长期价值：让 Advisor 的准不准**有据可查**，
而不是靠主观感觉宣称“Advisor 有用”。
