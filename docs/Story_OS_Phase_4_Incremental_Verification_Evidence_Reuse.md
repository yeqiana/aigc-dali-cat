# Story OS Phase 4：增量验证与 Evidence 复用

状态：**PHASE_4_PASS**
生产模式：`COLLABORATIVE`
真实图片生成：**NO**
Phase 5A：**NOT STARTED**

## 目标与边界

Phase 4 只判断已有 Evidence 是否仍绑定当前权威输入，并让 Runtime DAG 跳过有效证据对应的昂贵模型工作。它是 Evidence Validity Planner，不是 Episode State、Generation Attempt、Review Queue、Production Ledger 或冻结 Model Policy 的新 Authority。

本阶段没有改变 Attempt hard cap、Attempt Lease/Fencing、Review Queue Authority、Repair Wave 上限、Stage 或 Production Mode；没有实现 Phase 5 Canary 或 CODEX_MANAGED Cutover。

## 当前增量验证图

| Evidence | CLEAN / 可复用条件 | 变化后的动作 |
|---|---|---|
| Story Review | 正式 verifier 通过；Story/Storyboard SHA、版本/上下文、schema、PASS decision、issue codes、critic provenance 与 Episode 冻结 role Policy SHA 均匹配 | `DIRTY → STORY_REVIEW_REQUIRED`；达到阶段但收据缺失则 `MISSING_EVIDENCE` |
| Visual Profile Review | 正式 verifier 通过；校准资产 SHA、Visual Profile SHA、StoryOS 上下文、schema、PASS 与冻结 `vision.visual_lock` Policy SHA 匹配 | `DIRTY → VISUAL_REVIEW_REQUIRED`；应有收据缺失则补证 |
| Frame Semantic Review | PASS 且 issue codes 为空；当前 Frame Contract/source binding、Logical Asset、current generation key、artifact SHA、Story/Visual/Phase 3 context、schema、critic provenance 与 Episode 冻结视觉 Review Policy SHA 全部匹配 | `PATCH` 重审 dirty targets；真正全局 context/schema/source drift 或 dirty 比率越界才 `FULL` |
| Subtitle Audit | 独立字幕审计通过；不作为像素语义 Review 的输入 | 只运行字幕 Audit/Release 补证，不污染 Frame Vision Review |

证据文件存在不等于 CLEAN。缺少 Evidence、无法验证、schema 不兼容、Policy SHA 未绑定、Decision 非 PASS、Issue 非空、critic provenance 无效或 current candidate 不匹配都会 fail closed。Frame 的缺失收据同时进入 `missing_evidence_frames` 与 dirty targets，只补必要 Review，不回到 Story 起点。

Canonical fingerprint 不包含时间戳、队列深度、worker ID 或绝对路径。Frame fingerprint 包含 evidence 类型、logical asset key、generation key、artifact SHA、source binding、相关 Story/Visual 与 Phase 3 context、Episode-bound Policy SHA、Review schema 版本。Story/Visual fingerprint 同样只采用各自相关的 source/contract/context、冻结 Policy 和 schema。

## Dirty 与 Context

`dirty_frames` 是必须重新验证的目标；`context_frames` 只是目标 Review 的只读上下文，不会因此重生图片或再次调用 Critic；`reused_frames` 保留有效 PASS Evidence。

20 帧确定性夹具结果：

| 场景 | 动作 | dirty | context | reused | Critic 调用 |
|---|---:|---|---|---:|---:|
| 无变化 | `NOOP` | 0 | 0 | 20 | 0 |
| 仅 Frame03 artifact 改变 | `PATCH` | 03 | 02,03,04 | 19 | 1 |
| Repair 改变 03/07/11 | `PATCH` | 03,07,11 | 02,03,04,06,07,08,10,11,12 | 17 | 3 |
| Story Source SHA 改变 | `FULL` | 全部 20 帧 | 全部上下文 | 0 | 20 |
| Frame03 Evidence 缺失 | `PATCH` | 03 | 02,03,04 | 19 | 1 |

单帧与三帧修复分别比 20 帧全量复核少 95% 与 85% 的目标模型调用。虚拟成本按每个 fake Critic 300 ms 计算：全量 6000 ms、单帧 300 ms、三帧 900 ms；这是确定性调用预算估算，不是真实 Provider 或实测线上耗时。

Caption SHA 变化由 caption/image audit 独立处理，不会单独触发全帧 Vision Review。字幕烧录改变最终像素时，最终 artifact SHA 与字幕发布证据仍须单独校验。

