# StoryOS V3 Phase 9 Production Industrialization Acceptance

更新时间：2026-09-19  
适用分支：`story-platform-v3`  
结论级别：**CONDITIONAL / CODE-GREEN / PRODUCTION-EVIDENCE-PENDING**

## 1. 本次验收范围

本报告只记录当前工作区可复核的事实，不把代码测试、历史演练或 UI 状态冒充真实 Episode 生产结果。

覆盖：

- Runtime ownership / persistence authority；
- Platform/System 回归与恢复、学习闭环；
- Web Console 类型检查与构建；
- 当前 Episode 状态与 Phase 9 生产闭环缺口。

## 2. 已验证通过

| 领域 | 证据 | 结果 |
| --- | --- | --- |
| Runtime ownership | `python scripts/phase9_production_switch.py status` | V3_RUNTIME takeover `EFFECTIVE`，记录 owner 为 V3 |
| Canonical create 路由（只读 dry-run） | `story_os.py create --dry-run --json` | `09/05`、`10/02` 及新增“河边拍照”自然语言请求均返回 `PLANNED` 且 `written=false`；`11/01` 的旧 Runtime Request 仍无法解析 Story Intent，返回 `STORY_INTENT_NO_SIGNAL` |
| Python 全量回归 | `pytest tests/platform tests/system` | `1678 passed, 1 skipped, 5 warnings, 90 subtests`（迁移审计修复后重新验证） |
| 恢复/学习/文档定向回归 | `test_docs_authority_consistency.py`、`test_phase9_report_governance.py`、`test_phase95_learning_loop_integration.py`、`test_runtime_memory_advisor.py` | `8 passed`；全量回归为 `1678 passed, 1 skipped` |
| Learning self-test | `python episodes/_system/account_learning_index.py self-test` | PASS |
| Product doctor | `python episodes/_system/story_os_doctor.py` | errors=0, warnings=0 |
| Contract sync | `python episodes/_system/contract_sync.py` | Story OS V2.6.1 contract sync PASS |
| Frame/API 回归 | `pytest ...test_web_console_api_contract.py ...test_frame_contract_parallel_compile.py` | `4 passed` |
| Web Console | `npm run lint` / `npm run build` | 类型检查和 Vite 构建均通过；仅有 bundle size warning |
| Golden candidate scan | `python episodes/_system/golden_episode_regression.py candidates` | 4 个候选，`eligible_count=0`；未伪造 Golden registry |
| Frozen media recovery plan | `python episodes/_system/frozen_media_recovery.py plan ... --source-episode ...` | 65/65 `PRESENT_MATCH`，`restorable_count=0`，无媒体字节缺口 |
| Canonical derived refresh | Character Appearance Anchor + 20 Frame Contracts | Anchor/Frame Contract verify PASS；仅更新派生 contract/preimage cache，未修改 `episode-state`、Production Ledger、Final Candidate Snapshot |
| Visual Lock re-plan | `visual_lock_v21.py bind-from-queue` + 当前队列/合同核验 | 4 个 admission 均已按当前合同 SHA 绑定；Frame 01/03/12 实际像素 PASS，Frame 15 实际像素未兑现 `impact=4`，系统保持 `NEEDS_USER`；阶段仍为 `PUBLISH_READY` |
| 当前 Visual Lock 生产证据 | `image_scheduler.py run --max-workers 1` + provider receipts/lifecycle | Frame 01/03/12/15 均由 Codex Subscription `gpt-image-2` 真实生成，4:5 1080×1350，NP01 normalize，4/4 COMMITTED；raw-candidate budget 75/75，无旁路生成 |
| Production Ledger / Receipt 审计 | `production_ledger.py audit` + `meta/provider-receipts/` | Ledger PASS；4 个 provider receipt 与 4 个 COMMITTED 记录一致；`inflight_reserved=0`、`available=0`，无悬挂预算 claim |
| 本轮 Ledger CLI 缺陷修复 | `production_ledger.py review/show/audit` + 定向回归 | 修复循环导入导致的 `episode_dir/get_ledger` 未初始化；97 个 Phase9 定向 platform/system 用例通过 |
| Story Intent Parser 入口修复 | `story_intent_parser.py` + `test_autonomous_pipeline.py` | 将“照片/拍照/摄影/拍摄”纳入沉浸式采集信号；53 个 canonical/autonomous 用例通过，普通照片请求不再误报 `STORY_INTENT_NO_SIGNAL`；全量回归已复验 |
| V2.1 Migration evidence integrity | `migrate_v21.py` + `test_migrate_v21_evidence.py` | 索引引用的 `frames/*.json` 缺失时不再报告 `CURRENT_V21_OK`；11/01 现明确为 `PLAN_REPAIR_CURRENT_EVIDENCE`，且 `activation_plan.missing_evidence` 显式列出缺口；新增回归 `2 passed` |
| Derived refresh regression | `PYTHONPATH=. python -m pytest ...frame_contract_parallel_compile.py ...visual_lock_admission_state.py` | `18 passed` |
| Runtime consistency scan（当前工作区） | `python scripts/phase9_consistency_scan.py --quiet` | `consistent=true`；当前 JSONL/MySQL 对照无不一致项（两侧均无事实行，不能替代真实双写样本） |
| Runtime recovery drill（当前工作区） | `python scripts/phase9_recovery_drill.py --quiet` | 四场景 `24/24` 步骤通过；`worker_liveness_not_critical`、`recovery_decision_has_no_executor` 均已由 watchdog / executor 关闭 |
| Checkpoint / Resume / Advisor 定向回归 | `test_runtime_checkpoint_owner_authority.py`、`test_runtime_checkpoint_authority_consumers.py`、`test_preimage_resume.py`、`test_runtime_memory_advice.py`、`test_runtime_memory_advisor.py` | `12 passed`；覆盖 owner、checkpoint 消费、断点恢复与建议链 |
| Runtime staging smoke（JSONL） | `python scripts/phase9_runtime_smoke.py --mode jsonl --no-redis` | `PASS=19, FAIL=0, SKIPPED=13`；MySQL/Redis 双写与实时状态本次明确未验 |
| Account learning index refresh | `python episodes/_system/account_learning_index.py rebuild --limit 5` | `sample_size=0`；当前没有可用的真实发布数据，指数仍只能作为空证据容器 |

