# 项目协作规则（Codex 自动读取）

## Story OS 当前执行入口

涉及 `story` 分支的选题、分镜、出图、字幕、审核、发布、复盘任务，Codex 必须先读取仓库根目录 `START_HERE.md`，再读取 `SKILL.md`。

每次流程先读取并校验 `config/storyos.yaml`，再按 `config/index.yaml` 的最小读取集工作。当前产品版本仍从 `story_os_manifest.json` 读取；不要在 Agent 入口另维护一份版本号。

- `AGENTS.md`：Codex 自动入口与仓库协作规则。
- `SKILL.md`：Story OS 执行协议。
- `standards/制作规范_正式版.md`：唯一创作规范权威。
- `meta/episode-state.json`：唯一机器阶段事实源。
- `meta/story-gates.json`：门禁证据，不保存 stage，不得成为第二状态机。


唯一权威规范：[standards/制作规范_正式版.md](standards/制作规范_正式版.md)

传播评分与发布后数据诊断按 [standards/抖音推流评分与发布后漏斗规范_V1.4.md](standards/抖音推流评分与发布后漏斗规范_V1.4.md) 执行；该文件仅解释主规范 8.4/8.5/12.4/12.5，不建立第二权威，冲突时以主规范为准。V1.3 新增发布时间分层实验与 1h 冷启动快照：1h 仅用于时间实验，不替代主规范正式 6h/24h/48h/7d 验收窗口。

生产真实性、共享画风和字幕人话化按以下从属执行细则：
- [standards/风格锚点_MP4_网吧_流水席_旧数码_V1.2.md](standards/风格锚点_MP4_网吧_流水席_旧数码_V1.2.md)
- [standards/真实性与共享风格锚点规范_V1.1.md](standards/真实性与共享风格锚点规范_V1.1.md)
- [standards/字幕人话化与声音卡规范_V1.1.md](standards/字幕人话化与声音卡规范_V1.1.md)
- [standards/生产引擎与画幅规范_V1.2.md](standards/生产引擎与画幅规范_V1.2.md)

这些从属细则均不建立第二权威；冲突时以 `standards/制作规范_正式版.md` 为准。M00「现实生活纪实母版」在用户未指定时默认启用；MP4、网吧、流水席、误入小镇只作为校准来源。显式视觉体系可覆盖，且年代/采集设备物理真实性永远高于母风格质感。


<!-- STORY_OS_RUNTIME_REQUEST_P0_AGENTS_BEGIN -->
## Runtime Request P0｜一句话入口

涉及新篇全自动任务时，Codex 必须先把用户自然语言编译/记录为 Runtime Request，再进入 Story OS 创作流程。Runtime Request 只表示“用户要什么、怎么执行”，不得提前决定高潮帧、impact、天气或 Visual Lock 帧。

标准规则：

- 用户不传剧情：`auto_create`。不得反问用户补剧情；必须由 Story OS 自己发散候选、通过 Concept Ambition、写完整 Story。
- 用户说“剧情大概是…”：`user_seed`。必须强化和重写，禁止把用户原文直接拆成 20 张。
- 用户说“必须保留/结尾必须”：`core_constraints`。硬约束必须保留，其他结构允许优化。
- 只有用户明确说“剧情已经定了/不要改剧情”才使用 `locked_story`。
- 用户不写 image：默认 `image_model=gpt-image-2`、`image_quality=high`；正式生产不得静默降级 Quality。
- 用户显式指定 image：强绑定，禁止静默替换。
- 当前 V2.1 Visual Lock 永远按 4 张口径执行；“3 张校准”只允许出现在明确 legacy-only 的兼容代码/历史说明中。

请求可先写入 `runtime/requests/<request_id>.json`，Episode 创建后绑定到 `<episode>/meta/runtime-request.json`。绑定后的请求默认不可变；执行状态写 checkpoint/observability，不回写 Request。
<!-- STORY_OS_RUNTIME_REQUEST_P0_AGENTS_END -->

<!-- STORY_OS_RUNTIME_DAG_REFACTOR_AGENTS_BEGIN -->
## Runtime DAG / Resume / Quota

- 新篇有 `meta/runtime-request.json` 且 `runtime.execution_mode=dag` 时，优先由 `runtime_dag.py` 分段调度，不再默认启动单个全程大 Codex supervisor。
- Runtime DAG 不是第二状态机；每个 Step 最终仍必须通过 canonical `episode-state.json` + validate/machine/evidence gates。
- 中断恢复先验证已经到达的目标阶段；证据有效则 REUSED，不为“保险”重做昂贵 Step。
- 图片 worker pool 只复用 Python 进程/模块，不复用跨帧 Codex 对话上下文。
- Quota observability 仅记录真实日志计数或用户明确提供的 `/status` 百分比，不允许推测 Plus 剩余额度。
<!-- STORY_OS_RUNTIME_DAG_REFACTOR_AGENTS_END -->

