# Story OS — Repository Execution Contract V2.6.1

> 这是 `aigc-dali-cat/story` 的 Agent 执行入口，不是第二套创作规范。
> **创作规则冲突时，以 `standards/制作规范_正式版.md` 为唯一权威。**
> **机器阶段冲突时，以 `meta/episode-state.json` 为唯一状态事实源。**

## V2.6.1 Product Runtime First

- 默认整体 Runtime 为 `WORK`，当前 ChatGPT/Work + DevSpace 负责 Story、PREIMAGE、Critic、Review、Gate、Release。
- 默认图片执行 Runtime 为 `CODEX`；这只授权 image generation / image repair，不得把整个 Story OS 路由成 CODEX full-auto。
- 本机 `codex.exe` 的存在不代表整体 Runtime=CODEX；整套 CODEX Runtime 仍需显式 `STORY_OS_RUNTIME=CODEX`。
- 图片执行可用 `STORY_OS_IMAGE_RUNTIME=CODEX|PRODUCT_RUNTIME|AUTO` 临时覆盖；PRODUCT_RUNTIME 才使用 `HOST_ACTION_REQUIRED / HOST_WAIT` 图片 Host 路径。
- Host Action 使用 `meta/runtime/host-requests/<request_id>.json` 保存不可覆盖历史；`product-host-request.json` 只作为当前指针。
- Product Review 使用 `<kind>-attempt-<n>-request.json`，同一 attempt 的 frozen inputs 不得覆盖。
- Concept / Story Critic provenance 支持 `WORK_ISOLATED / WEB_ISOLATED / CODEX_ISOLATED`；均必须 fresh、source-SHA-bound、不可伪造 PASS。
- Codex 图片执行只消费已锁 Prompt / Frame Contract / References；控制模型固定 `gpt-5.6-sol` + `reasoning=high`，实际图片模型固定 `gpt-image-2` + `quality=high`。图片产出后仍回 Story OS 做 Normalize / Ledger / Review / Gate。

<!-- STORY_OS_V2_1_CONCEPT_BEGIN -->
## Story OS V2.1：概念野心优先

- 系统名称统一为 Story OS；仓库名/历史 adapter 名不定义创作 IP。
- V2.1 新篇 Story Lock 前必须 8–12 候选，至少 3 个 A4/A5。
- 最终题必须定义 Cover/Mid/Climax，Concept Voltage ≥80，无字测试全 PASS。
- 真实性只约束“怎么拍”，不得用于提前压小异常规模。
- 正式门禁：`episodes/_system/concept_ambition.py`。
<!-- STORY_OS_V2_1_CONCEPT_END -->

<!-- STORY_OS_V2_1_PHASE3_BEGIN -->
## V2.1 Phase 3：环境物理与异常放大

- `visual.environment_contract` 是环境唯一权威字段；禁止新建独立 weather 权威文件。
- `baseline + segments + frame_overrides` 描述环境时间线。
- 每帧必须具有 narrative_role / frame_mode / impact_level / required_visual_cues。
- `anomaly_amplified` / `climax_impact` 必须 impact 3–4，具备 scale_reference 与 escalation_from。
- 每次正式生图前先解析该帧：`environment_contract.py resolve-frame <episode> --frame NN --json`。
- 最终实际像素审核绑定 per-frame environment/directive SHA，避免一段天气修改导致全篇无理由重审。
<!-- STORY_OS_V2_1_PHASE3_END -->

<!-- STORY_OS_V2_1_PHASE4_BEGIN -->
## V2.1 Phase 4：Resolved Frame Contract

- Environment / Impact Contract 后、Visual Lock 校准前执行 `frame_contract.py compile-all`。
- 每帧合同合并 Story / 局部分镜 / Visual DNA / Capture / Authenticity / Continuity / Environment / Impact / References。
- 合同缓存路径：`meta/runtime/contracts/frames/NN.json`。
- Production Ledger generation request 必须绑定 `frame_contract_sha256`。
- `codex_subscription_image.py generate-for-frame` 自动注入 `<frame_contract>`。
- Frame Semantic Review 必须验证批准像素对应 generation attempt 的合同 SHA 与当前 SHA 一致。
- 合同文件是 derived cache，绝不能反向覆盖 Story/Storyboard/story-gates。
<!-- STORY_OS_V2_1_PHASE4_END -->

