# StoryOS Phase5A 最初 Canary 旧审核的受审验证纪元替代路径（2026-10-09）

## 真实阻断

固定根 Claim `native-image-proof-20261008` 的 V2 Attempt 1 已为 `SUCCEEDED`，图片文件存在，`FAST_SCOUT` 已终结；`FINAL_SEMANTIC` 则为 `blocked / FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`，历史 Critic 日志 0 字节，无 Runner ID、无 Final Semantic 模型回执。已有的 `image.controller` 回执不能冒充 `vision.final`。

代码原本仅支持后续 `phase5a-validation-eN` 退休，根 Claim 没有历代纪元文件，导致旧 Canary 事实上无法退休/替换。另外，安全恢复已经把未知 Final Semantic 标为 `blocked`，但退休校验不认识这个安全状态，反而将其视为未知错误。这两道不相容门禁造成测试系统无法重新完成原生 Capability 验证。

## 本次修复

- `_retirement_source_claim`：首个全局固定 Claim 严格映射为原生纪元 1，前提是唯一来源为真正的全局 Claim、工作区路径与身份精确一致、无已有 replacement 与后续纪元。任何最新纪元不同、来源不存在或替换已占位均失败关闭。
- `_assert_review_queue_not_recoverable`：仅承认已隔离、类型 `FINAL_SEMANTIC`、错误码 `FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`、恢复动作 `VERIFY_FINAL_SEMANTIC_EXECUTION_BEFORE_RETRY`、没有任何 Runner Request ID 或 Review Receipt 的旧记录为下一步候选。排队中的 Review、仍活跃的 Lease、Runner ID、已存在结果均禁止退休。
- `_retirement_evidence`：继续核验 TEST_ONLY/NON_PROMOTABLE、没有 Episode Stage 或 Release Authority、独立 MySQL V2 Attempt 1 `SUCCEEDED` 且已用 1/2/无 Active Attempt、没有正式 Review Receipt、诊断报告证明投影不可验证、无 Critic `turn.completed`；**额外检查任何 `vision.final` 模型执行回执，存在即禁止退休**。
- `retire_validation_epoch`：允许从官方严格验证的原始纪元 1 生成幂等、不可变的退休记录与单一预留的 `phase5a-validation-e2-*` 身份；原始图片、Attempt 消耗、回执和 MySQL 数据完全不变。
- `claim_global_canary`：为退休后的根纪元提供**显式 `allow_validation_epoch=True`** 的官方继任入口；后续纪元也可在无 replacement 文件时以同样 append-only 规则继续。拒绝把它当作免费的第二次原图 Attempt。

## 四槽位回归

- 根 Claim 身份和唯一来源、过时纪元拒绝
- blocked 的身份证据严格验证、Runner ID 或 Review Receipt 禁止退休
- 原始根纪元预算保留、退休幂等、继任纪元必须显式授权
- 真实模型执行回执或完整 Critic 运行记录阻断退休
- 现有 epoch 退休/重试/原生 Codex 相关合同

测试分组：15 + 17 + 17 + 17 = **66 passed**。前一轮新增根纪元合同测试等合计 68 项也通过。

## 真实 TEST_ONLY 执行记录（2026-10-09）

- 通过正式 `frame_semantic_review.reconcile_review_projection(write_report=True)` 生成根 Canary 的 `meta/review-projection-reconciliation.json`，分类为 `UNVERIFIED_REVIEW_PROJECTION`。证据明确包括 `Final Semantic Model Execution Receipt missing`、`Review Queue terminal SUCCESS receipt missing` 与 `frame review record missing`，**绝不当作 PASS**。
- 独立测试容器 `127.0.0.1:3306/STORY_OS_RUNTIME` 官方 `_retirement_evidence` 实测 `ELIGIBLE`，原始 Attempt 消耗 1、剩余 1、Review UNKNOWN 一条，执行 0 个模型调用；临时 DB 账号已清理。
- 官方 `retire_validation_epoch` **真实执行成功**：原始 `native-image-proof-20261008` 为 `validation_epoch=1`、`retired=true`、`retirement_reason=REVIEW_EXECUTION_RECEIPT_UNRECOVERABLE`，`generation_dispatch_eligible=false`，`review_dispatch_eligible=false`。旧 Attempt 状态、文件、模型执行证据和正式 Episode 均不改动。
- 从唯一预留身份 `phase5a-validation-e2-b675f7bc66b6` 创建新 TEST_ONLY 工作区，调用官方 `claim_global_canary(...,allow_validation_epoch=True)`，返回 `validation_epoch=2`、`resumed=false`。新身份与原始根 Claim、退休文件及 append-only 纪元声明形成唯一继任链。
- 官方 `phase5a_validation_input.prepare()` **真实执行返回 `READY`**；Frame01 状态 `queued`、新资产 `attempts_consumed=0`、`remaining_attempts=2`，`provider_calls=0`、`model_calls=0`、`stage_authority=false`。准备包括测试 Fixture、Frame Contract、Prompt Package 和 Production Queue，不代表实际 image tool capability 已证明。
- 主工作区根纪元变更通过精确 Git patch 同步，原文件已校验备份；新增测试文件使用不覆盖模式复制，主工作区 22 条相关新测试通过。随后额外一个 Canary dry-run 测试调用遭平台安全检查阻止，**未执行且不计入通过**；不得绕过安全检查，也不得借此触发图片生成。
- 正式《五十亩山地之后》的 `next_action` 仍为 `VERIFY_TECHNICAL_GENERATION_EVIDENCE`，Frame06/24 的两个旧 `OUTCOME_UNKNOWN` 保留，不进行自动重试。Runtime `HEALTHY`，OpenCodex 计划任务 `Disabled`。

## 运行边界

这是 TEST_ONLY 的独立验证纪元替代途径，不是正式 Episode 的 Frame06/24 旧 `OUTCOME_UNKNOWN` 重试许可。不得直接修改 MySQL Attempt 终态，不得以废弃验证纪元冒充 Capability PASS；若真实退休条件不全，不能推进继任。
StoryOS 保持纯图文、只用原生 Codex；OpenCodex 代理继续禁用，不引入视频。