<!-- STORY_OS_RUNTIME_PERFORMANCE_PACK_AGENTS_BEGIN -->
## Runtime Performance Pack

- Image Scheduler 使用 continuous first-completed 调度，但 image max workers 仍是 3，Ledger 仍单写。
- Scoped Codex 优先使用 `meta/runtime/execution-capsules/*.json`；Capsule 是 derived cache，冲突时源规范优先。
- 高风险 rolling review 只能输出 PASS_PREVIEW / REPAIR_NOW / UNCERTAIN；PASS_PREVIEW 永远不是最终通过。
- Prompt Package 是 derived cache，Frame Contract/scene SHA 漂移时必须重新编译。
- Provisional Release 只能写 runtime 临时草稿，不得改 release-manifest / snapshot / stage。
<!-- STORY_OS_RUNTIME_PERFORMANCE_PACK_AGENTS_END -->

<!-- STORY_OS_CHARACTER_ENTRY_POOL_AGENTS_BEGIN -->
## Character / Entry Pool

- CREATIVE_STORY 前准备 `meta/character-contract.json`；它是 Story Build Input Contract，不是新 Stage。
- 默认主角从 2004–2010 或 2020年代二十来岁普通青年池选择，可单人、两人、4–5人朋友团。
- 第一人称 POV 也必须固定人物锚点；小团体固定 P01/P02...、年龄、性别、衣着。
- 进入异常优先旅行、返乡、聚会、喝酒/游戏、挑战、废弃场所、户外、自驾、生活化工作/课题/科考、偶然绕路。
- 抢修员、电工、维修工、警察、记者、调查员、专业探灵人、秘密异常研究人员不得作为默认主角发动机。
- 工作/科考只能解释“为什么来到这里”，不能让专业技能成为解决异常的剧情捷径。
- Story Lock 前 Character Contract 必须 LOCKED，NO-ANOMALY TEST PASS，ORDINARY_PERSON_SCORE >= 75。
- Character Contract 绑定 Resolved Frame Contract；后续生图不得随意漂移人物。
<!-- STORY_OS_CHARACTER_ENTRY_POOL_AGENTS_END -->

<!-- STORY_OS_RUNTIME_OPTIMIZATION_R2_AGENTS_BEGIN -->
## Runtime Optimization R2

- `preproduction_only`：完成全部非图片前期资产并生成 `meta/preproduction-handoff.json`；禁止调用 image_generation。
- `image_continue`：先校验 Handoff Authority SHA；Story/Storyboard/Character 为冻结权威，禁止重写；Derived Cache 可重建。切换模式写 `meta/runtime-execution.json`，不得覆盖 immutable runtime-request。
- Shared Resource Library 只复用参考/描述，不默认复用旧集最终成片。
- Visual Lock 使用 1+3：baseline PASS 后，worst/first anomaly/high-impact 才可并行。
- RELEASE 必须先 resolve intro policy；四类开头是结构参考，不是机械模板。
- 标题只生成 1 个内部候选；不作为 PUBLISH_READY 必填项。
- `.storyos_cache/` 为本地全局缓存，不入 Git，不是权威资产。
<!-- STORY_OS_RUNTIME_OPTIMIZATION_R2_AGENTS_END -->

## V2.0 Multi-Runtime 执行路由

涉及 story 分支任务时，先读 `config/storyos.yaml` 和 `config/index.yaml`，再读 `START_HERE.md`，并按索引指向的 Runtime Contract 自动路由，不让用户手工选 runtime。

- 可写仓库文件系统 + terminal/code execution：`runtimes/CODEX.md`
- ChatGPT Work：`runtimes/WORK.md`
- 普通 ChatGPT Web：`runtimes/WEB.md`

Codex 不再被全局限制为“只能生成网页交接单”。当前 Codex 原生工具能生成/编辑图片和保存文件时，应直接按 CODEX runtime 执行；缺媒体能力时才降级 checkpoint/handoff。

全自动授权后：当前 V2.1 统一先完成 4 张 Visual Lock（ordinary baseline / worst condition / first anomaly / high-impact admission），再进入 Batch；每帧最多一次内容返修；已通过且 SHA 未漂移资产必须复用；自动审查不得冒充用户亲眼审核。