<!-- STORY_OS_V2_1_PHASE56_BEGIN -->
## V2.1 Phase 5 + 6：四层 Visual Lock 与有界并发

- 新篇 `visual.calibration.policy=four_admission_v21`。
- Visual Lock 必须有 baseline / worst / first anomaly / high-impact 四张实际像素准入图。
- high-impact 不因异常巨大而失败；必须同时满足 impact 兑现、尺度参照和真实拍摄可信度。
- 正式生图由 `image_scheduler.py` 调度，最大并发 3。
- 并发只发生在 image backend；Production Ledger begin/success/tech-fail 严格单写者。
- 429/timeout/5xx 自动 3→2→1 降速；稳定两波逐级恢复。
- technical failure 不消耗内容返修；失败依赖链阻塞，无关帧继续。
- Repair 继续遵守每帧普通内容返修最多一次。
<!-- STORY_OS_V2_1_PHASE56_END -->

<!-- STORY_OS_V2_1_PHASE78_BEGIN -->
## V2.1 Phase 7 + 8

- Fast Scout 三结果：PASS_FAST / REPAIR_NOW / DEFER_TO_FINAL。
- Scout 永远不调用 Production PASS；Final Frame Semantic Critic 不删除。
- high risk 包括 identity / key prop / first anomaly / amplified / climax / payoff / ending / POV / impact3-4。
- low risk 不额外花模型调用，直接 DEFER_TO_FINAL。
- Scout 技术失败同样 DEFER，不阻断生产。
- PUBLISH_READY 前构建并 verify `final-candidate-snapshot.json`。
- V2.1 Delivery 只能读取 Snapshot 中锁定的 delivery_files + SHA。
- Snapshot 漂移时 Delivery 必须 BLOCK。
<!-- STORY_OS_V2_1_PHASE78_END -->

<!-- STORY_OS_V2_1_PHASE910_BEGIN -->
## V2.1 Phase 9 + 10

- Migration 默认 READ-ONLY；Legacy 不伪造新 Evidence。
- `regression_matrix_v21.py run` 是 V2.1 Closure 回归入口。
- `workflow-observability.json` 只诊断，不推进 stage。
- Final Snapshot 后不得为了 published_at / post_id / metrics 修改 release-manifest。
- 实际发布事实写 `meta/publish-event.json`。
- 数据窗口：6h / 24h / 48h / 7d；DATA_REVIEWED 最低要求 48h。
- 数据复盘写 `meta/post-publish-review.json` 与 `meta/next-story-learning.json`。
- `reports/account-learning-index.json` 供下一篇 Concept Ambition 前读取，但不能覆盖 Concept/Story/Visual gate。
<!-- STORY_OS_V2_1_PHASE910_END -->

<!-- STORY_OS_RUNTIME_REQUEST_P0_CORE_BEGIN -->
## Runtime Request P0

新篇自然语言入口先编译为 `runtime-request`。未提供剧情时必须 `auto_create`；粗剧情必须 `user_seed → strengthen_and_rewrite`；未指定 image 时默认 `image_model=gpt-image-2`、`image_quality=high`；显式 image 禁止静默替换或降级 Quality。当前 Visual Lock 固定为 4 张准入帧。
<!-- STORY_OS_RUNTIME_REQUEST_P0_CORE_END -->

<!-- STORY_OS_V1_6_GOLDEN_PATH_BEGIN -->
## Story OS V2.0.3.6 Golden Path

**第一入口：先读 `START_HERE.md`。** 该文件只负责路由，不建立第二套创作规范。

Golden Path：`选题/去同质化 → Story Lock → 真实性卡/连续性锚点 → 四张 Visual Lock 准入 → Batch → 逐帧审核/必要返修 → Final Checklist → Release → 数据回填`。

