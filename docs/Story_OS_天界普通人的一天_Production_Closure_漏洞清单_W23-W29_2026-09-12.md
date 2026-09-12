# Story OS《天界普通人的一天》Production Closure 漏洞清单（W-23 ~ W-29）

- 日期：2026-09-12
- Episode：`episodes/天界普通人的一天/`
- 分支：`story-platform-v3`
- 触发任务：继续该 Episode 的全自动生产闭环（`VISUAL_CALIBRATED → PRODUCTION_PASSED → PUBLISH_READY`）
- 授权口径：用户要求「不要停止等待人工确认」「发现问题 → 记录 → 可修则修 → 继续推进」，单帧问题不得阻塞整个 Episode

> 编号说明：本文件的 **W-23 ~ W-29 是本 Episode 治理编号**，由用户在本轮任务中点名指定。仓库既有
> `reports/Story_OS_稳定生产闭环_暴露问题清单_20260911.md` 另有一套全局 W 系列（已用到 W-25 ~ W-34，见
> `reports/EP003_生产暴露问题整理_20260911.md`）。两者命名空间不同，本文件不修改、不重排历史清单。

## 1. 本轮真实生产事实（判定基线）

| 事实 | 证据 |
|---|---|
| Episode 阶段 `PRODUCTION_PASSED` | `meta/episode-state.json`（`updated_at=2026-09-12T21:13:04+08:00`） |
| 20/20 帧 `LOCKED`，画幅 1080×1350 | `meta/production-ledger.json` |
| 帧语义唯一残余错误全部指向 Frame 03 hook | `meta/frame-semantic-audit.json` |
| 用户已直接接受终稿与已知缺陷 | `meta/final-acceptance.json`、`meta/production-acceptance.json`（`basis=direct_user_review`, `known_defect_frames=["03"]`） |
| 发布正文/话题/置顶评论已补全 | `meta/release-manifest.json.publication` |
| 字幕终发布图 20/20 渲染完成 | `meta/subtitle-layout-audit.json`（`canonical_renderer=true`） |

## 2. 逐条清单

### W-23 Production Evidence Closure Gap

**现象**：生产证据的收尾口径在多个门禁实现里各自为政。`machine_gate.py` 与 `release_package.py` 接受
`meta/final-acceptance.json` 的受控降级，但 `delegated_delivery.preflight()` 与
`incremental_frame_review.verify_episode()` 直接要求帧语义 `PASS`，不接受任何降级——只要 Episode
带有**已由用户明确接受**的单帧缺陷，`delegated-delivery build` 就会硬失败，无法完成交付闭环。

**证据**：
- `release/production-review.md` 第 35 行已记录该边界为 W-23 / W-29。
- `episodes/_system/delegated_delivery.py`（本轮修改前）`preflight()` 中
  `if errors: raise SystemExit('frame semantic preflight failed: ...')`，无 acceptance 分支。
- `episodes/_system/incremental_frame_review.py:503` `verify_episode()` 未引用 `final_acceptance`。

**根因**：acceptance 降级是在各调用点分别实现的，没有统一策略模块；新增调用点容易漏接。

**本轮处置**：在 `delegated_delivery.preflight()` 接入 `from final_acceptance import valid as acceptance_valid`，
有合法 `final-acceptance.json` 时降级为 `DELEGATED DELIVERY WARN` 并继续。与 `machine_gate` / `release_package`
同口径。`incremental_frame_review` **未改动**（它同时服务增量复审决策，降级语义不同，留给 W-26）。

**状态**：已修复（代码）。当前不构成 PUBLISH_READY 阻塞。

---

### W-24 Runtime Projection Drift

**现象**：`meta/runtime/next-action.json` 是纯派生缓存（`next_action.py` 从 `episode-state.json` 推导），
一旦上游事实变更而派生文件未重跑，就会出现「派生 < 事实」的漂移：下游宿主/Agent 读到的是旧世界。

**本轮实测到的具体漂移**：
- `meta/runtime/next-action.json` 生成于 `21:19:03`，其 `progress.publication` 仍是
  `description=null, topics=[], pinned_comment=null`；
