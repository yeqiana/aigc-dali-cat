# Shadow Observation（人工影子观察层）

Pre Production Advisor 的**人工观察层**。它在 Shadow Mode 之外，给作者两个可选的、
纯手动的动作：把一次 Advisor 观察记进账本，以及写下自己对 Advisor 的人工判断。

这一层是**加成**的：生产 Runtime 从不调用它，删除它也不会影响任何生产流程。
它只回答一个问题，而且必须由人来回答：

> 这个 Advisor 上一次到底说对了没有？

---

## 一、为什么需要它

Shadow Mode 已经能出报告，但报告本身不会告诉你 Advisor 准不准。
只有把「Advisor 说了什么」和「人后来怎么看」分开记下来，才能积累经验。

所以这一层只做两件事：

1. **Episode Observation Ledger**：客观记录每次 Shadow 观察的事实
   （哪一集、哪个 Story Lock 版本、decision、最高风险等级、建议）。
2. **Advisor Feedback**：记录人对这份报告的主观判断
   （采纳没采纳、准不准、哪条证据被证实/被推翻、漏了什么）。

账本是事实，反馈是判断。两者都不改报告、不改 Story Lock、不改状态。

---

## 二、冻结边界

- **不接入 Runtime**：没有生产流程调用这里；只有人手动运行 `observe` 命令。
- **不是权威**：账本每行都带 `authority: derived_non_authority`，
  永远不给 PASS，永远不替代 `meta/episode-state.json`、`meta/story-gates.json`。
- **不阻断生产**：写账本、写反馈都发生在生产之外；失败也不影响生产。
- **只有人能判断**：`judgement_source` 只能是 `human`，本阶段不接受自动判断。
- **无伪评分**：准确度只有 `correct / partially_correct / incorrect / unknown`
  四个人工标签，不出现分数、百分比、星级。
- **追加不改写**：账本是 append-only JSONL，修正就是新增一行，历史行永不修改。
- **可删除**：删除账本或反馈只会丢掉经验历史，不会碰任何生产事实。

---

## 三、数据流

```
Story Lock
   |
   v
Shadow Mode（run_shadow，只出报告）
   |
   v
observe record        -> Episode Observation Ledger  (reports/pre-production/observation-ledger.jsonl)
   |
   v
人看报告，写判断
   |
   v
observe feedback      -> Advisor Feedback          (reports/pre-production/advisor-feedback/PFB-<report_id>.json)
   |
   v
（可选）反馈里的 review_reference_id 指向 Memory Adapter 的经验记录
```

---

## 四、Episode Observation Ledger

一行一次观察，append-only JSONL，默认
`reports/pre-production/observation-ledger.jsonl`。

去重键是 `(run_mode, episode_id, story_lock_sha256)`：同一个 Story Lock 版本
重复观察只会返回 `REUSED`，不会重复追加。Story Lock 改了（SHA 变了）才算新观察。

关键字段：

| 字段 | 含义 |
| --- | --- |
| `observation_id` | `OB-<episode>-<sha8>`，稳定标识 |
| `run_mode` | 固定 `shadow` |
| `decision` | `PASS / WARNING / NEEDS_REVISION` |
| `confidence` | `LOW / MEDIUM / HIGH` |
| `highest_risk_level` | 本次最高的 risk 等级，`NONE` 表示没有风险 |
| `risk_count` / `evidence_count` | 真实计数，不是分数 |
| `recommendations` | 建议 token 列表 |
| `feedback_id` | 关联的人工反馈 id（还没写就是 `null`） |
| `authority` | 固定 `derived_non_authority` |

契约：`pre_production/contracts/observation_ledger_entry.schema.json`。

---

## 五、Advisor Feedback

一条反馈对应一份 Advisor 报告的一个精确版本，默认写在
`reports/pre-production/advisor-feedback/PFB-<report_id>.json`。

反馈会记录 `advisor_report_sha256`，所以它绑定的是**当时那一版报告**；
报告重新生成后，旧反馈不会被误当成本次判断。

字段：

| 字段 | 含义 |
| --- | --- |
| `judgement_source` | 固定 `human` |
| `creator_decision` | `pending / accepted / revised / ignored` |
| `advisor_accuracy` | `correct / partially_correct / incorrect / unknown` |
| `confirmed_evidence` | 被人证实的 `evidence_id` 列表 |
| `refuted_evidence` | 被人推翻的 `evidence_id` 列表 |
| `missed_risks` | Advisor 漏掉的自由文本条目 |
| `notes` | 人工备注 |

引用报告里不存在的 `evidence_id` 时，命令只给 warning，不拒绝、不阻断。
契约：`pre_production/contracts/advisor_feedback.schema.json`。

---

## 六、人工反馈入口

全部通过命令行，纯手动：

```powershell
# 1. 记录一次影子观察（只读分析 + 追加一行账本）
python -m pre_production observe record <episode_dir> [--ledger PATH] [--dry-run]

# 2. 写下人对某份报告的人工判断
python -m pre_production observe feedback --report <advisor_report.yaml> `
    --decision accepted --accuracy partially_correct `
    --confirmed SE-xxx --refuted SE-yyy --missed "漏掉了关系风险" --notes "先改机制"

# 3. 回看账本
python -m pre_production observe list [--episode 10-03] [--json]

# 校验产物契约
python -m pre_production validate <yaml> --kind feedback|observation
```

`--dry-run` 只打印将要写入的内容，不落盘。

---

## 七、测试

```powershell
python -m pytest pre_production/tests/test_shadow_observation.py -q
```

覆盖：账本追加/去重、反馈人工边界、未知证据 warning、契约合法性、无分数键，
以及「改了账本也不影响生产事实」这一条边界。

