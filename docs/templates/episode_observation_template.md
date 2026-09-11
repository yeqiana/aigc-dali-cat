# Episode Observation Template（每集复盘模板）

用途：EP004 – EP020 每集生产结束后，人工填写一份。填写规范见
`docs/Story_OS_PreProduction_Intelligence_EP004_EP020_Observation_Runbook_V1.0.md`。

复制本文件到 `reports/pre-production/observations/<episode_id>.md` 后填写。

约束：

- 只写事实与定性判断，不写百分比、不写换算等级、不写总分；
- 每条判断都要引用 `evidence_id` 或 `feedback_id`；
- 拿不准就写「样本不足」，不猜；
- 本模板不写入任何生产状态，也不修改 `meta/episode-state.json` 或 `meta/story-gates.json`。

---

## 0. 机器可读摘要

```yaml
episode_id: <例如 10-04>
advisor_result:
  decision: <PASS | WARNING | NEEDS_REVISION>
  confidence: <LOW | MEDIUM | HIGH>
  advisor_report_reference: <advisor_report:PPA-...>
risk_summary:
  - risk_type: <例如 similarity>
    risk_level: <LOW | MEDIUM | HIGH>
    matched_features: [<token>, <token>]
    evidence_id: <SIM-...>
    human_view: <认可 | 误报 | 样本不足>
creator_decision:
  creator_action: <ACCEPT | REVISE | IGNORE>
  recommendation_result: <USEFUL | PARTIAL | NOT_USEFUL>
  risk_acknowledged: <yes | no>
  feedback_reference: <PFB-...>
production_result:
  production_outcome: <自由文本；未生产则留空>
  audience_feedback: <可选；原始数据原样抄录，不做计算>
experience_status:
  experience_reference: <EXP-...>
  decision_experience_reference: <CDE-...>
  complete: <true | false>
  missing: [<缺哪个引用>]
learning_notes:
  conclusion: <证据支持 | 证据不足 | 样本不足>
  risk_pattern_tokens: [<token>, <token>]
  notes: <自由文本>
```

---

## 1. Advisor 是否发现问题？

- decision：
- risks（逐条：等级 + 摘要 + evidence_id）：
- recommendations（逐条）：
- 结论：

## 2. 风险是否真实？

| # | evidence_id | Advisor 的风险 | 人的判断（认可 / 误报 / 样本不足） | 理由 |
| --- | --- | --- | --- | --- |
| 1 | | | | |

- 漏报（Advisor 没提但人认为存在的风险）：

## 3. 建议是否采用？

| # | 建议 | creator_decision | recommendation_result | 说明 |
| --- | --- | --- | --- | --- |
| 1 | | | | |

## 4. 最终结果如何？

- 是否按建议改稿：是 / 否 / 部分
- 修改方向：
- 最终效果：
- 与 Advisor 判断的关系：

## 5. 哪些经验值得保存？

- Risk Pattern 形态（token 组合）：
- 值得长期保留的经验点：
- 备注：

---

## 附录：收尾检查

- [ ] 三份 YAML 已落盘并通过 `validate`
- [ ] 观察记录已在 `observe list` 中出现
- [ ] 反馈文件已写入 `reports/pre-production/advisor-feedback/`
- [ ] `experience list --episode <episode_id>` 能查到本集
- [ ] `experience stats` 中本集 complete / incomplete 状态已确认
- [ ] 本模板已填写完毕