- 而 `meta/release-manifest.json` 在 `21:34:20` 已补齐 description / topics / pinned_comment。
- 即：真实生产事实 > ledger > runtime projection 的链条在最后一跳断了。

**根因**：派生文件没有"上游 SHA 失效"标记，任何写入 `release-manifest.json` / `episode-state.json` 的动作
都不会自动使 projection 失效；只有显式调用 `story_os.py next-action --write` 才刷新。

**本轮处置**：在阶段推进到 `PUBLISH_READY` 后重新生成 projection，并复核
`action / target_state / blocking / hard_stop / continue_without_user_prompt` 与真实阶段一致。
长期建议（未实施）：把 projection 的 `derived_at` 绑定上游文件 SHA，读侧做漂移检测。

**状态**：本轮漂移已消除（重生成派生）；机制性缺口仍存在。

---

### W-25 Human Acceptance State Transition Missing

**现象**：用户在 `meta/final-acceptance.json` / `meta/production-acceptance.json` 已明确
「接受当前 20 张为终稿、接受携带已知缺陷」，但没有任何机制把这份人工决策转换成阶段推进；
生产侧仍表现为"等待人工"（例如 `production-ledger` 早期帧 03 状态为 `NEEDS_USER`），
全自动流程因此停在原地。

**证据**：`meta/production-acceptance.json`（`decision=accept_current_as_final`、
`declared_at=2026-09-12T20:35:00+08:00`）；`meta/runtime-checkpoint.json` 中
`incremental_frame_review.build_plan` 曾以 `frame 03 not production-passed: 'NEEDS_USER'` 报错（`attempt 13` 记录）。

**根因**：人工终稿接受被建模为「证据文件」而不是「状态迁移事件」，缺少
`Evidence → Ledger → Projection → Next Action → Gate` 的显式转换入口。

**本轮处置**：以 `final-acceptance.json` 为唯一接受依据，按用户已给的决策继续推进；
所有降级点统一打印 WARN 并保留原始证据文件不改写（`frame-semantic-review.json` 保持
`summary.passed=false`，不冒充通过）。

**状态**：本轮受控绕过（不阻塞）。

---

### W-26 Human Decision Reconciliation Missing

**现象**：缺少把"用户决策"与"机器残余门禁错误"做统一对账的入口。结果是对同一份
`final-acceptance.json`，不同脚本各自解释：

| 脚本 | 是否有 acceptance 降级 |
|---|---|
| `machine_gate.py` | 有 |
| `validate_episode.py` | 有（production / subtitle / sound_card / fast_frame_scout） |
| `release_package.py` | 有 |
| `final_candidate_snapshot.preflight()` | 有（frame semantic / fast scout） |
| `delegated_delivery.py` | **本轮前无** → 已补 |
| `release_preflight_verify.verify_release_semantic()` | **无**（见 W-28） |
| `incremental_frame_review.verify_episode()` | **无** |

**根因**：降级策略分散实现，缺少 `acceptance_policy` 公共模块与统一的
"哪些门禁可降级 / 降级后 INFO 文案 / 禁止降级白名单"声明。

**本轮处置**：`delegated_delivery` 对齐；其余未动。**未做**的是抽公共模块（属结构性重构，
超出本轮 P0 边界），仅在本清单登记。

**状态**：部分修复。

---

### W-27 Runtime CLI Contract Drift

**现象**：两类漂移，都会让自动化脚本静默走错分支。

1. **同机两个 codex CLI 并存**：
   - PATH 命中的 `C:\Users\79873\AppData\Local\OpenAI\Codex\bin\codex.exe` = `0.130.0-alpha.5`，
     会直接报 `unknown variant \`default\`, expected \`fast\` or \`flex\``（因为用户全局
     `config.toml` 写了 `service_tier="default"`，该版本不认识）。
   - `D:\soft\nvm-setup\nodejs\codex.cmd` = `0.153.4`，可用。
2. **子命令参数顺序不统一**：
   - `validate_episode.py <episode_dir> --target X`（目录在前）
   - `evidence_gate.py --target X <episode_dir>`（目录在后）
   - `story_os.py release-package <episode_dir> <build|verify|show>`（子命令在目录之后）

