# StoryOS Final Semantic 派发前持久化 Runner ID 与中断后证据核销（2026-10-09）

## 问题证据

固定 Phase5A Canary `native-image-proof-20261008` 的图片 Frame01 已在独立 3306 V2 Authority 中记录一次 `SUCCEEDED`，队列为 `generated`，Fast Scout 为 `finalized`，但 Final Semantic 阶段历史记录为 `blocked / FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`。历史 `REVIEW_STARTED` Trace 存在，但没有可恢复的 `runner_request_id`，Critic JSONL 文件 0 字节，正式 Final Semantic 回执缺失。**无法据此得出 Critic 没有执行过的结论**。

现有 `review_queue` 只在模型调用结束后取得 `codex_user_runner` 返回的 Runner request_id；只保留 lease 身份不能从 Runner 查询原始执行结果。这是本轮修复的因果点。

## 新实现（仅对未来调用生效）

1. `review_queue.claim()` 在持久化 `running` claim 的同一 Queue Transaction 中预分配 32 位十六进制 `runner_request_id`，并记录 `review_dispatch_intent_at`；仅适用于 `FINAL_SEMANTIC`。`_claim_next_lane_item()` 在返回给模型执行器之前保存 Queue；不增加任何图片 Attempt。
2. `review_queue._final_semantic_receipt()` 沿既有 `review_item` 参数，传给 `frame_semantic_review.run_critic()`；该函数将 ID 加入 `model_execution_context`。
3. `codex_critic_runner.launch()` 在真实 `codex_user_runner.run_codex` 前校验 ID，并将相同 ID 作为 `request_id` 传入。模型执行回执 `call_id` 与该预分配 ID 一致，方便单一身份核对。未通过 Review Authority 绑定、artifact SHA、原生 durable Runner 结果和终态回执验证时，绝不能批准 Final Semantic。
4. 如果模型或审核提交抛异常、结果未知，则保持队列 `blocked`、无伪造 `TECH_FAILED` 终态回执，留存预分配 ID 与异常类别。不重复派发。如果一个曾被分配 ID 的 Review 错误地重新排入 `queued`，只有已有合法终态回执可被采用；否则自动隔离，而不是消耗第二次调用。
5. 原生工具 `scripts/storyos_review_execution_evidence_audit.py` 只读列出 Final Semantic 的稳定 Runner ID、原生持久化结果是否存在、是否观察到 `turn.completed` 和允许的下一步调查方向。即使有终态 Runner 结果，也只能显示 `RUNNER_TERMINAL_CANDIDATE_REQUIRE_OFFICIAL_RECONCILIATION`，**绝不修改 Review Authority、自动重新调用、声称审核 PASS**。只支持正式 Episode 根目录或固定 TEST_ONLY 工作区根目录的子路径。

## 验证及不可越过的边界

- 新增单元测试：持久化前 ID 分配、重复认领隔离、Fast Scout 不受影响、模型异常无伪造完成回执、Runner 对同一 ID 的传递，以及只读恢复工具的身份/终态/边界检查。
- 四槽位相关回归：15 + 14 + 86 + 19 = **134 passed**，额外 4 个子测试通过；另有 25 项扩展回归通过。
- 新工具不能解决旧 Canary 本身：历史调用发生时没有预分配 ID，不能“补造”当时的执行身份。旧 Final Semantic 仍是 `FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`，必须先按人工可核实的独立证据走 Review Authority 合规核销，不得再次派发来伪装恢复。
- 正式《五十亩山地之后》Frame06/24 的 `OUTCOME_UNKNOWN` 绝不修改；其图片预算与 TEST_ONLY Review 的推理调用是两个独立权限。正式图仍为 2/25。
- `StoryOSRuntime` 保持健康；数据库为 Docker MySQL 8.0 正式 3307 V2；`StoryOS-OpenCodex-Proxy` 保持 Disabled。绝不恢复 OpenCodex 代理，不涉及视频生成。
- 隔离集成分支提交后再用精确小补丁同步主工作区。主工作区其他未提交修改和图片资产不被覆盖。

## 后续准入

对于新的 Final Semantic 调用，先查 Queue 中的 `runner_request_id`，只读检查对应的 Runner 持久化任务与官方 `model_execution_receipt`、candidate / commit manifest / artifact SHA / model policy；如证据不全保持 `blocked`。任何候选终态都不是自动审核通过许可证。
