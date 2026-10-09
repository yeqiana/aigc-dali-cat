# StoryOS 原生 Codex 直连 Review 持久化与外部 Lease 安全闭环（2026-10-09）

## 前置状态

集成基线 `dbb1004` 已为每次新的 Final Semantic 在 Review Queue claim 的事务内预分配 32-hex `runner_request_id`，并通过 `frame_semantic_review -> codex_critic_runner -> codex_user_runner` 传递到原生 Codex。正式主工作区此前已局部同步此修复。

本轮检查发现旧实现只在 **user_runner bridge** 模式持久化原生 Runner task-results：`codex_user_runner.run_codex()` 在 **direct** 模式完全忽略传入的 `request_id`，故 `_finalize_final_semantic_receipt()` 检查 Runner task result 时无法通过。若继续直连派发，可能形成新的无法核实的 Final Semantic UNKNOWN。

## 改动

1. **原生 Codex direct 结果持久化**：在有 `request_id` 的直接执行入口前，校验该 ID 符合 Runner ID 格式且未有结果；必须提供可复核的日志文件句柄或 PIPE，否则在调用模型前拒绝。Codex 完成后取回 **准确的合并日志字节**，以和 bridge 相同的 `schema_version/request_id/returncode/output_sha256/output_bytes/output_base64/evidence` 格式持久化，确保 `_finalize_final_semantic_receipt` 能找到同 ID 的结果。写结果使用 exclusive create、flush、fsync，防止覆盖以前调用的回执，且保留异常与非 0 的真实返回码；模型的正常退出或 `turn.completed` 仍非 Final Semantic PASS。
2. **重复调用隔离**：同一 direct ID 若已存在结果文件，必须在模型启动前拒绝，不能覆盖旧回执或重复扣费。
3. **调度器安全退出**：停止标志已设置、没有本地活跃任务、没有可认领的 queued Review 时，即使外部 worker 还持有合法 Review lease，调度器也能正常退出，绝不抢走外部 claim。
4. **遗留假回执隔离**：此前仅有 `{"status":"SUCCESS"}` 的简化旧测试被误当成合法完成证明。现要求 Final Semantic terminal receipt 的 Episode、Asset、Generation、Attempt、图片 SHA、model role、profile、model policy 全部匹配；任何不完整遗留回执在再次派发前隔离，不自动建新的 Runner ID。

## 四槽位真实回归

| 槽位 | 范围 | 结果 |
|---|---|---|
| A | direct 持久化、重复 ID、不可观察 stdout、非零退出、预分配 ID | 9 passed |
| B | 外部 lease 退出、过期 claim、完整/不完整回执 | 12 passed |
| C | Codex Runner direct/bridge 兼容、Final Semantic queue | 83 passed、2 subtests |
| D | 固定 Canary 前置门禁、Review 证据、原生生图限制 | 21 passed |
| **合计** | | **125 passed、2 subtests** |

这些为真实运行的 pytest，模拟模型进程以避免新的 Provider 调用。并未证明旧 Canary Final Semantic 的历史调用可恢复，因为其历史 critic JSONL 0 字节、没有预分配 `runner_request_id` 或正式模型回执，必须继续 `blocked`。

## 正式生产不可突破的边界

- 正式 Episode《五十亩山地之后》最新可用图片 2/25，Frame06 和 24 历史 Provider 为旧 `opencodex`、MySQL Authority 均为 `OUTCOME_UNKNOWN`，严禁重复派发；本轮不更新正式数据库。
- TEST_ONLY Phase5A 固定 Canary Frame01 仍保留既有图片，但 Final Semantic 未验收，不假报 PASS，也不再触发模型。
- StoryOS 图文生产，只走原生 Codex，禁止 OpenCodex 代理及视频生成。
- 集成分支保护 `config/agent_runtime/codex-subscription-batch.json`、`episodes/_system/effective_config.py`、`unused/meta/episode-performance-ledger.json` 三处先存 dirty；仅本轮五个文件与本文纳入独立提交。
- 主工作区可能另有用户/并发修改，只允许有备份和精确锚点的局部集成，不得 reset/clean/rebase。
