# Dali Cat Story OS — Repository Execution Contract V2.0

> 这是 `aigc-dali-cat/story` 的 Agent 执行入口，不是第二套创作规范。
> **创作规则冲突时，以 `standards/制作规范_正式版.md` 为唯一权威。**
> **机器阶段冲突时，以 `meta/episode-state.json` 为唯一状态事实源。**

<!-- STORY_OS_V1_6_GOLDEN_PATH_BEGIN -->
## Story OS V2.0 Golden Path

**第一入口：先读 `START_HERE.md`。** 该文件只负责路由，不建立第二套创作规范。

Golden Path：`选题/去同质化 → Story Lock → 真实性卡/连续性锚点 → 三张校准+四张视觉准入 → Visual Lock → Batch → 逐帧审核/必要返修 → Final Checklist → Release → 数据回填`。

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

按以下顺序：

1. `START_HERE.md`
2. `README.md`
2. `AGENTS.md`
3. `standards/制作规范_正式版.md`
4. 与任务相关的从属细则：
   - `standards/抖音推流评分与发布后漏斗规范_V1.4.md`
   - `standards/真实性与共享风格锚点规范_V1.1.md`
   - `standards/字幕人话化与声音卡规范_V1.1.md`
   - `standards/最终字幕视觉规范_V1.1.md`
   - `standards/生产引擎与画幅规范_V1.2.md`
5. 目标剧集 README / docs / 已锁分镜
6. 若存在 `meta/episode-state.json`，同时读取三个核心 meta 文件；若 `machine_contract.strict=true`，还必须读取 production ledger 与 frame reviews。

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

V1.5 正向推进会依次执行：

1. `validate_episode.py`：原 Story OS / manifest 门禁；
2. `machine_gate.py`：真实性、校准、参考资产、逐帧结构化审查、production ledger 硬门禁。

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
- 三张校准必须分别为：普通相册基线 / 最差但成立条件 / 首次重大异常
- 三张校准必须是三个不同图号，且属于四张视觉准入帧
- 三张校准资产和联系表必须保存 SHA-256 并保持不变
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

# 锁三张校准
python episodes/_system/evidence_tool.py record-calibration <episode_dir> --role baseline --frame 01 --asset <01.png> --decision passed
python episodes/_system/evidence_tool.py record-calibration <episode_dir> --role worst_condition --frame 10 --asset <10.png> --decision passed
python episodes/_system/evidence_tool.py record-calibration <episode_dir> --role first_major_anomaly --frame 04 --asset <04.png> --decision passed

# 生成三张校准联系表并写回 hash
python episodes/_system/calibration_sheet.py <episode_dir>

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

- 用户未指定画风/质感：默认 `M00｜MP4 × 网吧 × 流水席旧数码质感校准版`。
- 显式单集/系列风格可覆盖默认 M00；年代/设备物理真实性永远高于母风格“复古感”。
- Story Lock 必须保存 story + storyboard 的明确批准和 SHA-256。
- Visual Lock 必须保存 visual spec、校准联系表、已通过 reference 与解析后 visual profile 的明确批准和 SHA-256。
- `PUBLISH_READY` 前必须有最新 `meta/text-audit.json`，且其 `source_sha256` 等于当前 captions。
- `PUBLISH_READY` 前必须有用户明确批准的 `meta/release-package.json`，最终封面/正文/字幕/发布文案/传播卡 hash 全部一致。
- V1.7 的 transport guard / text revision transaction 原样保留，不重复造轮子。
<!-- STORY_OS_V1_8_EVIDENCE_END -->

<!-- STORY_OS_V2_0_EXEC -->
## Story OS V2.0 — Full Auto Delivery
`locked source → auto plan → calibration → visual admission → batch → vision review → one repair max → captions → checksum → delivery ZIP`
自动生产是证据/编排层，不是第二状态机。
<!-- /STORY_OS_V2_0_EXEC -->