**本轮处置**：所有需要 codex 的步骤显式传 `--codex "D:\soft\nvm-setup\nodejs\codex.cmd"`，
避免命中坏版本；**没有**修改用户的全局 `config.toml`（属用户环境，未授权且改动不可逆）。

**状态**：已规避，不阻塞。建议后续在脚本层增加 codex 版本探测与 fail-fast。

---

### W-28 Release Evidence Missing

**现象**：两类。

1. `release_preflight_verify.verify_release_semantic()` 只报 `missing / stale`，没有 acceptance 降级路径
   （与 W-26 同源）。一旦帧语义带已接受缺陷，release critic 的失败无法被人工接受覆盖。
2. `meta/release-manifest.json` 的 `release.contact_sheet_path` 指向
   `episodes/天界普通人的一天/production/contact-sheets/publish-final.jpg`，**该文件不存在**
   （本轮实测 `Test-Path` = False）。

**影响评估**：`final_candidate_snapshot.build_lock()` 只消费 `cover_path` / `publish_dir` /
`body_glob` / `body_frame_count` / `artifacts.*`，**不校验** `contact_sheet_path`；
`release_package.py` 同样不校验。因此当前不阻塞 PUBLISH_READY，但该字段属于
"清单里写了、磁盘上不存在"的悬空引用。

**本轮处置**：

- 第 2 类（悬空引用）：已修复。用真实 `production/publish/01..20.png` 像素生成 contact sheet，写到清单已声明路径
  `episodes/天界普通人的一天/production/contact-sheets/publish-final.jpg`（1152×1268，SHA256
  `9f410c7d028a2cb529534001e7c7d1015d7cc9cec02986ce3d937a9b68d2d13b`）。这是真实派生预览图，非占位文件；不参与任何门禁 SHA，故不影响已 LOCKED 的 snapshot / release package。
- 第 1 类（release critic 无 acceptance 降级）：本集 release semantic critic 本轮真实 PASS，未被触发；保留记录供后续剧集参考，不在本集扩大改动范围。

**状态**：悬空引用已修复；第 1 类保留为观察项。

---

### W-29 Full-Auto Recoverable Gate Cannot Auto-Advance

**现象**：存在"机器可自行修复、但门禁没有自动修复入口，只能人工介入"的点。本轮实测触发 3 次：

1. **caption-image-audit 无 per-frame 恢复器**：该审计以 5 帧为 chunk，任一帧
   `subtitle_unobstructed=false` 就令 `summary.passed=false`。但没有"自动重排该帧字幕 →
   重审该帧"的闭环，只能人工改 `meta/subtitle-layout.json` 后重跑。
   本轮实测：chunk 1 报 Frame 02 遮挡（字幕 x72–996 / y702–754 压住工单白纸正文 x482–943 与握夹子的手 x210–423），
   chunk 3 报 Frame 16 遮挡（字幕 x69–383 / y707–757 整段盖住前景回收袋印刷 `可回收物`）。
2. **Fast Scout 缺失不可自愈**：高风险帧缺 `meta/frame-scouts/<NN>.json` 或 `frame_contract_sha256`
   漂移时，`fast_frame_scout.audit()` 只报错，不会自行补跑。
   本轮实测：`meta/frame-scout-summary.json` 报 `high-risk frame 03 scout stale` 与
   07/12/17/18/19 `missing`，共 6 条。
3. **W-25/W-26 的降级点**同样只能靠调用方各自判断。

**本轮处置**：
- 用官方 `meta/subtitle-layout.json` 的 `safe_zone_override_reason` 机制（制作规范第五章允许的
  唯一合法出口）为 Frame 02 / Frame 16 指定回避位置，并重渲染 + 重跑字幕布局审计 +
  重跑 caption/image 审计（按 publish SHA 增量，只重审这 2 帧）。
- 手工补跑 6 个高风险帧的 Fast Scout。
- 明确不改：门禁脚本的判定阈值不动，证据文件不改写。

