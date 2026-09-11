# Story OS Pre Production Intelligence (MVP)

Story Lock 之后的**只读辅助层**。它在正式生产开始前把故事结构化、和历史篇目做结构对比，
输出一份带证据的建议报告，帮助作者在写画面之前发现选题重复风险。

它可以被整体删除而不影响任何生产流程。

---

## 一、链路

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
Evidence
   |
   v
Advisor Report            -> advisor_report.yaml
   |
   v
Memory Adapter            -> Review Reference（经验沉淀）
   |
   v
Shadow Mode               -> 只出报告，继续原生产流程
   |
   v
Shadow Observation        -> 观察记录 + 人工反馈（可选，不接 Runtime）
```

入口：`pre_production/shadow_mode.py` 的 `run_shadow()`（永不抛异常、永不影响生产）；
Shadow Observation 入口：`pre_production/observation/observation.py` 的 `run_observation()`（同样永不抛异常）。

---

## 二、冻结边界（MVP 不做的事）

- 不修改 `meta/episode-state.json` 状态机，不新增第二状态机。
- 不修改 `meta/story-gates.json` 的权威职责。
- 不实现 Production Gate，不阻断、不替代 Runtime。
- 不自动修改 Story Lock。
- 不输出相似度百分比，不输出 87/92 这类伪精确分数；风险只有 `LOW / MEDIUM / HIGH`，且必须附证据。
- Story DNA 只做结构化，不判断好坏。
- Shadow Observation 只做记录；任何失败都返回 `blocks_production=false`，Advisor 始终 Advisory Only。

Advisor Report 的 `boundaries` 字段会把这些边界显式写进产物。

---

## 三、目录

```
pre_production/
  story_dna/            Story Lock -> 结构化 DNA（lexicon 驱动，无评分）
    extractor.py        Story Lock 发现 / 解析 / 逐 token 证据
    schema.py           契约读取与 token 工具（contracts JSON 是唯一来源）
    lexicon.py          关键词 -> token 数据表（RULE_VERSION）
    validator.py        Story DNA / Similarity / Advisor / Review 契约校验
  similarity_analysis/  与历史 DNA 对比，产出 Similarity Evidence
    retrieval.py        从真实 Story Lock 读取历史样本（保留路径与 SHA）
    analyzer.py         维度命中 + 风险分级规则
    evidence.py         Evidence 构造 / 排序 / 计数
  advisor/              证据 -> 风险 -> 建议 -> 报告
    risk_assessor.py    只有 MEDIUM/HIGH 才成为风险，并保留证据
    recommendation.py   风险 -> 非约束性建议
    report_generator.py decision / confidence / boundaries
  memory_adapter/       只做接口：读历史经验、写 Review Reference
  observation/          Shadow Observation（观察记录 + 账本 + 人工反馈，不接 Runtime）
    schema.py           Episode Observation Record / Advisor Feedback 契约
    ledger.py           Episode Observation Ledger（append-only JSONL，生命周期）
    feedback.py         Advisor Feedback Model（人工判断，非评分）
    observation.py      Shadow Observation Runner（永不抛异常）
    tests/              Observation / Feedback / 人工入口 / Runner / EP003 回归
  contracts/            六份 JSON 契约（唯一契约来源）
  tests/                unit / contract / EP003 回归 / Shadow Mode
```

产物默认写到 `<episode>/meta/pre-production/`：`story_fingerprint.yaml`、
`similarity_report.yaml`、`advisor_report.yaml`。
Review Reference 写到 `reports/pre-production/review-references/`；
Observation Ledger 写到 `reports/pre-production/observation-ledger.jsonl`；
Advisor Feedback 写到 `reports/pre-production/advisor-feedback/`。

---

## 四、命令行

```powershell
# 只读分析，打印结论
python -m pre_production analyze <episode_dir>

# 只读分析并落盘三份 artifact
python -m pre_production analyze <episode_dir> --out-dir <dir>

# Shadow Mode（永不抛异常，永不阻断生产）
python -m pre_production shadow <episode_dir> [--dry-run] [--no-memory]

# 校验任意 artifact
python -m pre_production validate <yaml> --kind dna|similarity|advisor|review|feedback|observation