## 3. 当前生产事实

当前真实 Episode 状态统计（排除 `_archive`、`_tests`、`_system`）：

| 状态 | 数量 |
| --- | ---: |
| `IDEA_LOCKED` | 4 |
| `STORYBOARD_LOCKED` | 1 |
| `VISUAL_CALIBRATED` | 2 |
| `PUBLISH_READY` | 4 |
| `PRODUCTION_PASSED` | 0 |
| `PUBLISHED` | 0 |
| `DATA_REVIEWED` | 0 |

因此当前不能宣称“真实生产闭环已完成”，也不能宣称已经形成 3-Episode Production SLO。

## 3.1 Phase 9 逐项验收矩阵

| 项目 | 当前判定 | 证据边界 |
| --- | --- | --- |
| P9.1 Filesystem Authority / Owner Persistence | **CODE PASS** | Authority、owner、SHA、派生缓存与导出边界已有测试和 Doctor/Contract Sync 证据；尚缺三篇真实生产样本的长期运行证明 |
| P9.2 Runtime 全链路 / 无 bypass | **CONDITIONAL** | Canonical create、状态门禁和 runtime consistency 通过；三篇候选尚未各自跑通 `create → release` |
| P9.3 Episode State / Gates / Checkpoint / Resume | **CODE PASS** | 单状态源、恢复演练 `24/24`、Checkpoint/Resume 定向回归通过；未替代真实生产中断样本 |
| P9.4 Experience Store / Feedback / Advisor | **CONDITIONAL** | Advisor 与离线学习链路通过；真实发布反馈 `sample_size=0`，不能证明持续学习效果 |
| P9.5 Platform / System Regression | **PASS** | 全量 Python 回归 `1678 passed, 1 skipped`，Product Doctor、Contract Sync、Runtime smoke 均通过 |
| P9.6 Docs / Reports Consistency | **PASS** | 当前验收报告、迁移审计报告与治理回归一致；工作树仍未达到提交前洁净标准 |