**状态**：本轮实例已恢复；机制性缺口（缺自动恢复器）仍开放。

## 3. 本 Episode 全部降级项（供发布决策复核）

| 项 | 口径 | 依据 |
|---|---|---|
| Frame 03 hook 缺陷（`ANOMALY_UNREADABLE` / `STORY_BEAT_NOT_VISIBLE` / `ANOMALY_CONCEALMENT_MISSING`） | 用户直接接受为已知缺陷 | `meta/final-acceptance.json` |
| `quality.production_gate` | 保持 `pending`，**不冒充 pass** | `meta/release-manifest.json` |
| `reviews.production` / `reviews.subtitle` / `sound_card_completed` | waived（用户接受） | `validate_episode` WARN 输出 |
| Fast Scout 07/12/17/18/19 与 03 | 本轮已补跑真实证据（见 W-29 处置） | `meta/frame-scout-summary.json` |
| `release.contact_sheet_path` | 本轮已生成真实 contact sheet，引用不再悬空 | W-28 |
| codex CLI 版本 | 显式指定可用版本，不改全局配置 | W-27 |

## 4. 剩余真正硬阻塞

本清单 W-23 ~ W-29 **没有一条**指向"必须人工才能继续"的硬阻塞：全部已修复、已规避，
或已在不改证据的前提下如实降级记录。

真正需要用户亲自做的只有发布动作本身（在抖音端确认 AI 生成标识并发布），
它不属于 Story OS 门禁，也不由本流程代理。

## 5. 相关文件

- 生产验收记录：`episodes/天界普通人的一天/release/production-review.md`
- 帧语义证据：`meta/frame-semantic-review.json`、`meta/frame-semantic-audit.json`
- 字幕布局：`meta/subtitle-layout.json`、`meta/subtitle-layout-audit.json`
- 字幕/画面审计：`meta/caption-image-audit.json`（与 `meta/caption-image-audit-v2-00{1..4}.jsonl` 原始日志）
- 快扫证据：`meta/frame-scout-summary.json`、`meta/frame-scouts/*.json`
- 阶段事实源：`meta/episode-state.json`
- 派生投影：`meta/runtime/next-action.json`

## 6. 最终闭环状态（2026-09-12 22:00）

阶段推进完成：`VISUAL_CALIBRATED → PRODUCTION_PASSED → PUBLISH_READY`。

推进命令：`python episodes/_system/episode_state.py transition "episodes/天界普通人的一天" PUBLISH_READY --note "..."`
推进前验收：`validate_episode.py --target PUBLISH_READY` PASS（4 WARN 降级）、`machine_gate.py --target PUBLISH_READY` PASS（2 WARN 降级）、`EVIDENCE GATE PASS | target=PUBLISH_READY`。

| 漏洞 | 最终状态 | 说明 |
|---|---|---|
| W-23 Production Evidence Closure Gap | 已修复 | delegated_delivery.preflight 接入 final_acceptance 降级；Final Candidate Snapshot `b079b377` build+verify PASS |
| W-24 Runtime Projection Drift | 已修复 | `story_os.py next-action --write` 刷新，`action=COMPLETE` / state=PUBLISH_READY / publication 字段回填 |
| W-25 Human Acceptance State Transition Missing | 已解除 | `episode_state.py transition` 正常走完，acceptance 不再阻断迁移 |
| W-26 Human Decision Reconciliation Missing | 已解除 | 用户接受事实经 final-acceptance.json 统一消费，投影与门禁一致 |
| W-27 Runtime CLI Contract Drift | 已规避 | 显式传 `--codex "D:\soft\nvm-setup\nodejs\codex.cmd"`（0.153.4）；全局配置未改（属用户环境） |
| W-28 Release Evidence Missing | 已修复（悬空引用） | 生成真实 contact sheet 至已声明路径（SHA256 `9f410c7d`）；release critic 无降级路径保留为观察项 |
| W-29 Full-Auto Recoverable Gate Cannot Auto-Advance | 已修复 | Fast Scout 6 帧补齐 + caption-image-audit 重跑，可恢复门禁全部自动推进 |