# Shadow Observation（人工影子观察层，纯手动，永不阻断生产）
python -m pre_production observe record [episode_dir] [--report <advisor_report.yaml>] [--ledger PATH] [--dry-run]
python -m pre_production observe feedback --report <advisor_report.yaml> --creator-decision ACCEPT|REVISE|IGNORE --recommendation-result USEFUL|PARTIAL|NOT_USEFUL --risk-acknowledged yes|no [--revision-direction TEXT] [--final-effect TEXT] [--notes TEXT] [--dry-run]
python -m pre_production observe list [--ledger PATH] [--episode ID] [--json]
```

常用参数：`--history <episode_dir|story_lock.md>`（补充历史样本）、`--limit N`、`--repo-root`。

---

## 五、风险分级规则（冻结）

| 命中维度 | 等级 |
| --- | --- |
| anomaly + (setting 或 visual_pattern) | HIGH |
| 只有 anomaly | MEDIUM |
| setting + visual_pattern + (relationship 或 character) | MEDIUM |
| 其他命中 | LOW |
| 无命中 | 不产出 evidence |

账号级通用 token（如 `first_person_handheld_capture`）已从对比中排除，避免把整个账号的底色当成重复。

Advisor decision：

- `NEEDS_REVISION`：存在 HIGH，且 Story Lock 本身未声明差异化证据。
- `WARNING`：存在 MEDIUM/HIGH。
- `PASS`：其余情况。

---

## 六、EP003 验收

输入归档 EP003（`episodes/_archive/*EP003*`，雾中的另一座生活区）：

- 预期 `decision: WARNING`
- 必须存在 similarity evidence，且每条都能指回真实历史 Story Lock
- 不得出现任何分数/百分比字段

对应测试：`pre_production/tests/test_ep003_regression.py`（归档缺失时 skip，不伪造结论）。

---

## 七、Shadow Observation（人工影子观察层）

Shadow Mode 之后的**可选人工动作**：把每次 Advisor 运行记进账本，并写下人对这次运行的判断。
生产 Runtime 从不调用它；删除它只会丢经验历史，不动任何生产事实。
Advisor 始终是 **Advisory Only**，所有失败都返回 `blocks_production=false`。

```
Advisor Report -> observe record -> Episode Observation Ledger -> 人工反馈 -> observe feedback -> 更新 Observation

OBSERVED -> FEEDBACK_PENDING -> COMPLETED
```

- **Observation（`observation/observation.py`）**：`run_observation()` 记录一次 Advisor 运行，
  永不抛异常；失败也返回 `ok=false` 且 `blocks_production=false`。重复运行幂等且只前向推进。
- **Episode Observation Ledger（`observation/ledger.py`）**：append-only JSONL，默认
  `reports/pre-production/observation-ledger.jsonl`。每行一个完整快照，同一 `observation_id` 取最新一行为准；
  状态只前向推进，修正就是新增一行。字段：`episode_id / story_dna_reference / advisor_report_reference /
  observation_status / creator_feedback_reference / production_outcome / learning_summary`，
  并固定 `authority: derived_non_authority`。
- **Advisor Feedback（`observation/feedback.py`）**：默认
  `reports/pre-production/advisor-feedback/PFB-<report_id>.json`。`judgement_source` 恒为 `human`；
  `creator_decision` 为 `ACCEPT / REVISE / IGNORE`；`recommendation_result` 为 `USEFUL / PARTIAL / NOT_USEFUL`；
  另外记录 `risk_acknowledged`、`revision_direction`、`final_effect`、`notes`。
- **契约**：`contracts/episode_observation.schema.json`、`contracts/advisor_feedback_model.schema.json`，
  由 `observation/schema.py` 校验。

边界：Feedback 不修改 Advisor、不修改 Story Lock、不变成硬规则、不引入评分；
它只是后续 Experience Store 的数据入口。反馈与账本都在生产之外，失败也不影响生产。

---

## 八、测试

```powershell
python -m pytest pre_production/tests pre_production/observation/tests -q
```

覆盖：Story DNA 单元测试、Schema Validator 契约测试、Similarity Evidence 测试、
Advisor Report 契约测试、EP003 回归、Shadow Mode 非阻断性，以及 Shadow Observation
（Observation Ledger Schema、Feedback Contract、人工反馈入口、Runner 生命周期、EP003 观察回归）。