Repair Attempt2 成为 current candidate 后，Attempt1 的 Review 仍保留历史但不会被当成当前 PASS；当前 logical key、generation key、artifact SHA、contract/context 与冻结 Policy SHA 必须一致。Frame03 修复只污染自身及 Review Contract 明确要求的 continuity context，不自动重审未改变帧。

## Runtime DAG 与 Phase 3 Repair Wave

`runtime_dag.py` 先运行 `incremental_closure.plan()` 并消费其 JSON：

- 帧 `NOOP`：执行只读 verify，不派发 Critic。
- 帧 `PATCH` / `FULL`：调用既有 `incremental_frame_review.py review`，仅对 dirty targets 做 Review。
- Story/Visual 已到目标阶段且 canonical target gate 通过：Runtime 复用目标证据并跳过整个已完成步骤；目标阶段已到但 gate 失败且 Planner 判 `DIRTY`/`MISSING` 时，只路由对应 scoped Review。尚未完成 Story/Visual 域步骤时继续现有 authoring/calibration worker，不因单份 Review 收据而跳过整项工作。
- Subtitle `DIRTY`/`MISSING`：只运行独立字幕审计。
- 缺失且没有受支持恢复路径的权威 Evidence：fail closed，不静默当作 CLEAN。

Phase 3 Repair Wave 完成时，`repair_aggregator.finalize_wave()` 幂等生成并持久化 Incremental Plan。Resume 复用同一结果；若 Planner 未把修复帧列为 dirty，记录 `INVALIDATION_MISMATCH`，不能宣称增量验证通过。后续仍由现有 Final/Release Gate 决定阶段推进。

Runtime 记录 `INCREMENTAL_PLAN_STARTED/FINISHED`、`INCREMENTAL_VERIFY_STARTED/FINISHED`、`EVIDENCE_REUSED`、`EVIDENCE_INVALIDATED`、`EVIDENCE_MISSING`、`FRAME_REVIEW_REUSED/RECOMPUTED`。Telemetry 只记执行事实，不授予 PASS。

## Frozen Policy 与全局配置漂移

复用身份读取 Episode 已冻结的 `model_policy_persistence` SHA，不重新 resolve 当前全局配置。全局配置后续变化本身不会让同一 Frozen Episode 的 Evidence 全部变脏；Episode-bound Policy SHA 实际变化、缺失或 Receipt 未绑定该 SHA 时禁止复用模型 Evidence。

## Phase 3 辅助失败归因矩阵

| 辅助失败 | 分类 | 处理与结论 |
|---|---|---|
| Runtime Registry 旧断言仍期望旧节点列表 | `B_STALE_TEST_EXPECTATION` | 当前正式 DAG 已含既有 `PROMPT_AUTHORING` 节点；只更新测试期望，没有删减生产节点。 |
| TEST_ONLY MySQL 测试库缺 Attempt 表 | `D_ENVIRONMENT_SETUP` | 测试 Setup 通过现有迁移/bootstrap 建表；没有在生产代码加静默 fallback。 |
| delegated approval fixture 缺 checkpoint | `C_INVALID_TEST_FIXTURE` | Fixture 使用正式 `runtime_checkpoint.save()` 建立前置证据；没有降低生产 checkpoint 要求。 |

额外确认：治理 convergence 的 Phase 4 旧 Fixture 缺少 current generation/policy/fingerprint 属于 `C_INVALID_TEST_FIXTURE`，已补 canonical identity；Frame Semantic enforcement 的隔离 MySQL/JSON authority 配置属于 `C_INVALID_TEST_FIXTURE`；Runtime Observability 自测临时 Episode 的 MySQL 隔离配置属于 `D_ENVIRONMENT_SETUP`。以上修正没有放宽正式校验。

## 验收记录

- Phase 4 合并用例（含 Runtime Registry 和 Governance convergence）：83 passed、15 subtests passed。
- Phase 1/2/3 核心 Authority / Queue / Recovery 回归组：107 passed、8 subtests passed。
- 测试 Setup 自测：TEST_ONLY MySQL bootstrap 5 passed；delegated approval / frame semantic fixture 5 passed。
- Phase 3 修复后辅助用例：Runtime Registry、TEST_ONLY MySQL bootstrap、delegated approval checkpoint fixture 均通过。
- Runtime DAG、Runtime Observability 自测，StoryOS 配置校验、Python compile、`git diff --check`：提交前需记录最终结果。
- `tests/system/test_report_regressions.py` 与 `unused/meta/episode-performance-ledger.json`：`CONCURRENT_MODIFICATION_BLOCKED`，未纳入 Phase 4 修改/提交范围。
- 仅用 synthetic fixtures 与本地确定性测试；没有调用真实图片生成。

Phase 5A Canary / CODEX_MANAGED Cutover **未开始**。