结论：无必须人工才能继续的硬阻塞；唯一需要用户亲自完成的是抖音端发布动作（确认真实 AI 生成标识后发布），不属 Story OS 门禁。

---

## 7. 二次曝露扫描：W-30 ~ W-35（2026-09-12 22:10）

对 Episode 目录全部 meta 证据做悬空引用、状态一致性、编码与队列残留扫描后新暴露的问题。
以下全部**不阻塞**已完成的 PUBLISH_READY，逐条给出证据与处置。

### W-30 Runtime Checkpoint / DAG State Stale After Closure

**现象**：`meta/runtime-checkpoint.json` 仍是 `last_completed=RUNTIME_INITIALIZED`、`next_action=READ_EPISODE_STATE`、`locked_frames=[]`、`failed_frames=[]`；`meta/runtime-dag-state.json` 末次 `PRODUCTION=HOST_WAIT`（attempt 13）。两者都停在最后一次 DAG 尝试 `20:54`，而 `episode-state.json` 已是 `PUBLISH_READY`、ledger 20/20 LOCKED。

**影响**：不是阶段矛盾（AGENTS.md 明确 DAG / checkpoint 不是状态机，`episode-state.json` 才是权威），但任何按 checkpoint 恢复的流程会以为生产仍卡在等待宿主。

**处置**：不修。刷新它只能重跑 DAG 或手写状态，AGENTS.md 禁止手写状态；如实保留其作为“最后一次 DAG 运行事实记录”。

### W-31 Resume Capsule Projection Drift

**现象**：`meta/runtime/resume-capsule.json` 停在 `current_state=VISUAL_CALIBRATED`、`next_target=PRODUCTION_PASSED`（generated_at 20:54）。

**处置**：**已修复**。用官方派生缓存入口 `python episodes/_system/runtime_resume_capsule.py build <ep>` 重建，现为 `current_state=PUBLISH_READY`、`next_target=PUBLISHED`、`runtime_step=RELEASE`、`next_actions=["complete; do not reopen production unless user requests changes"]`。

### W-32 Windows Subprocess Output Encoding Corruption（U+FFFD / GBK）

**现象**：存储的运行时证据里中文集名被替换字符损坏 —— `runtime-checkpoint.json` 27 处、`runtime-dag-state.json` 153 处 `U+FFFD`，原文 `episodes/天界普通人的一天` 不可逆丢失。同一根因在测试侧可稳定复现：`test_v202_production_closure.test_backend_normalizes_to_ledger_canvas` 在默认编码下抛 `UnicodeDecodeError: 'gbk' codec can't decode byte 0x81`（`subprocess.run(..., text=True)` 用 GBK 解子进程 UTF-8 输出，`stdout` 变 `None` 后再触发 `TypeError`）。

**影响**：证据文本不可逆损坏（仅影响可读性，不影响任何 SHA 校验与门禁）；本机默认编码下相关测试假失败。

**处置**：不修改存储证据（改写历史证据不安全）；根因位于子进程输出捕获，属共享模块，按 P0 不扩大改动。**可用规避**：`set PYTHONUTF8=1`（已验证该测试随即 PASS，全套件 122 passed）。

### W-33 DAG Step False-PASS on Planner Crash

**现象**：`runtime-dag-state.json` 中 `INCREMENTAL_PLAN` 记为 `status=PASS`，但其 note 内嵌 `frame_plan.action=ERROR` 与真实 traceback：`ValueError: frame 03 not production-passed: 'NEEDS_USER'`。即内层 planner 崩溃时外层 step 仍记 PASS。

**影响**：DAG 证据把一次失败记成通过；同时暴露隐性健壮性问题 —— `frame_semantic_review.frame_records()` 遇到 `NEEDS_USER` 帧直接 `raise`，而不是降级为“阻塞帧”。

**处置**：如实记录，未改共享模块（P0 禁止随意改公共行为）。该异常在本集已随 Frame 03 转 LOCKED 自然解除；当前 `incremental_frame_review.py plan` 可正常执行。

### W-34 Production Queue Never Terminalized