- 创作规则唯一权威仍是 `standards/制作规范_正式版.md`。
- 阶段唯一事实源仍是 `meta/episode-state.json`。
- `AUTHORITY_INDEX.json / story-gates / production-ledger / frame-reviews / FINAL_CHECKLIST` 都只是路由或证据，不得成为第二状态机。
- 不要默认通读整个 `standards/`；按 `standards/AUTHORITY_INDEX.json` 只读取当前任务需要的 active 细则。
<!-- STORY_OS_V1_6_GOLDEN_PATH_END -->

## 1. 单一状态源

禁止再创建第二套 `episode.yaml stage`。

每篇接入机器状态的剧集使用：

```text
meta/
├── episode-state.json       # 唯一阶段状态源
├── release-manifest.json    # 最终发布版本事实
├── story-gates.json         # 故事/视觉/字幕/锁图/机器证据配置，不保存阶段
├── production-ledger.json   # 逐帧生产事务，不保存阶段
└── frame-reviews/           # 严格模式下逐帧真实性结构化审查
```

职责必须分离：

- `episode-state.json`：只回答“现在处于哪个阶段”。
- `release-manifest.json`：只回答“最终准备/实际发布的是哪一版”。
- `story-gates.json`：只回答“进入下一阶段所需证据是否齐全”。
- `production-ledger.json`：只回答“每张图生产过程发生了什么”。
- `frame-reviews/NN.json`：只回答“该帧真实性/连续性硬项是否通过”。

任何证据文件都不能覆盖 `current_state`，也不能自建另一套 stage。

## 2. 任务开始前必须读取

读取顺序只由 `START_HERE.md` 第 1 节维护，本文件不再复制第二份顺序。任何流程先校验 `config/storyos.yaml`，再使用 `config/index.yaml` 限定阶段读取集；执行到本文件后，继续按 `AGENTS.md → standards/制作规范_正式版.md → AUTHORITY_INDEX.json active 细则 → 目标剧集` 路由。`README.md` 只做项目说明，不是执行入口。

## 3. 唯一生产状态机

