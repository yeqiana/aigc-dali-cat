# StoryOS 隔离分支安全集成与 TEST_ONLY 审核恢复记录（2026-10-09）

> 范围：只记录真实发生的操作与证据。测试环境不是正式生产，不能据此授予《五十亩山地之后》的 Review Authority、M00 或 PUBLISH_READY。

## 1. 安全集成事实

- 正式主工作树 `story-platform-v3-rever` 仍有并发未提交修改，基线 `ea6f917`。
- 既有隔离分支 `storyos-native-image-repair-20261008` 的首轮修复提交是 `a5e5ea9`，含 32 个文件。
- 主工作区有 8 个与隔离分支内容不同、且同时有本地修改的文件；在各自版本与 HEAD 的三方合并模拟中：
  - **能自动合并（2）**：`episodes/_system/image_scheduler.py`、`episodes/_system/image_worker_pool.py`。
  - **出现实际冲突（6）**：`episodes/_system/codex_subscription_image.py`、`episodes/_system/codex_user_runner.py`、`episodes/_system/effective_config.py`、`episodes/_system/image_payload_transport.py`、`tests/system/test_codex_user_runner.py`、`tests/system/test_login_auth_payload_transport.py`。
- 自动合并仅表示文本三方合并没有冲突，**不是语义或生产验收**。不得直接 cherry-pick 覆盖主工作树的脏文件；必须在独立集成工作树逐项并入并复测。
- 禁止 reset/clean/rebase、覆盖正式 runtime.env、输出数据库凭据、写假 PASS；不启用 OpenCodex 代理，也不引入视频生成。

## 2. TEST_ONLY Phase5A 单帧恢复（只核实真实事件）

- Docker 引擎恢复后，**仅启动**此前存在的测试容器 `storyos-phase5a-mysql`，映射 `127.0.0.1:3306`，没有改动正式数据库。
- 从真实队列读取到：Frame01 图片 `generated`，Fast Scout `finalized`，Final Semantic `running` 且租约于 2026-10-08 过期。
- 证据检查：`frame-semantic-critic-attempt-1.jsonl` 0 字节，无 `vision.final` execution receipt，无正式 review-commit；只有 candidate/pending，并不能当作最终 PASS。
- 在无相关审核进程、测试标记存在、review_key 精确匹配、租约过期且原图片状态为 `generated` 的前提下，原子调用 `recover_claims()`，将**该 TEST_ONLY 审核**从 `running` 隔离为 `blocked`。
- 写入后数据库回读确认：review_key 未变，Fast Scout 仍 `finalized`，Frame01 仍 `generated`；故障码 `FINAL_SEMANTIC_UNVERIFIED_INTERRUPTED_CALL`。
- **没有重新派发模型，没有再次生图，也没有授予审核通过**。后续如恢复 Final Semantic 必须先核对历史模型执行证据及授权，不能以 candidate 自行补 PASS。

## 3. 本轮新的代码保护

- `next_action.py` 新增隔离 Final Semantic 的只读恢复投影，若无可运行图片，返回 `VERIFY_FINAL_SEMANTIC_EXECUTION_BEFORE_RETRY`、`hard_stop=true` 和 `auto_recoverable=false`，不生成新图片。
- 新增 `test_next_action_final_semantic_blocked.py`：覆盖异常审核标识、历史审核忽略、去重与 `derive()` 业务出口。
- `test_local_sqlite_checkpoint_probe.py` 添加 8 并发 CAS 同 revision 竞争测试，确认只有一个胜出，修订号仅前进一次；SQLite 仍是独立试验库，没有生产切换。
- 2026-10-09 本轮四槽位验证：A 38、B 8、C 65、D 30，共 **141 pytest passed**（不同测试文件）；下一次补充测试通过 12 项（与这 141 项有重叠，不能相加）。
- 之前的扩大回归 229 passed + 4 subtests 属于前一轮提交，不把它和本轮重叠测试累计。

## 4. 未结项（按优先级）

1. 在隔离的集成工作树逐一解决 6 处文本冲突，保留主工作区并发修改，重新执行相关回归。
2. 校验正式 Episode 自身的 PREIMAGE / image route / M00 授权与原生工具可用性；TEST_ONLY 结果不得作为正式像素和审核权威。
3. Final Semantic 的独立回执缺失仍需真实诊断；禁止盲目重复模型执行。
4. SQLite 只做 LOCAL 评估，完成 MySQL/Redis/文件 Authority 对账与可回滚迁移后才可切换。
## 5. 安全集成试验与原生路由红绿回归（2026-10-09）

- 创建独立集成工作树 `storyos-main-integration-20261009`，基线 `b31b1c7`，原始主工作树未修改。
- 对 8 个重叠文件执行三方文本合并；6 个冲突区优先选中已经验证的 native-only 逻辑，2 个文件文本自动合并。
- 合并后差异复审发现：原主工作区非冲突代码仍将 `opencodex` 引回 `codex_subscription_image.py` 的 gateway provider/诊断，以及 `image_worker_pool.py` 的 Visual Lock proof 例外。**此前宽回归通过，但语义上违反原生通道红线。**
- 为此新增 `tests/system/test_native_image_no_proxy_bypass.py` 三条 AST 结构合同：Provider Gateway 必须固定为 `codex_subscription`；任何图片能力例外都必须受 Phase5A grant 约束，不得附加 OpenCodex 旁路；工具诊断只能使用 text-only smoke 任务。
- 新合同在错误合并结果上明确 **3 failed**（预期失败复现）；在独立集成工作树剔除这两处代理旁路后 **13 passed**（新旧路由测试联合复测）。
- 合并候选此时在业务逻辑上与 `b31b1c7` 一致。主工作区所新增的 OpenCodex 例外**不允许合并**；不以“自动文本合并”取代策略评审。
- 该集成候选只记录隔离验证，不意味着把主工作树中已有 133 项未提交变更重置、替换或合并到正式生产。禁止对此作为正式生产 Stage/Review Authority 证据。
