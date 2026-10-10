# StoryOS PREIMAGE 900 秒超时证据与执行预算

本轮只审计已有本地回执及源代码，不运行模型/生图/数据库写入。

## 已观察事实

《五十亩山地之后》的已有本地回执显示 PREIMAGE_CHARACTER_FINALIZE、PREIMAGE_ENVIRONMENT、PREIMAGE_WORLD 各出现一条 TIMEOUT，分别约 900.140、900.235、900.157 秒。

代码 `preimage_task_contract.py` 中 `execution_budget.timeout_seconds=900`，对应 World Prepare 与 Character Finalize 的模型 Producer 默认 `timeout_seconds=900`。此时间匹配**强烈提示被执行预算截断的可能性**，但不能据此断言远端模型没有产出、模型质量差、任务是失败可自动重试，更不能将图片 Attempt UNKNOWN 当作失败。

## 已有只读手段

- `python scripts/storyos_model_receipt_triage.py <episode_dir>`：只输出失败状态与是否存在分类。
- `python scripts/storyos_perf_evidence_snapshot.py <episode_dir>`：按模型角色与回执结局分别统计 P50/P95，避免将超时样本与成功样本混成一组。

## 下一步应取得的证据

1. 用现有 Runner 耐久任务 ID/Receipt 与时间戳核对三次 PREIMAGE 调用的用户侧实际完成状态、是否曾持久留存 Candidate。
2. 核对相应 PREIMAGE 的冻结 Capsule SHA 与最终 JSON evidence；若已完成则不重复付费调用。
3. 仅在严格确认旧 Attempt/Task 的 authority 状态和输出边界后，评审提高预算、缩小上下文或 Resume。
4. 不建议简单从 900 秒统一延长到 1800 秒：那可能只是让超时成本翻倍。

**目前这是证据关联，不是已证明的根因。**