沿用仓库原生 `_system`：

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
→ PUBLISHED
→ DATA_REVIEWED
```

正向推进必须使用：

```bash
python episodes/_system/episode_state.py transition <episode_dir> <TARGET> --note "..."
```

当前正向推进会依次执行：

1. `validate_episode.py`：manifest / 发布条件门禁；
2. `machine_gate.py`：真实性、校准、参考资产、逐帧结构化审查、production ledger 硬门禁；
3. `evidence_gate.py`：Story / Visual / Release 的稳定审批 provenance 与 SHA 门禁。

任一失败不得推进。禁止手改 `current_state` 越级。

## 4. Story OS 门禁映射

### STORY_GATE → 进入 STORYBOARD_LOCKED 前

必须满足：

- 最近 5 篇账号级同质化检查完成
- 四把锁至少 2 把不同
- 未触发机制换皮一票否决
- 任务/事件闭环
- 至少保留 2 种竞争解释
- hook / climax / payoff 已明确
- `reviews.story = passed`

### VISUAL_GATE → 进入 VISUAL_CALIBRATED 前

原有门禁：

- 恰好 4 张视觉准入帧，图号合法且互不重复
- `reviews.visual_admission = passed`
- `reviews.authenticity = passed`
- `continuity.required` 中声明的连续性锚点全部填写
- 不允许“先批量出图，再补锚点”

V1.5 严格机器门禁追加：

- 项目级真实性卡完整：年代、地点、拍摄者、拍摄原因、主设备、稳定/受限/失控三种状态
- 辅助采集设备最多 2 种且必须有剧情来源
- 当前第一视角设备或拍摄者若完整入镜，必须登记物理解释
- 四张 Visual Lock 准入必须分别为：普通相册基线 / 最差但成立条件 / 首次重大异常 / 高冲击异常
- 四张准入必须是四个不同图号，并保存 SHA-256 与统一 Review 证据
- 若本集声明 `references.required=true`，所有 required anchors 都必须有已通过且 hash 锁定的 reference asset

### PRODUCTION_GATE → 进入 PRODUCTION_PASSED 前

原有门禁：

- `reviews.production = passed`
- `reviews.continuity = passed`
- `reviews.authenticity = passed`
- 若本集需要字幕：声音卡完成、`reviews.subtitle = passed`、captions 证据存在

V1.5 严格机器门禁追加：

- `production-ledger.json` 正文帧数必须等于 manifest
- 每帧状态必须为 `PASSED` 或 `LOCKED`
- 每帧最多一次内容返修
- 每帧必须有 approved asset + SHA-256
- `LOCKED` 帧的 lock hash 必须等于 approved asset hash
- 每帧必须有 `meta/frame-reviews/NN.json`
- `viewpoint_physics / capture_profile_match / not_cinematic / album_test` 必须 pass
- identity / key_prop / location / continuity 等字段只要出现 fail 即阻断
- 有效摄影红旗 >=3 即阻断
- 红旗豁免必须是 detected 的子集且有预登记原因
- `repair / must_regenerate` 不得进入 PRODUCTION_PASSED

### RELEASE_GATE → 进入 PUBLISH_READY 前

在原传播评分/发布 Manifest 门禁基础上增加：

- `reviews.recommendation_fit = passed`
- `reviews.publish = passed`
- publish 正文数量符合 `body_frame_count`
- 本地完整验收时，正文发布图必须匹配 manifest 画幅：4:5 → 1080×1350；9:16 → 1080×1920；新篇未指定时默认 4:5
- 锁定底图 SHA-256 不得变化

## 5. 最小修改协议

用户修改指令默认解释为最小改动：

- “只改字幕 / 底图别动 / 一像素尽量别动” → `locks.edit_mode = subtitle_only`
- “只裁切” → `crop_only`
- “保持原画风重做这一张” → `regenerate_frame`
- “整段重做” → `regenerate_sequence`

当 `subtitle_only`：

- `locks.assets` 至少登记 1 个底图
- 必须保存 SHA-256
- 本地 validator 发现任一锁定资产 hash 改变立即 FAIL
- 未点名的已通过帧不得连带重做

## 5.1 Production Engine V1.2

正式出图使用 `meta/production-ledger.json` 记录逐帧请求指纹、技术失败、内容返修、候选 SHA-256、approved/lock 资产与批次；它不得保存剧集 stage。

- 未指定画幅：默认 `4:5 / 1080×1350`。
- 明确指定 `9:16`：使用 `1080×1920`。
- 技术失败不占内容返修次数；每帧最多一次内容返修。
- originals / repairs / approved / publish 必须分离，不得覆盖原图。
- 正式请求默认 prompt ≤260 字符且 ≤900 UTF-8 bytes，reference 默认最多 2 张并记录 role/kind/hash。
- 详细执行见 `standards/生产引擎与画幅规范_V1.2.md` 和 `episodes/_system/production_ledger.py`。

## 5.2 Machine Evidence V1.5

机器化不负责替代审美判断，只负责把已经写进规范的“硬条件”变成可验证证据。

常用命令：

```bash
# 新篇初始化后创建逐帧审查模板
python episodes/_system/evidence_tool.py init-reviews <episode_dir>

# 把已完成的真实性卡写回 story-gates
python episodes/_system/evidence_tool.py import-authenticity <episode_dir> --file <card.json>

# V2.1+ 使用 visual_lock_v21.py 的四帧准入计划、队列与统一 Critic。
# legacy 的三帧校准联系表仅用于历史 Episode 兼容，不能作为当前 Visual Lock 入口。

# 连续性参考资产（仅需要时）
python episodes/_system/evidence_tool.py reference-policy <episode_dir> --required --anchor protagonist --anchor location
python episodes/_system/evidence_tool.py register-reference <episode_dir> --id protagonist-main --anchor protagonist --kind identity --asset <ref.png>

