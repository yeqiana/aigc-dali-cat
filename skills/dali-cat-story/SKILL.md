# dali-cat-story — Story OS V2.6.1 Adapter Contract

> This Skill is a **thin execution adapter** for the repository's canonical Story OS.  
> It does not own a state machine, does not duplicate engine logic, and must not become a second source of creative or release truth.

## 1. Authority

1. `standards/制作规范_正式版.md` —唯一创作规则权威。
2. `<episode>/meta/episode-state.json` —唯一机器阶段事实源。
3. `<episode>/meta/release-manifest.json` —最终发布版本事实。
4. `story-gates.json / production-ledger.json / frame-reviews/` —只保存证据，不保存第二套 stage。
5. 每次执行先读取仓库根 `START_HERE.md` 与根 `SKILL.md`，再按 `standards/AUTHORITY_INDEX.json` 路由当前任务需要的 active 细则。

## 2. Canonical Engine

所有状态推进、门禁、画幅归一、生产闭环和委托交付能力都由仓库唯一实现：

`episodes/_system`

**禁止**把以下核心实现复制到本 Skill 的 `scripts/` 中：

- `episode_state.py`
- `validate_episode.py`
- `machine_gate.py`
- `evidence_gate.py`
- `canvas_normalize.py`
- `delegated_delivery.py`
- `codex_auto_orchestrator.py`

Skill 只允许保留 wrapper / helper。升级 Story OS 时，优先升级 canonical engine 与本 adapter contract，而不是复制实现。

## 3. Human Golden Path

```text
Story Lock
→ Visual Lock
→ Batch
→ 逐帧审核 / 必要返修
→ text audit
→ Release
→ 6h / 24h / 48h / 7d 数据回填
```

人类工作流不能衍生第二套机器状态机。

唯一七阶段仍为：

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
→ PUBLISHED
→ DATA_REVIEWED
```

## 4. V2.0.3.3 Capability Contract

本 adapter 必须识别并服从以下 canonical capabilities：

- `single_state_machine`
- `multi_runtime`
- `machine_gate`
- `evidence_gate`
- `production_ledger`
- `frame_reviews`
- `canvas_normalization`
- `deterministic_postflight`
- `delegated_delivery`
- `release_manifest`
- `minimal_edit_contract`
- `continuous_work_host_loop`
- `derived_next_action`
- `preimage_runtime_node`
- `work_actual_pixel_review_barrier`
- `canonical_episode_discovery`
- `semantic_text_encoding_health`
- `runtime_path_portability`
- `canonical_module_index`
- `codex_batch_inflight_3`

支持的执行环境由根 Story OS contract 决定；当前 contract 覆盖 CODEX / ChatGPT Work / ChatGPT Web。任何 runtime 都不得绕开 Story Lock、Visual Lock、最小修改协议和 Release Lock。

## 5. Canonical Commands

初始化/阶段推进：

```bash
python episodes/_system/episode_state.py init <episode_dir> --id <id> --series <series> --title "<title>" --frame-count <n>
python episodes/_system/episode_state.py transition <episode_dir> <TARGET> --note "..."
```

验证：

```bash
python episodes/_system/validate_episode.py <episode_dir>
python episodes/_system/machine_gate.py <episode_dir> --target <TARGET>
python episodes/_system/evidence_gate.py <episode_dir> --target <TARGET>
python episodes/_system/contract_sync.py
```

不要手改 `current_state` 越级。

## 6. Minimal-edit Contract

- `subtitle_only`：底图由 SHA-256 锁定，只改字幕层/文本资产。
- `crop_only`：只允许改变构图裁切，不重生内容。
- `regenerate_frame`：只允许重做被点名帧。
- `regenerate_sequence`：只允许重做明确授权的连续区间。
- 未点名且已通过帧继续锁定，禁止“顺手统一重做”。
- Visual Lock 通过前不得进入正式 Batch。

## 7. Production Closure

Agent/worker 返回 `rc=0` 不等于剧集 COMPLETE。正式委托执行必须以 canonical deterministic postflight、release evidence 与真实 publish asset 为准；approved fallback 不得伪装成正式交付。

## 8. V2.0.3.2 Hardening Rule

V2.0.3.2 只做契约收敛与同步硬化，不新增第二个字幕审核管线、不新增 Capture Gate、不引入第二套 review state。

> **Invariant: Skill is an adapter, not a Story OS copy. Canonical engine exists only under `episodes/_system`.**

## V2.0.3.2 Creative Enforcement

This Skill remains a thin adapter. Canonical creative enforcement lives under `episodes/_system`.

Capabilities:
- `story_semantic_review`
- `visual_profile_enforcement`
- `deterministic_subtitle_layout`

Story Lock requires the canonical independent semantic review for V2.0.3.2 episodes; Visual Lock requires actual calibration profile review; publish subtitles use the canonical layout renderer/audit. No new episode state is introduced.


## V2.0.3.3 Frame Semantic Enforcement

Canonical capabilities additionally required:
- `actual_frame_semantic_review`
- `sha_bound_frame_reviews`
- `release_evidence_closure`

The adapter does not implement these capabilities itself; canonical implementation remains under `episodes/_system/frame_semantic_review.py`.

<!-- STORY_OS_V2_0_3_4_INCREMENTAL_ADAPTER_BEGIN -->
## V2.0.3.4 Incremental Workspace Adapter

The adapter delegates incremental/local-media work to the canonical engine; it does not own another state machine.

Canonical capabilities routed here:
- `incremental_closure`
- `dirty_set_propagation`
- `incremental_frame_review`
- `caption_fingerprint_binding`
- `local_media_workspace`
- `media_sha_index`
- `safe_media_migration`

Canonical implementations remain under `episodes/_system`:
- `incremental_closure.py`
- `incremental_frame_review.py`
- `media_workspace.py`

Skill is an adapter, not a Story OS copy.
<!-- STORY_OS_V2_0_3_4_INCREMENTAL_ADAPTER_END -->

<!-- STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE_BEGIN -->
## V2.5.1.1 Forced Candidate Gate
正式生图入口自动执行 Raw Candidate Budget；技术失败释放预算；同一 Queue Item 技术重试复用 token；候选额度耗尽后硬停止内容生图循环。
<!-- STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE_END -->

<!-- STORY_OS_V2_6_1_PRODUCT_RUNTIME_FIRST_BEGIN -->
## V2.6.1 Product Runtime First / Cross-Shell Contract

性能优先，但不降低创作门禁。恢复优先使用 Resume Capsule；正式图片候选走原子 Candidate Lifecycle。
禁止 Agent 使用 Bash heredoc、PowerShell here-string、嵌套 `powershell -Command`、`shell=True` 或把大段 JSON/多行 Python 塞进 shell。
多行/结构化内容必须走 UTF-8 文件、stdin 或仓库 file edit/write API；路径作为 argv 元素传递，不手工拼引号。
Final Visual Freeze 只绑定视觉 SHA，Caption 变化只触发 Caption ↔ Image Audit，不得重新拉起全量 Visual Critic。

V2.6.1 Runtime 能力声明：
- `product_runtime_first`
- `local_codex_explicit_only`
- `no_silent_codex_fallback`
- `product_runtime_host_action`
- `product_runtime_image_route`

WORK/WEB 的宿主动作使用 request_id + SHA-bound request history；正常等待宿主执行记为 `HOST_WAIT`，不是故障 `BLOCKED`。
<!-- STORY_OS_V2_6_1_PRODUCT_RUNTIME_FIRST_END -->