<!-- STORY_OS_V2_1_AGENTS_BEGIN -->
## V2.1 Concept Ambition / Image-first

V2.1 新篇不得直接从一个稳妥题目开始写完整故事。先生成 8–12 个候选；不因现实不存在、异常太大或世界规则太怪而提前降级；每个候选先定义 Cover/Mid/Climax；至少 3 个候选进入 A4/A5；运行独立 `concept_ambition.py run-critic`，只允许基于 Concept Voltage ≥80 且无字测试全 PASS 的 selected_id 进入 Story/Storyboard。旧 2.0.x Episode 不追溯补造该 evidence。
<!-- STORY_OS_V2_1_AGENTS_END -->

<!-- STORY_OS_V2_1_PHASE3_AGENTS_BEGIN -->
## V2.1 Phase 3 Environment / Anomaly Impact

Story Lock 后先完成环境合同与逐帧 impact 设计，再进入 Visual Lock。天气不得滤镜化；高冲击异常不得只靠字幕说“更大”，必须在像素中通过尺度参照和前后级差成立。
<!-- STORY_OS_V2_1_PHASE3_AGENTS_END -->

<!-- STORY_OS_V2_1_PHASE4_AGENTS_BEGIN -->
## V2.1 Phase 4 Resolved Frame Contract

Environment / Impact Contract 通过后先编译全部 Frame Contracts，再进入 Visual Lock 校准。正式生图不得只依赖临时 scene prompt；scene prompt 与 Resolved Frame Contract 分层存在，后者是当次生产的完整机器合同。若合同 SHA 漂移，旧 generation attempt 不得直接冒充当前合同。
<!-- STORY_OS_V2_1_PHASE4_AGENTS_END -->

<!-- STORY_OS_V2_1_PHASE56_AGENTS_BEGIN -->
## V2.1 Phase 5/6 Execution

Visual Lock 不再只看三张“风格图”：先 baseline，随后 worst condition / first anomaly / high-impact admission 三张可并行，最后统一 Critic。正式 Batch 不允许手工连续调用 image backend 形成隐式串行，应建立 production queue 并由 `image_scheduler.py run --max-workers 3` 执行。Scheduler 返回 PARTIAL 时先处理/重试技术失败，不得把缺帧当 PASS。
<!-- STORY_OS_V2_1_PHASE56_AGENTS_END -->

<!-- STORY_OS_V2_1_PHASE78_AGENTS_BEGIN -->
## V2.1 Phase 7/8 Execution

在 Visual Lock 前启用 Fast Scout，使 Scheduler 对高风险生成结果并行做早期像素 triage；REPAIR_NOW 只影响该帧与依赖链。不要把 PASS_FAST 写成正式通过。Release 完成 release_preflight 后必须 build+verify Final Candidate Snapshot，再记录 release_lock/推进 PUBLISH_READY。Delivery 只能消费 verified Snapshot。
<!-- STORY_OS_V2_1_PHASE78_AGENTS_END -->

<!-- STORY_OS_V2_1_PHASE910_AGENTS_BEGIN -->
## V2.1 Phase 9/10 Closure

新故事开题前先 `account_learning_index.py rebuild --limit 5`，只把账号历史数据当 evidence。真实发布后用 `post_publish_review.py mark-published` 推进 PUBLISHED；之后按实际后台数据 record 6h/24h/48h/7d。48h 后 `complete` 才可推进 DATA_REVIEWED。不要改冻结的 release-manifest，也不要手写假数据。
<!-- STORY_OS_V2_1_PHASE910_AGENTS_END -->

## Episodes 机器状态与发布清单

> 当前 Story OS：`episode-state.json` 仍是唯一阶段事实源；`story-gates.json` 只记录故事/视觉/字幕/锁图门禁证据，不得保存或覆盖 stage。