## 4. 未通过 / 待补证据

1. **Storage Profile 仍是候选冻结**：F0 的当前路径证据已形成（`episode_meta_store.mode=json`、`hot_state.mode=file`、runtime trace 为 JSONL），但工作树不洁，F1 不能转为正式 SLO provenance；MySQL/Redis authority 继续保持 DEFERRED，不把测试能力冒充生产双写。
2. **真实 SLO 样本不足**：已识别 3 个带 Runtime Request 的待整备候选（`09/05` 当前 `PUBLISH_READY` 但被 Frame 15 阻塞；`10/02` 为 `VISUAL_CALIBRATED` 且缺生产/发布门禁；`11/01` 为 `PUBLISH_READY` 但缺 V2.6 合同与语义审查）。三者都尚未在同一 commit、同一 Production Profile 下完成真实 `create --full-auto → PUBLISH_READY`，也缺少 E2E、ACTIVE、HOST_WAIT、图片、Review、repair 和人工介入统计。
3. **发布后闭环未完成**：当前 `PUBLISHED=0`、`DATA_REVIEWED=0`；本次 learning index rebuild 的 `sample_size=0`，因此 Experience Store 只有代码/离线闭环，缺少真实发布反馈校准。
4. **Golden / 真实性证据不足**：2026-09-19 候选扫描为 `candidate_count=4 / eligible_count=0`，Golden registry 仍为空；真实现代 Runner 新 Episode 证据不足，历史报告不能替代本次生产证据。
5. **目标 Episode 的当前机器阶段虽为 `PUBLISH_READY`，但重新验收仍未通过**：Frame Contract/人物锚已完成派生重建；Visual Lock 四张当前合同像素已真实生成，其中 Frame 01/03/12 PASS，Frame 15 因高冲击异常未在像素中成立而进入 `NEEDS_USER`。不能把普通交接画面冒充高影响准入，也不能自动伪造用户授权。
6. **三候选目标门禁仍未形成真实生产样本**：对当前带 `meta/runtime-request.json` 的三篇候选重新执行 `validate_episode.py --target PUBLISH_READY --metadata-only`：09/05 失败于 `visual_admission`/Frame15；10/02 失败于 `state_authority` 与缺失 `release-manifest.json`；11/01 失败于 `quality.production_gate != pass`、production/subtitle review 仍为 `waived`。因此三篇均不能被计入 PUBLISH_READY 生产样本。
7. **工作区洁净性**：`git diff --check` 仍报告 Web Console 现有改动中的尾随空白/文件末尾空行；不影响上述功能测试，但未达到提交前洁净标准。

## 5. 本次未执行的副作用操作

- 未切换 JSON/File 到 MySQL/Redis 默认模式；
- 未伪造或手工推进 `episode-state.json`；
- 本轮已启动并完成目标 Episode 的四张 Visual Lock 真实图片任务；未启动发布任务，也未推进 Episode 阶段；
- 未提交或推送 Git。

## 6. Acceptance Decision

**NO-GO（生产真实性） / GO（代码回归与审计基础）**。

下一道硬门槛是：先冻结 Production Profile，再以同一版本完成 3 篇真实 Episode，并补齐 release/post-publish/learning evidence；在此之前，Phase 9 只能标记为条件通过，不能标记 COMPLETE。