**现象**：`meta/production-queue.json` 35 条中残留 `blocked:1`、`interrupted_unknown:4`、`superseded:5`，phase 残留 `BLOCKED:2`、`RECONCILE_PENDING:4`、`BEGIN_REJECTED:2`，Episode 关闭后未收敛为终态。其中帧16 的项 `16-4f68bcfaa7c2-a1`（BEGIN_REJECTED）携带的 `expected_lifecycle` 路径从未落盘（同帧 a2 已成功）。

**影响**：不阻塞门禁（ledger 20/20 LOCKED），但队列视图与实际交付不一致，属残留状态。

**处置**：不修。仅 `production_recovery.py recover-user-runner-success` 会写队列，且是逐帧、会改状态的命令，不适合在已闭环 Episode 上补跑。

### W-35 Accepted Known-Defect Frame Never Converges in Incremental Planner

**现象**：`incremental_frame_review.build_plan()` / `incremental_closure.plan()` 不读 `meta/final-acceptance.json`，Frame 03 永久判为 dirty（`review_not_pass` / `check_failed:*` / `bound_review_invalid`）。Episode 已在 `PUBLISH_READY`，planner 仍输出 `action=PRODUCTION_INCREMENTAL_REQUIRED`。

**影响**：一旦恢复自动运行，调度会反复针对 Frame 03 走返修路径，与用户“不再消耗返修额度”的明确要求冲突；属“已接受缺陷无法在 planner 收敛”的可恢复门禁缺口（W-29 同类）。

**处置**：**已修复**。`build_plan()` 接入 `final_acceptance.covers()`：被判 dirty 的帧若在 `known_defect_frames` 内，则移入显式字段 `accepted_known_defect_frames` / `accepted_reasons`（不静默当作 clean，也不参与 `context_change` / dirty ratio）。

**修复后验证**：

- `incremental_frame_review.py plan` → `action=NOOP`，`accepted_known_defect_frames=["03"]`
- `incremental_closure.py plan` → `frames=CLEAN`、`action=POSTFLIGHT_ONLY`（原为 `PRODUCTION_INCREMENTAL_REQUIRED`）
- `incremental_frame_review.py self-test` PASS、`contract_sync.py --check` PASS
- 回归：validate / machine_gate / evidence_gate / snapshot verify / release-package verify / delegated-delivery verify 全部仍 PASS
- 全套件：`python -m pytest episodes/_system -q` → 122 passed（需 `PYTHONUTF8=1`，见 W-32）

### W-36 环境卫生与证据细节（低风险观察项，合并记录）

| 项 | 现象 | 处置 |
|---|---|---|
| BOM 残留 | `meta/.frame-scout-04-a08ae795dc.candidate.json` 带 UTF-8 BOM，严格 `utf-8` 读取会失败；该 dot-file 未被 `frame-scout-summary.json` 引用，属遗留候选文件 | 记录，不改写证据文件 |
| 声明未产出的契约产物 | `character-visual-contract.master_policy` 声明 `meta/character-pixel-master.json` / `meta/character-master-crops.json`，本集 `pixel_master_required=false`，文件不存在 | 记录；不擅自改契约 |
| 胶囊缓存陈旧 | `execution-capsules/creative_story.json` 的 `current_state=IDEA_LOCKED`；缺失项均带 `exists:false` 如实标注 | 记录；胶囊为 derived cache，按 AGENTS.md 源规范优先 |
| 双 release-lock | `release-package.json.user_approved=true`（直接通道，源自用户已声明的终稿接受）与 `delegated-approvals.json.release_lock`（委托通道）同时存在，`evidence_gate` 取直接通道 | 记录，不删记录 |

### W-30 ~ W-36 结论

新增 7 项中 **2 项已修复**（W-31 resume capsule、W-35 planner 收敛），**5 项如实记录**（W-30 / W-32 / W-33 / W-34 / W-36）。**无一项构成 PUBLISH_READY 之后的硬阻塞**；最需要注意的是 W-32（编码根因，跨模块，建议后续统一 `PYTHONUTF8=1` 或显式 `encoding="utf-8"`）。