# 最终机器预检
python episodes/_system/machine_gate.py <episode_dir> --target PRODUCTION_PASSED
```

## 6. 新篇初始化 / 旧篇升级

新篇：

```bash
python episodes/_system/episode_state.py init \
  episodes/10_新系列/01_新故事 \
  --id 10-01 \
  --series 10_新系列 \
  --title "新故事" \
  --frame-count 20
```

V1.5 新篇默认 `machine_contract.strict=true`，不允许缺真实性机器证据进入后续阶段。

旧剧集不批量伪造证据。缺 `story-gates.json` 时先：

```bash
python episodes/_system/episode_state.py migrate-gates <episode_dir>
```

迁移后默认 `machine_contract.strict=false`。只有旧剧集重新进入制作且真实证据已准备时执行：

```bash
python episodes/_system/episode_state.py enable-machine-gates <episode_dir>
```

该命令只开启严格验证，不会自动把任何 review 标记为 passed。

## 7. 验收

原 Story OS：

```bash
python episodes/_system/validate_episode.py <episode_dir>
python episodes/_system/validate_episode.py <episode_dir> --target VISUAL_CALIBRATED
python episodes/_system/validate_episode.py --all --metadata-only
```

机器证据：

```bash
python episodes/_system/machine_gate.py <episode_dir> --target VISUAL_CALIBRATED
python episodes/_system/machine_gate.py <episode_dir> --target PRODUCTION_PASSED
python episodes/_system/machine_gate.py --all --metadata-only
```

本地正式推进不要使用 `--metadata-only`。

## 8. 边界

机器门禁可以判断“证据是否齐、图片尺寸/数量/hash 是否正确、硬失败字段是否存在”，但不能替代人工/多模态判断：

- 是否真实像手机相册
- 是否有继续滑动欲望
- 人物是否像同一个人
- 高潮是否真正够强
- 结尾是否产生回看价值

这些仍必须按主规范人工终审。机器只负责：**人工已经做过判断后，不允许证据缺失、状态漂移或返工越界。**

<!-- STORY_OS_V1_7_RELIABILITY_BEGIN -->
## Story OS V1.7 — Production Reliability

V1.7 不新增 episode stage，只增加生产可靠性证据与文字专修事务：

- `episodes/_system/transport_guard.py`：技术重试请求指纹锁、失败分类、熔断；技术失败不计内容返修。
- `episodes/_system/text_audit.py`：字幕硬项 + AI 腔警告，只审计不自动改稿。
- `episodes/_system/text_revision.py`：文字专修 backup → diff → audit → submit → approve/revert；锁定图片/reference/manifest/state 不得变化。
- `meta/transport-state.json` 与 `meta/text-revisions/` 都是证据/事务，不是第二状态机。

常用入口：

```bash
python episodes/_system/story_os.py transport <episode_dir> preflight <frame>
python episodes/_system/story_os.py audit-text <episode_dir> --file <subtitles.yaml>
python episodes/_system/story_os.py text-revision <episode_dir> start --file <path>
```

详细执行见 `standards/生产可靠性与文本事务规范_V1.0.md`。
<!-- STORY_OS_V1_7_RELIABILITY_END -->

<!-- STORY_OS_V1_8_EVIDENCE_BEGIN -->
## Story OS V1.8 — Default Visual IP + Evidence Locks

- 用户未指定画风/质感：默认 `M00｜现实生活纪实母版`；MP4、网吧、流水席、误入小镇仅作为校准来源。
- 显式单集/系列风格可覆盖默认 M00；年代/设备物理真实性永远高于母风格“复古感”。
- Story Lock 必须保存 story + storyboard 的明确批准和 SHA-256。
- Visual Lock 必须保存 visual spec、校准联系表、已通过 reference 与解析后 visual profile 的明确批准和 SHA-256。
- `PUBLISH_READY` 前必须有最新 `meta/text-audit.json`，且其 `source_sha256` 等于当前 captions。
- `PUBLISH_READY` 前必须有用户明确批准的 `meta/release-package.json`，最终封面/正文/字幕/发布文案/传播卡 hash 全部一致。
- V1.7 的 transport guard / text revision transaction 原样保留，不重复造轮子。
<!-- STORY_OS_V1_8_EVIDENCE_END -->

<!-- STORY_OS_V2_MULTI_RUNTIME_SKILL_BEGIN -->
## Story OS V2.0 Multi-Runtime Execution

- CODEX：文件原生全自动生产，目标 approved/publish/SHA/FINAL ZIP。
- WORK：持久工作区长任务，目标一次任务尽量做到最终交付。
- WEB：尽量连续执行；产品工具边界出现时写 checkpoint，下一轮直接恢复。

用户已明确授权“全自动”时，不在正常 Story/Visual/Repair/Release 节点重复询问“是否继续”；只在硬冲突、权限/安全确认、一次内容返修后仍失败等情况暂停。
<!-- STORY_OS_V2_MULTI_RUNTIME_SKILL_END -->

<!-- STORY_OS_V2_0_1_SKILL_BEGIN -->
## Story OS V2.0.1 — Executable CODEX Production

CODEX runtime 提供机器可执行入口 `story_os.py run <episode> --full-auto`，并提供基于当前 Codex ChatGPT 登录态的单图 backend `codex_subscription_image.py`。这两者只补执行能力，不建立第二状态机、不改变主规范、不伪造人工批准。
<!-- STORY_OS_V2_0_1_SKILL_END -->

<!-- STORY_OS_V2_0_2_SKILL_BEGIN -->
## Story OS V2.0.2 Production Closure

Full-auto pipeline: `worker → deterministic postflight → COMPLETE|PAUSED|BLOCKED`。图片链路必须 `raw → normalize → exact ledger canvas`。全自动批准使用 delegated provenance，不伪装 direct user review；最终 ZIP 必须通过 delegated delivery verify。
<!-- STORY_OS_V2_0_2_SKILL_END -->


## V2.0.3.3 Frame Semantic Enforcement

- `actual_frame_semantic_review`：独立 Critic 审实际最终图片，而不是 prompt。
- `sha_bound_frame_reviews`：每帧 review 必须绑定当前 approved asset SHA。
- `release_evidence_closure`：Release 前再次执行 Production semantic preflight，交付包携带 frame review / audit。
- recovered/locked 资产没有当前 SHA 的 schema 2 review 时不得继承 PASS。
- 不新增第八状态。


<!-- STORY_OS_V2_0_3_5_RELEASE_GUARD_BEGIN -->
## Story OS V2.0.3.5 — Release Guard

不新增 episode stage。新增四个发布前 P0 硬证据：

- `meta/recent5-review.json`：真实最近 5 篇 fingerprint + registry SHA 绑定，禁止只写 `recent5_checked=true`。
- `<series>/meta/series-lock.json` + `meta/series-lock-binding.json`：连续世界观跨集 anchor SHA。
- `meta/release-semantic-review.json`：fresh isolated critic 审最终 cover/title/01-03/climax/payoff/description。
- `meta/publish-compliance.json`：AI 内容声明计划 + 虚构上下文治理证据。

旧 V2.0.3.4 episode 默认兼容；V2.0.3.5 新篇或显式 `release_preflight.py enable` 的剧集启用。
<!-- STORY_OS_V2_0_3_5_RELEASE_GUARD_END -->


<!-- STORY_OS_V2_0_3_5_1_SERIES_DETECTION_HOTFIX -->
## V2.0.3.5.1 Series Detection Hotfix

- **禁止通过目录兄弟 episode 数量推断连续世界观。**
- 栏目/题材分类默认不是连续系列。
- 只有 `<series>/meta/series-lock.json` 已存在，或 `<series>/meta/series-continuity.json` 显式 `enabled=true`，才启用 Series Lock。
- 连续系列可先执行 `release_preflight.py declare-series`；`init-series-lock` 会自动写入声明。


<!-- STORY_OS_V2_0_3_6_SEMANTIC_RECENT5 -->
## V2.0.3.6 Semantic Recent-5

- Recent-5 不再只认 fingerprint 字符串完全相等。
- V2.0.3.6 新篇必须生成 fresh isolated `meta/recent5-semantic-review.json`。
- critic 只判断九维是否语义等价，不得自行给数值分。
- Python 固定计算 `effective=max(exact, semantic)`，veto 固定为 exact OR semantic。
- semantic evidence 绑定 fingerprint SHA、registry SHA、历史 episode IDs、critic log SHA。
- V2.0.3.5.1 及更早 episode 保持兼容。

<!-- STORY_OS_RUNTIME_DAG_REFACTOR_CORE_BEGIN -->
## Runtime DAG Refactor
绑定 Runtime Request 的新篇默认使用 Runtime DAG：Creative Story → Visual Lock → Production → Release。每步完成立即落 checkpoint；恢复时验证后复用。DAG 不建立第二 stage。图片采用 continuous max3 调度；Scoped Worker 优先用 Execution Capsule；Prompt Package / Rolling Review / Provisional Release 都是派生执行优化，不替代正式 Gate。图片 pool 只复用 Python worker，不复用 Codex 跨帧上下文。
<!-- STORY_OS_RUNTIME_DAG_REFACTOR_CORE_END -->

<!-- STORY_OS_CHARACTER_ENTRY_POOL_CORE_BEGIN -->
## Character / Entry Pool
新篇 Concept 前先准备 Character Contract：优先普通二十来岁青年/朋友团，以旅行、返乡、聚会、挑战、废弃场所、户外、生活化工作/科考等日常理由进入异常；默认禁用抢修/维修/警察/记者/调查员等功能型主角。第一人称也锁人物锚点。Story Lock 前 NO-ANOMALY TEST 必须 PASS，随后 Character Contract 绑定进 Frame Contract。
<!-- STORY_OS_CHARACTER_ENTRY_POOL_CORE_END -->

<!-- STORY_OS_RUNTIME_OPTIMIZATION_R2_CORE_BEGIN -->
## Runtime Optimization R2
支持 `preproduction_only`（只做生图前资产并写 Handoff）和 `image_continue`（校验 Handoff 后从 Visual/Image 继续，禁止重写 Story）。启用 `.storyos_cache/` 多级缓存、`library/` 共享参考资源库、Visual Lock 1+3、简介四类开头策略和“标题仅1个内部候选”规则。正式 Story/Visual/Production/Release Gate 均不删除。
<!-- STORY_OS_RUNTIME_OPTIMIZATION_R2_CORE_END -->

<!-- STORY_OS_V230_AGENT_RUNTIME_BEGIN -->
## Story OS V2.3 Agent Runtime

执行链：
`Raw Request → Intent Resolver → immutable Runtime Request → Request Router → Workflow DAG → Tool/Model Execution → Trace/Evidence`

- `meta/episode-state.json` 仍是唯一阶段状态源。
- `meta/runtime-route.json` 只记录路由决策，不是第二状态机。
- `meta/runtime/trace-events.jsonl` 只记录执行事实，不授予 PASS。
- 当前 GPT-Image-2 桌面通道不假设 exact RAW canvas；记录真实 RAW 尺寸与 Provider Receipt，再由 NP01 安全 Normalize。
<!-- STORY_OS_V230_AGENT_RUNTIME_END -->

<!-- STORY_OS_V240_BATCH_RUNTIME_BEGIN -->
## Story OS V2.4 Batch Image Runtime

正式 Production 默认使用 5 图 Batch Runtime：

`5 Frame Contracts → 1 image_generation call → 5 mapped images → per-frame Receipt/Normalize/Ledger/Review`

- Visual Lock 继续保持 1+3，不走 Batch。
- Provider 首个真实 Batch 同时作为 Capability Probe。
- Batch Transport 失败自动回退现有 single-frame worker。
- Deviation >= 80 且 Criticality >= 80 才允许 High×High 紧急单帧返修。
- 其他内容失败等待 Batch 原始生成完成后进入 Repair Arbiter。
- Batch / Trace / Receipt 都是 Evidence，不改变 `meta/episode-state.json` 唯一阶段权威。
<!-- STORY_OS_V240_BATCH_RUNTIME_END -->

<!-- STORY_OS_V241_IMAGE_PROVIDER_RUNTIME_BEGIN -->
## Story OS V2.4.1 Image Provider Runtime

Production Batch 先读取 `config/providers/image-provider-runtime.json`：

- 存在 `OPENAI_API_KEY`：优先 OpenAI Image API，GPT-Image-2 可用 `n=5`（上限10）执行 native multi-image。
- 无 API Key 或 API transport 失败：保持 Codex Subscription fallback。
- API Key / Authorization Header 禁止写入任何仓库文件或 Episode Evidence。
- `output_index -> Frame` 是 Story OS 映射约定，不是 Provider 创作权威，仍必须逐帧 Review。
- 4:5 API 请求使用 1088×1360，9:16 使用 1152×2048，之后无裁切 Normalize 到正式 Release Canvas。
<!-- STORY_OS_V241_IMAGE_PROVIDER_RUNTIME_END -->

<!-- STORY_OS_V242_CODEX_SUBSCRIPTION_BATCH_BEGIN -->
## Story OS V2.4.2 Codex Subscription Batch Runtime

没有 `OPENAI_API_KEY` 时，Production Batch 正式走：

`1 Story OS Batch -> 5 isolated Codex image workers in parallel`

这是 Logical Batch，不是 Provider-native `n=5`：

- `logical_batch=true`
- `native_multi_image=false`
- `single_http_request=false`
- 不需要 API Key，使用本机 ChatGPT/Codex 登录态
- 默认最多 5 个 Codex 图片 worker 同时在途
- 无 API Key 时全局只允许 1 个 Logical Batch 在途，避免 2×5=10 个图片调用
- 技术失败自适应 5→3→1，只重试失败帧
- 成功帧永不因为同批其他帧技术失败而重生
- Fast Scout 延迟到 5 帧原始生成 barrier terminal 后再执行
<!-- STORY_OS_V242_CODEX_SUBSCRIPTION_BATCH_END -->

<!-- STORY_OS_V2_5_1_RUNTIME_FAST_PATH_BEGIN -->
## V2.5.1 Runtime Fast Path

恢复/新上下文先执行：`python episodes/_system/story_os.py fast-path prepare <episode>`。优先读 `meta/runtime/resume-capsule.json` 与当前 step Execution Capsule；只在 source SHA 漂移、缺字段或 Gate 报 drift 时才广泛重读仓库。未显式验证像素视觉能力的 Rolling Reviewer 只能 `UNCERTAIN → Final Review`，不得 `REPAIR_NOW`。主会话每次再次生成原始候选前必须先 claim Raw Candidate Budget；默认同一 original/repair/exception 最多 2 次，技术失败不计。
<!-- STORY_OS_V2_5_1_RUNTIME_FAST_PATH_END -->

<!-- STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE_BEGIN -->
## V2.5.1.1 Forced Candidate Gate
正式生图入口自动执行 Raw Candidate Budget；技术失败释放预算；同一 Queue Item 技术重试复用 token；候选额度耗尽后硬停止内容生图循环。
<!-- STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE_END -->

<!-- STORY_OS_V2_6_0_PERFORMANCE_RUNTIME_BEGIN -->
## V2.6.0 Performance Runtime / Cross-Shell Contract

性能优先，但不降低创作门禁。恢复优先使用 Resume Capsule；正式图片候选走原子 Candidate Lifecycle。
禁止 Agent 使用 Bash heredoc、PowerShell here-string、嵌套 `powershell -Command`、`shell=True` 或把大段 JSON/多行 Python 塞进 shell。
多行/结构化内容必须走 UTF-8 文件、stdin 或仓库 file edit/write API；路径作为 argv 元素传递，不手工拼引号。
Final Visual Freeze 只绑定视觉 SHA，Caption 变化只触发 Caption ↔ Image Audit，不得重新拉起全量 Visual Critic。
<!-- STORY_OS_V2_6_0_PERFORMANCE_RUNTIME_END -->