1. 新建具体剧集时，按 [`episodes/_system/README.md`](episodes/_system/README.md) 初始化 `meta/episode-state.json`、`meta/release-manifest.json` 与 `meta/story-gates.json`；历史剧集不批量伪造状态，只在重新进入制作/发布/复盘时迁移。
2. 机器状态固定为：`IDEA_LOCKED → STORYBOARD_LOCKED → VISUAL_CALIBRATED → PRODUCTION_PASSED → PUBLISH_READY → PUBLISHED → DATA_REVIEWED`。
3. `episode-state.json` 是阶段事实源；README 的状态文案与其冲突时必须修 README，不得反过来只改机器状态来迁就旧文案。
4. 正向推进必须使用 `episodes/_system/episode_state.py transition`，只能相邻前进。脚本会先用 `validate_episode.py --target` 验收目标门禁，失败时不得手工越级修改 JSON。
5. `release-manifest.json` 只记录实际发布版本事实，不替代分镜、制作规范或数据报告；路径统一使用仓库根目录相对路径。
6. `PUBLISH_READY` 前必须完成制作门禁与九项传播卡，并写明 `publish_decision=go`；`conditional/not_recommended` 若仍发布必须填写 `decision_note`。
7. 发布图可继续被 `.gitignore` 排除；完整张数/封面存在性校验在本地工作区执行。只检查 Git 元数据时才使用 `--metadata-only`。

## 提交规则

1. 允许提交 git 的图片/大文件仅限以下两类：
   - 角色参考图：`episodes/**/assets/characters/`
   - 竞品与账号截图：`research/competitors/`、`research/account/`
2. 其他图片、视频、音频、压缩包一律禁止提交，已由 `.gitignore` 默认忽略，包括：
   - 各集 `images/`、`publish/` 成片
   - `assets/` 下 frames、subtitled、references、shenshi、materials 等中间资产
   - 发布包 zip、`workbench/` 中间处理资产、`.playwright-cli/` 截图
3. 新增大文件前先 `git status` 确认只出现白名单文件；可用 `git check-ignore <文件>` 验证是否被忽略。
4. 已误提交的非白名单文件用 `git rm --cached` 移出索引（保留本地），不要删本地文件。

<!-- STORY_OS_V1_8_AGENTS_BEGIN -->
## V1.8 默认视觉路由

Codex 若未收到用户明确画风/质感指令，必须先解析 `M00 / 现实生活纪实母版`，再按本集真实性卡决定实际设备表现。MP4、网吧、流水席、误入小镇只是校准来源；不得把“默认 M00”误解成“所有作品都必须旧低清”。

当前推进统一调用稳定外部名 `evidence_gate.py`；`v18_gate.py` 只保留为历史兼容实现。Story/Visual Approval provenance、最新 Text Audit 与 Release 证据都不得漂移。
<!-- STORY_OS_V1_8_AGENTS_END -->

<!-- STORY_OS_V2_0_1_AGENTS_BEGIN -->
## V2.0.1 Codex 可执行全自动

在 CODEX runtime 且用户明确要求“全自动执行 / 做到最终交付”时，优先使用 `python episodes/_system/story_os.py run <episode_dir> --full-auto` 或遵循同等底层流程。不要再把 CODEX runtime 降级成只写交接提示词。

自动返修必须记录为 `delegated_auto_review`；正式 Story/Visual/Release 的 `user_approved` 只能来自真实直接批准。外部证据门禁统一调用 `evidence_gate.py`。
<!-- STORY_OS_V2_0_1_AGENTS_END -->

<!-- STORY_OS_V2_0_2_AGENTS_BEGIN -->
## V2.0.2 Production Closure

- `story_os.py run --full-auto` 的成功条件是 postflight COMPLETE，不是 Codex worker rc=0。
- 正式图片用 `codex_subscription_image.py generate-for-frame`；raw 与 exact-canvas candidate 分离。
- full-auto self review 后用 `delegated_approval.py record` 锁 Story/Visual；不得伪造 `--user-approved`。
- Evidence Gate 接受 direct_user_review 或已授权的 delegated_auto_review。
- delegated delivery 只接受真实 publish 资产，禁止 approved fallback。
<!-- STORY_OS_V2_0_2_AGENTS_END -->
<!-- STORY_OS_V2_0_3_4_AGENTS_BEGIN -->
## V2.0.3.4 Incremental Workspace

- 全自动执行前先运行 `incremental_closure.py plan`；已有有效 SHA-bound PASS 证据不得无条件重跑。
- Production 结束后使用 `incremental_frame_review.py review`，由它自动选择 NOOP / PATCH / FULL。
- PATCH 只看 dirty roots + 必要邻帧；Story/Storyboard/Visual Contract 漂移或 dirty >25% 自动 FULL。
- 新生产媒体必须写入 `<episode>/media/`；交付写入 `<episode>/release/`。图片/视频/ZIP 保留本地，Git 只保存路径与 SHA 索引。
- 不得删除被 `.gitignore` 忽略的旧媒体来“整理目录”；迁移必须通过 `media_workspace.py` 的 copy→SHA verify→reference rewrite→remove-old 流程。
<!-- STORY_OS_V2_0_3_4_AGENTS_END -->

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
