# Phase5A 固定 Canary：历史生图成功不等于 Final Semantic 验收（2026-10-09）

## 背景与只读证据

- 既有全局 Claim：`native-image-proof-20261008`；必须恢复该固定身份，禁止重新分配、重置或覆盖历史 Attempt。
- 独立 TEST_ONLY：`127.0.0.1:3306/STORY_OS_RUNTIME`，与正式 `3307/STORY_OS_RUNTIME` 严格隔离。使用临时、最小权限的只读/准备专用账号验证，账号在调用完成后删除；不复制正式数据库的凭据。
- 正规 `phase5a_initial_canary_input.prepare()` 返回 `INITIAL_CANARY_ATTEMPT_NOT_FRESH`。这是正确阻断：经 `logical_asset_identity` 计算后，该固定资产在 V2 Authority 的准确身份为 `_external/762890e73501c583/frame-01`，**Attempt 1 已为 `SUCCEEDED`，剩余 1 次，不应再次执行首次准备**。
- 原生候选记录：Provider `codex_subscription`、执行器 `codex_user_runner`、图片模型 `gpt-image-2.5-flare` / `high`；存在正式结果引用、真实 RAW（2,325,654 字节），队列 `generated` 的 output 文件也真实存在（2,024,972 字节），Fast Scout 已 `finalized`。
- **证据边界**：历史 worker JSONL 仅有一条 `agent_message`、`turn.completed` 等过程事件；**未观察到可确认的 `image_generation` 工具调用事件**。不能因为 Provider 字段、RAW 或 Attempt `SUCCEEDED` 就推断具备正式可用的原生 image tool 能力，也不可冒充 Phase5A Capability PASS。
- 确切下一阻断：同一 generation_key 的 `FINAL_SEMANTIC` Review 为 `blocked`，失败代码 `FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`，没有 Review receipt，历史 critic JSONL 为 **0 字节**。日志为空也不能证明模型从未执行。

## 本次修复

- 既有 `phase5a_collaborative_canary._preflight()` 在验证单帧 Generated Attempt 与身份一致后，检查对应 `FINAL_SEMANTIC` Review。若审核 `blocked` 且没有可靠终态，返回 `CANARY_FINAL_SEMANTIC_EXECUTION_UNVERIFIED`，禁止继续将其宣告为 `READY`。
- 其他被阻断的 Final Semantic 返回 `CANARY_FINAL_SEMANTIC_BLOCKED_REQUIRES_RECOVERY`。非当前 generation_key 的 Review、已终结审核、以及获官方 Review Authority 允许重新排队的状态仍可按原合同处理。
- **没有修改** `generation_attempt_authority`、`review_queue` 的权威状态、模型路由、任何图片、审查记录或预算。不能通过直接改 JSON / MySQL 清除阻断。
- 新增 6 项安全测试，涵盖不可重复执行、已经 finalized 的合法通过和其它 generation_key 的隔离。隔离分支定向四组测试 `12+13+14+40=79 passed`。
- 原始文件已在主工作区备份，然后局部同步修改；主工作区该补丁后定向 `12+15=27 passed`，`git diff --check` 通过。
- 使用独立临时 TEST_ONLY 只读账号，真实重跑 canonical `run_production_subpath(..., dry_run=True)` 后返回：`CANARY_FINAL_SEMANTIC_EXECUTION_UNVERIFIED`。测试账号按流程清理；没有新 provider call、没有新增 Attempt 或正式图片。

## 正确恢复路径

1. **优先只读**查找历史 Final Semantic 运行期的持久化 request_id、Runner 原始结果、受信的 `vision.final` 模型执行回执。单独的 `turn.completed` 或空文件都不能批准重派。
2. 如果确有带身份、artifact SHA 和模型策略的一致终态回执，走 Review Authority 的原生恢复/核销流程，不能伪造 `PASS`。
3. 如仍无法证明，保持 `blocked`、保持固定 Canary 的 Attempt 1 `SUCCEEDED`，不要擅自把剩余图片 Attempt 消费掉。另拟经审核批准的独立测试策略才能进一步证明原生图片工具，不能提升这条历史记录为正式 Capability PASS。
4. 生产 Episode《五十亩山地之后》的 Frame06/24 仍是历史 `OUTCOME_UNKNOWN`；和 TEST_ONLY Canary 的 `SUCCEEDED` 完全隔离。正式图片仍是 2/25。
5. StoryOS 永远是图文生产系统，只用原生 Codex，不恢复 OpenCodex，也不引入视频生成。
