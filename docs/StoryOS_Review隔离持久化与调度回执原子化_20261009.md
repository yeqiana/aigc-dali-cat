# StoryOS Review 隔离持久化、Scheduler 终态与原生 Codex 原子回执（2026-10-09）

## 已定位的真实问题

1. **隔离写丢失**：`review_queue.claim()` 可能将旧 `FINAL_SEMANTIC` 回执不可信的 queued 行改成 blocked，并返回 `None`。旧 `_claim_next_lane_item()` 只有成功认领 row 才保存队列。导致 blocked 只存在于内存，重启后还在 queued，stop lane 可能无限等。
2. **调度器虚假成功**：`image_scheduler._scheduler_terminal_rc()` 对生成完成分支只看图片条目的失败标志，忽略 Final Semantic Review 中的 blocked/running/queued；可能把生成成功但审核未闭环报告为返回码 0。
3. **直连结果半文件**：`codex_user_runner._persist_direct_result()` 使用最终文件名 `open("x")` 直接写 JSON。进程在写入后、fsync 前崩溃可能留下不完整文件，被以后读取当作不可信的既有证据，进一步阻断恢复。

## 具体修复

- `_claim_and_persist_under_lock` 在已有队列事务内对认领前后关键字段做指纹比对；**无新 claim 但发生隔离**时也必须保存 Queue。适用普通 Episode 和锁定 Phase5A epoch 的 Claim 入口。
- 完成图片后统一检查 Review Queue：被阻断的 Final Semantic 返回 22；仍在执行返回 24；仍待认领返回 20；只有图片与 Review 都没有未完成条目才可在相应路径返回 0。
- 原生 direct 的 Runner 结果在同一目录先使用临时文件完整写入并 fsync，然后通过 `os.link(tmp, final)` 进行**原子、不覆盖**发布；删除临时文件。如果无法完成原子发布，保留失败而不是伪造回执。旧结果不可被覆盖；保持完整 request_id/sha256/returncode/output_base64 格式。
- 这一补丁**不会**对已使用的图片 Attempt 退款、重新派发图片或重写 Final Semantic Review Authority。

## 四槽位验证

| 槽位 | 范围 | 结果 |
|---|---|---|
| A | 隔离状态必须落盘、重启不会重复领取、可观察 lease | 13 passed |
| B | generated 图片下 Review blocked/running/queued 不会返回 0 | 8 passed |
| C | direct 原子回执、写入失败无半文件、旧 ID 不被覆盖 | 38 passed |
| D | Phase5A/Final Semantic 合同、原生 Codex 限制 | 21 passed |
| **合计** | | **80 passed** |

全程 pytest 使用模拟 Provider，不执行正式模型调用。本次不会把旧 Canary 的历史无 ID 中断审核错误宣告 PASS。

## 正式环境边界

- 只用原生 Codex；旧 OpenCodex 代理保持 Disabled；StoryOS 为纯图文，不引入视频。
- 正式 MySQL 8.0 的 Generation Attempt Authority 保持不变。《五十亩山地之后》Frame 06、24 仍为 `OUTCOME_UNKNOWN`，不允许未经原始回执核销就二次调用。
- 固定 TEST_ONLY Phase5A Canary 已有真实图片，但历史 Final Semantic 缺少可信 Runner ID 和最终审核回执；状态必须继续 blocked。
- 安全集成分支已有三个其它并发 dirty 文件，本轮提交只含自有修改；主工作区大量 dirty 文件只能备份后精确同步，禁止覆盖或重置。
