# Story OS Visual Profile Governance V1.0

> 状态：设计规范（Design Only，本阶段不实现）
> 范围：Story OS 多视觉体系（多世界/多年代）扩展治理
> 本阶段不修改 Runtime、生产代码、Gate，不影响当前生产，不提交 git
> 权威关系：本文档是 `standards/制作规范_正式版.md` 的下位设计规范，不建立第二创作权威；冲突时以主规范为准

---

## 0. 术语与当前实现审计

### 0.1 当前实际存在的视觉机制（不是一层，是五层）

任务背景假设"当前只有 M00 一个画风"。审计后的事实是：Story OS 已经把视觉拆成五个独立层，只是缺少统一的 Profile 治理。

| 层 | 负责 | 资产 | 解析/编译 | 权威边界 |
| --- | --- | --- | --- | --- |
| 设备物理层 Capture Profile | 某台设备的动态范围、弱光、对焦、白平衡、压缩、边缘行为 | `standards/capture_profiles/CP01..CP08` + `index.json` | `capture_profile.py`（validate/list/show） | 设备物理真实性优先于母风格质感 |
| 相机作者层 Capture Grammar | 谁在拍、视点、站位、是否摆拍、构图缺陷、禁止幽灵机位 | `standards/capture_grammars/FIRST_PERSON_CASUAL_SNAPSHOT_V1.json` | `capture_grammar_v228.py` | 相机作者性高于 Visual Profile 的构图/摄影提示 |
| 序列层 Sequence Grammar | 摄影者配比、开篇记忆、镜头族多样性、跨帧连续性、屏幕内容物理 | `standards/sequence_grammars/SG01_personal_evidence_sequence.json` | `sequence_grammar.py` | 多帧节奏与连续性 |
| 质感/年代层 Visual Profile | 年代、材质、色彩、光线、胶片/数码质感、must_keep、forbidden | `standards/visual_profiles/*.json` | `visual_profile.py` + `visual_profile_bridge_v224.py` | 账号母风格或单集显式锁定 |
| 帧合同层 Resolved Frame Contract | 把上述各层编译成逐帧完整机器合同 | `meta/runtime/contracts/frames/{NN}.json` | `frame_contract.py` | 当次生产的完整合同，缓存不是权威 |

另有 `environment_contract.py` 负责逐帧环境与异常 impact（`story-gates.visual.environment_contract` / `frame_directives`），它是帧级物理上下文，不是画风层。

### 0.2 当前 M00 的实际定义

文件：`standards/visual_profiles/M00_MP4_网吧_流水席_旧数码.json`（`profile_id=M00`，`profile_version=2.0`，`default_when_unspecified=true`）。

- `scope=account_default_visual_mother_style`，即账号级视觉母风格，不是单集画风。
- `principle`：宁可普通一点、乱一点，也不能精致得像广告、电影剧照或 AI 概念图；具体年代与设备物理表现优先。
- `precedence`：显式单集/系列 Profile → Capture 物理与年代 → M00 视觉语言。
- `visual_dna`（30+ 键）已经承载了"真实优先"的关键约束：`reality_first`、`ordinary_chinese_life_density=high`、`people=ordinary_unprepared_not_actor_like`、`cinematic_lighting=forbidden_by_default`、`commercial_hdr=forbidden`、`global_vintage_lut=forbidden`、`scene_cleaning=forbidden_by_default`、`camera_authorship=required`、`ghost_camera=forbidden`、`narrative_information_gain=required_after_frame_01`、`continuity=strict`、`seed_dependency=none`。
- `texture_translation` 区分"旧数码/廉价相机"与"现代手机"两套物理表现，明确 `avoid_fake_old_noise_or_fake_low_resolution`。
- `anti_homogeneity`：锁质感不锁场景，禁止强制复用 CRT / MP4 / 网吧等道具。
- `anchors`：F01 流水席、F02 MP4、F03 误入小镇、F04 网吧（F04 标注 `user_locked_semantic_anchor`，无 source+hash，不伪造哈希）。

关键结论：**M00 不只是"一个画风"，它同时承载了账号级"现实母规范"和一组可继承的基底规则。** 这正是必须做治理而不是加画风的根因。

### 0.3 当前 Profile 解析与覆盖路径

1. `story-gates.json#visual_profile`：`mode=default`（可带 `capture_profile`）或 `mode=override`（必须 `profile_id` + `profile_path` + `override_reason`）。当前检查的活跃集此键多为 `null`，即默认 M00。
2. Episode 级显式锁定：`<episode>/meta/visual-profile.json`。真实样本 `episodes/12_千寻/01_那条不存在的隧道/meta/visual-profile.json` 锁定 `SPIRITED_AWAY_LIVE_ACTION_V1`，带 `profile_sha256`、`lock_status=locked`、`default_m00_applicable=false`、`substitution_allowed=false`、`visual_profile_role[]`、`capture_grammar` 固定、`conflict_resolution`、`authority_sources[]`。
3. 编译：`visual_profile_bridge_v224.compile_prompt_contract()` 合并 Profile（质感/年代）+ Capture Grammar（相机作者性）+ Sequence Grammar，输出 `profile_sha256` 与文本合同；显式声明 `Capture Grammar 对摄影者身份/视点/站位/构图的约束高于 Visual Profile`。
4. 评审：`visual_lock_baseline_gate.py` 的 9 项检查含 `visual_profile_match`，`visual_lock_v21.py` 负责四张 admission 的正式 Visual Lock；`visual_review.py` 按合约版本分派 legacy/ v2.1。

### 0.4 审计发现的治理缺口

| 编号 | 缺口 | 证据 |
| --- | --- | --- |
| G1 | 无 Visual Profile JSON Schema | `standards/schemas/` 只有 `propagation-core.schema.json` 与 `runtime-request.schema.json` |
| G2 | 无 Visual Profile 注册表 | `capture_profiles/` 有 `index.json`；`visual_profiles/` 只有目录 glob，无 index |
| G3 | Profile 命名不统一，且存在无法解析的 Profile id | 同时存在 `M00`、`SPIRITED_AWAY_LIVE_ACTION_V1`；`M00_HEAVEN_WORKER_DAILY_V1` / `M00_ANCIENT_DAILY_LIFE_V1` 在 `standards/visual_profiles/` 中无对应文件 |
| G4 | 存在两套 Profile 解析实现 | `visual_profile_resolver.py`（关键词路由 + 静默回退）已被 `story_creator.py` 接入，与 `visual_profile.py`/`visual_profile_bridge_v224.py`（正式解析链）并存 |
| G5 | 无 Profile 选择策略 | 谁决定用 M01/M02/M03 没有权威判定，只有手工 override |
| G6 | 无账号级视觉人格约束 | 多 Profile 并存时，无"一个账号在不同世界间仍保持一致视觉身份"的规则 |
| G7 | 虚构世界的"纪实真实性"无定义 | 天界等非现实世界，`reality_first` 的真实性基准与"设备从哪来"未定义 |
| G8 | 新创建链路静默回退 Profile | `visual_profile_resolver.resolve_profile()` 未命中时返回默认 profile id，违反"禁止静默替换画风" |

G3/G4 必须在 Phase 2 之前收敛，否则 M01/M02/M03 会各自长出第三、第四套解析器。

### 0.5 零距离证据：一个正在发生的治理缺口

本次审计在当前分支已落地的建集链路（`episodes/_system/story_creator.py` + `episodes/_system/visual_profile_resolver.py`）里，直接观察到缺口已经成型：

1. `episodes/江南卖花姑娘的一天/meta/runtime-request.json` 声明 `"visual_profile": "M00_ANCIENT_DAILY_LIFE_V1"`。
2. 该 id 在 `standards/visual_profiles/` 中**没有对应文件**（目录只有 `M00_MP4_网吧_流水席_旧数码.json` 与 `SPIRITED_AWAY_LIVE_ACTION_V1.json`）。
3. `episodes/_system/story_creator.py` 调用 `visual_profile_resolver.resolve_profile()`；未命中时该函数返回默认 id `M00_MP4_网吧_流水席_旧数码` 且 `source=default`，**不报错**。
4. 同一条链路把结果写进 `runtime-request.json#visual_profile_resolution`，形式上"有解析证据"，实质上发生了静默替换。

这正好验证本文档的立论：**画风扩展若不先做治理，会以"能跑通但语义错误"的形式悄悄落地。** Phase 2/3 必须先收敛此链路，再谈 M01/M02/M03。

附注（同文件邻域，超出本文档范围）：`story_creator.create_episode()` 另写入一份最小 `meta/episode-state.json`，与"`meta/episode-state.json` 为唯一阶段事实源"的既定合同需要单独对齐。

---

## 1. 背景：为什么不能简单增加画风

最直接的做法是"给古代/天界/江南各写一段 prompt"。这会引入四类不可控：

1. **账号视觉人格混乱**：同一账号在 M00 与 M01 之间来回切换时，用户对"这个号长什么样"的预期被打断，关注转化率下降。
2. **用户预期下降**：M00 建立的是"真实生活纪实"预期；一旦某集出现电影布光或海报构图，用户判定为"AI 味/广告"，而不再是同一种真实感。
3. **Prompt 漂移**：prompt 不是合同，无法 SHA 校验、无法 Gate、无法审计。当前 `visual_profile_bridge_v224` 已经用 `profile_sha256` 把画风钉成可验证合同，回到 prompt 是能力倒退。
4. **生产标准不一致**：不同世界若各自定义"什么算合格"，Visual Lock / Frame Contract / Gate 会失去统一判据。

所以扩展必须发生在**合同层**：新增视觉体系 = 新增可解析、可校验、可继承的 Profile 合同，而不是新增一段 prompt。

---

## 2. Visual Profile 模型

### 2.1 目标字段（V1.0 规范字段集）

```yaml
profile_id: M01                        # 唯一标识，见 3.1 编号规范
profile_version: "1.0"                 # profile 自身版本
schema_version: 1                      # 合同 schema 版本
platform_min_version: "2.7.0"          # 最低可解析平台版本

identity:                              # 这个视觉世界是什么
  profile_name: 古代普通人生活纪实
  world: historical_china_ordinary
  era: pre_modern                         # modern / historical / mythic / fictional
  scope: account_immersive_profile        # 账号母版 / 单集显式锁定
  default_when_unspecified: false

capture_philosophy:                    # 为什么这样拍（最高层意图）
  principle: 记录一个普通人的一天，而不是拍一部电视剧
  reality_basis: real_world_ordinary      # real_world_ordinary / fictional_world_mundane
  diegetic_capture_device: ""             # 虚构世界必须显式声明，见 3.6

camera_language:                       # 相机作者性（与 Capture Grammar 分层的衔接位）
  operator: participant_or_companion_inside_event
  viewpoint: first_person_or_companion_eye
  capture_grammar_ref: FIRST_PERSON_CASUAL_SNAPSHOT_V1
  capture_profile_ref: CP03             # 默认设备物理档案

realism_level:                         # 真实度基准
  level: documentary_ordinary           # documentary_ordinary / fictional_mundane / stylized_film
  cinematic_lighting: forbidden_by_default

lighting_rules:                        # 光线来源必须物理成立
  source: practical_and_available_only
  forbidden: [studio_lighting, three_point_setup, beauty_dish]

color_rules:                           # 色彩策略
  strategy: environment_driven_low_to_medium_saturation
  forbidden: [global_vintage_lut, commercial_hdr, heavy_teal_orange]

composition_rules:                     # 构图行为
  strategy: unposed_imperfect_personal_record
  forbidden: [symmetrical_hero_framing, poster_composition, staged_group_lineup]

prohibited_patterns:                   # 该 Profile 的硬禁止清单（可继承 base 后追加）
  - 现代摄影设备入镜
  - 影视棚拍布光
  - 电影剧照式站位

audience_expectation:                  # 用户看到后会预期什么
  expectation: 真实的古代市井日常记录
  break_conditions: [出现现代物件, 出现影视级布光, 人物明显摆拍]

compatible_story_types:                # 适合的选题族
  - historical_ordinary_life
  - folk_craft_and_errands

# 以下为现有资产已使用的字段，V1.0 保留并纳入 schema
visual_dna: { }
texture_translation: { }
must_keep: [ ]
forbidden: [ ]
anti_homogeneity: { lock_texture_not_scene: true, rule: "" }
precedence: [ ]
```

### 2.2 字段语义与权威归属

| 字段组 | 回答的问题 | 谁使用 | 可否被 Episode 覆盖 |
| --- | --- | --- | --- |
| `identity` | 这是哪个世界/年代 | 选择策略、审计 | 否 |
| `capture_philosophy` | 为什么这样拍 | Profile 编译、Gate | 否（只可收窄） |
| `camera_language` | 谁在拍、用什么设备 | Capture Grammar / Capture Profile 衔接 | 否（作者性归 Capture Grammar） |
| `realism_level` | 真实度基准 | Visual Lock、Gate | 否 |
| `lighting_rules` / `color_rules` / `composition_rules` | 具体视觉语言 | 编译进 Frame Contract | 仅可显式覆盖并留 reason |
| `prohibited_patterns` | 硬禁止 | Gate、Critic | 不可删除，只可追加 |
| `audience_expectation` | 用户预期 | 选题与发布判定 | 否 |
| `compatible_story_types` | 适配选题族 | 选择策略 | 否 |

### 2.3 与现有资产的关系

V1.0 字段是**现有 `visual_dna` / `must_keep` / `forbidden` 的结构化上位表达**，不是替换。Phase 2 只做"补齐 + 校验"，不重写已锁定的 `SPIRITED_AWAY_LIVE_ACTION_V1` 与 M00 历史证据，也不改历史 Profile 的 SHA。

---

## 3. Profile 分类

### 3.1 编号规范（先定名，再定内容）

- `M<NN>`：**账号级沉浸式母版**，可跨多集复用，允许作为 `default_when_unspecified`。M00 已占用。
- `<THEME>_<LOOK>_V<n>`：**系列/单集专属视觉体系**，如 `SPIRITED_AWAY_LIVE_ACTION_V1`，通常 `default_when_unspecified=false`。
- 一个视觉世界只允许一个 id；`M00_HEAVEN_WORKER_DAILY_V1`、`M00_ANCIENT_DAILY_LIFE_V1` 这类"M 前缀 + 主题"的混合命名必须收敛为正式编号（见 8. Phase 2）。

### 3.2 M00 现实生活纪实母版（已实现，保持默认）

| 维度 | 定义 |
| --- | --- |
| 定位 | 账号默认视觉母风格；当代普通中国生活 |
| capture philosophy | 手机相册感、第一人称/同行者在场的私人记录、非电影 |
| camera language | `FIRST_PERSON_CASUAL_SNAPSHOT_V1` + CP01 现代手机 |
| realism level | `documentary_ordinary`；`cinematic_lighting=forbidden_by_default` |
| lighting | 可用光/现场光优先 |
| color | 环境驱动、低到中饱和；禁止全局复古 LUT、商业 HDR |
| composition | 非摆拍、生活性缺陷 |
| prohibited | 电影布光、海报感、完美构图、AI 概念图、美化皮肤 |
| audience expectation | "真实生活记录"；一旦精致化即破坏预期 |
| compatible story types | 当代生活、返程/绕路、旧物怪谈、山难纪实等（当前主体） |

M00 的**特殊职责**：它同时是"现实基底规则"的当前承载者（见 4.）。

### 3.3 M01 古代普通人生活纪实

| 维度 | 定义 |
| --- | --- |
| 定位 | 账号级沉浸式母版；古代普通百姓的市井/生计日常 |
| capture philosophy | 一个古代普通人的一天；手持记录感；**非影视古装大片** |
| camera language | 与 M00 同哲学（第一人称/同行者在场随手拍），设备物理改为年代合理的"世界内记录器具"或显式声明 `diegetic_capture_device` |
| realism level | `documentary_ordinary`（就古代世界而言的普通纪实） |
| lighting | 自然光 + 油灯/烛火/天光等年代可用光；禁止影视布光 |
| color | 环境驱动、材质驱动；禁止统一"古风滤镜" |
| composition | 非摆拍；禁止古装剧式的对称/英雄构图 |
| prohibited | 现代摄影设备、影视棚拍、影楼古装写真感、仙侠特效、塑料皮肤 |
| audience expectation | "古代普通人的真实生活" |
| compatible story types | 市井生计、手艺人、赶集、行旅 |

**风险**：M01 与 M03 极易被做成同一种"古风滤镜"。治理要求是——它们共享现实哲学，但必须在 `era`、`environment`、`lighting source`、`wardrobe`、`prohibited` 上写出可区分的差异，否则应合并为一个 Profile 的两种 `environment`。

### 3.4 M02 天界普通工作人员

| 维度 | 定义 |
| --- | --- |
| 定位 | 账号级沉浸式母版；虚构世界（天界）的**普通岗位日常** |
| capture philosophy | 天界的"上班族一天"；第一视角生活体验；**非神话战斗** |
| camera language | 必须显式声明 `diegetic_capture_device`（这个世界用什么记录）与对应 Capture Profile；不得默认套用现代手机物理 |
| realism level | `fictional_mundane`（虚构世界内部的日常真实），不是 `documentary_ordinary` |
| lighting | 由世界规则定义的光源，但必须"物理成立且可解释"；禁止无因果泛光 |
| color | 世界材质驱动；禁止神话电影式的强对比/史诗色调 |
| composition | 普通人视角；禁止英雄登场、神兵大型阵列 |
| prohibited | 神话战斗、史诗大场面、神性光晕滥用、游戏 CG 感 |
| audience expectation | "天界打工人的真实日常" |
| compatible story types | 云务/送信/值守等岗位日常、跨界误会 |

**这是 V1.0 最重要的治理裁决（G7）**：M02 不能简单继承 M00 的 `reality_first` 语义，因为"现实"基准不同。必须新增两个字段：

- `capture_philosophy.reality_basis`：`fictional_world_mundane`，定义"真实"= 该世界内部常识的平民日常，而不是现实世界的物理。
- `capture_philosophy.diegetic_capture_device`：这个世界用什么器具记录，为什么它物理成立（否则会产生"幽灵摄影机"——当前 Capture Grammar 明令禁止）。

### 3.5 M03 江南沉浸式生活

| 维度 | 定义 |
| --- | --- |
| 定位 | 账号级沉浸式母版；江南地域的沉浸式生活记录 |
| capture philosophy | 真实旅行/生活记录感；地域氛围来自环境而非滤镜 |
| camera language | 与 M00 同哲学；设备物理按 `era` 决定 |
| realism level | `documentary_ordinary` |
| lighting | 江南多雨湿气、自然天光；禁止"江南滤镜"式统一调色 |
| color | 湿地/水汽环境驱动；禁止统一青绿 LUT |
| composition | 非摆拍；禁止旅游宣传海报构图 |
| prohibited | 抒情 MV 感、宣传片航拍感、统一江南调色 |
| audience expectation | "江南普通人的真实生活" |
| compatible story types | 水乡日常、茶/卖花/船居等生计 |

**待决**：M03 的 `era` 目前不明确（现代还是古代？）。`episodes/江南卖花姑娘的一天/meta/runtime-request.json` 绑定 `M00_ANCIENT_DAILY_LIFE_V1`，已有链路把"江南"当作古代，但 M03 名称为"沉浸式生活"，语义偏地域而非年代。必须在 Phase 1 明确：**M03 = 地域母版（era 需在实例中声明）**，或**把江南归入 M01 的一个 environment**。命名冲突需在 Phase 2 一并收敛（见 0.5）。

### 3.6 分类小结

| Profile | 哲学 | `reality_basis` | 关键差异字段 |
| --- | --- | --- | --- |
| M00 | 现实纪实 | `real_world_ordinary` | 已实现 |
| M01 | 古代纪实 | `real_world_ordinary`（历史年代） | `era`、`wardrobe`、`lighting source` |
| M02 | 虚构世界日常纪实 | `fictional_world_mundane` | `diegetic_capture_device`、世界光源 |
| M03 | 地域沉浸生活 | `real_world_ordinary` | `environment`、`era`（待定） |

M01 与 M03 是"同一哲学、不同年代/地域"，M02 是"不同真实性基准"。三者的**共同基底仍是 M00 的现实规则**，差异只允许出现在年代/世界/材质/光源/禁止项，不允许出现在"非电影化"这条底线上。

---

## 4. Profile 继承模型

```
Base Visual Reality Rules（账号级不可变底线）
        |  (只能继承，不能被 Profile 反转)
        v
Visual Profile（M00 / M01 / M02 / M03 / THEME_LOOK_Vn）
        |  (可收窄、可追加禁止，不可放宽底线)
        v
Episode Visual Lock（meta/visual-profile.json，单集显式锁定）
```

### 4.1 三层职责

- **Base Visual Reality Rules**：账号级底线，当前散落在 M00 `visual_dna`、`FIRST_PERSON_CASUAL_SNAPSHOT_V1` 与 `standards/制作规范_正式版.md`/`真实性与共享风格锚点规范_V1.1.md` 中。V1.0 先在治理层把它显式化，**是否物理抽取为一个 base 文件留到 Phase 2 决定**。
- **Visual Profile**：世界/年代/质感层，继承 base 后定义差异。
- **Episode Visual Lock**：单集显式锁定（如 12-01 的 SPIRITED_AWAY），只允许**收窄**，不允许反转 base。

### 4.2 字段继承 / 覆盖矩阵

| 字段 | Base | Profile 可否覆盖 | Episode Lock 可否覆盖 |
| --- | --- | --- | --- |
| `reality_first` / 非电影化底线 | 定义 | 否 | 否 |
| `ghost_camera` 禁止、`camera_authorship=required` | 定义 | 否 | 否 |
| `defects_must_have_physical_cause` | 定义 | 否 | 否 |
| `realism_basis` | 定义 | 是（M02 例外） | 否 |
| `era` / `world` | 未定义 | 是 | 否 |
| `lighting_rules` / `color_rules` / `composition_rules` | 默认 | 是 | 是（需 reason） |
| `capture_profile_ref` | 默认 CP01 | 是 | 是 |
| `prohibited_patterns` | 最小集 | 只能追加 | 只能追加 |
| `audience_expectation` / `compatible_story_types` | 账号默认 | 是 | 否 |
| `must_keep` | 空 | 是 | 是 |

**不可覆盖的红线**：任何 Profile 与 Episode Lock 都不得把"非电影化、非摆拍、物理成立、有摄影者"这四条反转。SPIRITED_AWAY 已经用 `conflict_resolution` 表达了同一原则，V1.0 把它上升为通用规则。

### 4.3 与现有 `precedence` 的关系

现有 precedence 是 `explicit_episode_or_series_visual_profile → capture_physics_and_story_era → 母风格视觉语言`。V1.0 保持该顺序，并在其之下补一条不可覆盖的 base 层：

```
Base Reality (不可覆盖)
  > Episode/Series Visual Profile (显式锁定)
  > Capture Physics & Story Era
  > Profile Visual Language (母风格)
  > Frame Contract 编译结果
```

---

## 5. 视觉一致性约束

### 5.1 每个 Profile 必须包含

- `capture style`：记录器具与拍摄行为（衔接 `capture_grammar_ref` / `capture_profile_ref`）。
- `camera behavior`：谁在拍、视点、是否允许摆拍（衔接 Capture Grammar）。
- `realism`：`realism_level` + `reality_basis`。
- `lighting`：光源来源与禁止项。
- `environment`：环境/年代/材质的可区分描述。

缺任一项即视为 Profile 不完整，不得进入 Visual Lock（Phase 4 落为校验）。

### 5.2 各 Profile 的禁止项（示例，非穷尽）

| Profile | 必须禁止 |
| --- | --- |
| M00 | 电影布光、海报感、完美构图、商业 HDR、全局复古 LUT、美化皮肤、幽灵机位 |
| M01 | 现代摄影设备入镜、影视棚拍、影楼古装写真感、仙侠特效 |
| M02 | 神话战斗、史诗大场面、神性光晕滥用、游戏 CG 感、无因果泛光 |
| M03 | 抒情 MV 感、宣传片航拍、统一江南青绿调色 |

### 5.3 共享约束（所有 Profile 继承）

- 摄影缺陷必须有物理原因，禁止装饰性假损伤。
- 每帧必须能回答"谁拍的、为什么拍、为什么保存"。
- 锁质感不锁场景（继承 M00 `anti_homogeneity`）。
- 禁止静默替换另一个 Profile 或 Capture Grammar。

---

## 6. 与 Story OS 链路关系

```
Story Lock
   |
   v
Visual Profile Selection        <- 本文档新增的治理点（Phase 3 接入）
   |
   v
Visual Lock（1 + 3 四张 admission）
   |
   v
Frame Contract（合并 Profile + Capture Grammar + Sequence + Environment）
   |
   v
Production（Batch / Scheduler）
   |
   v
Review（visual_profile_match 等检查项）
```

关键定性：**Visual Profile 不是 prompt，而是生产合同。** 它进入 Frame Contract 编译、进入 Visual Lock 评审检查项、可被 SHA 校验；prompt 只是它的渲染产物之一。

Visual Profile 的位置在 **Story Lock 之后、Visual Lock 之前**：Story Lock 决定故事是什么，Profile 决定这个世界"长什么样"和"用什么拍"，Visual Lock 用像素证明它成立。

---

## 7. Profile 选择策略

### 7.1 输入与输出

输入：`story_type`、`era`、`world`、`audience_expectation`、`account_series`、用户显式指定。
输出：`profile_id`（+ 可选 `capture_profile_ref`）。

### 7.2 决策优先级（高到低）

1. **用户显式锁定**：Runtime Request / Episode 级声明 → 强绑定，禁止替换（现有 `mode=explicit_user_locked` 语义）。
2. **系列覆盖**：`<series>` 级 Profile 声明。
3. **故事信号推断**：按 `world`/`era`/`story_type` 命中 Profile 的 `compatible_story_types`。
4. **账号默认回退**：M00。

### 7.3 示例决策表

| 故事信号 | 结果 |
| --- | --- |
| 当代情侣 / 旧物怪谈 / 山难纪实 | M00 |
| 古代市井百姓日常 | M01 |
| 天界普通岗位日常 | M02 |
| 江南地域沉浸生活 | M03（`era` 由实例声明） |
| 用户显式指定其他视觉体系 | 强绑定该 Profile |

### 7.4 冲突与回退

- 推断结果与显式锁定冲突：显式锁定胜出，并记录 `override_reason`。
- 无任一命中：回退 M00，不报错，但必须留证据说明"按账号默认处理"。
- 命中多个同优先级候选：视为选择策略失败，必须显式报错，禁止随机挑一个。

---

## 8. 后续实施计划

### Phase 1：文档规范（本阶段）
- 产出：本文档。
- 验收：M00 现状、五层机制、缺口、编号规范、继承模型、选择策略均有明文。
- 风险：编号与既有 `M00_*` 混合命名的收敛属于破坏性命名变更，必须单独评审。

### Phase 2：Profile JSON Schema + 注册表
- 产出：`standards/schemas/visual-profile.schema.json`；`standards/visual_profiles/index.json`（对齐 `capture_profiles/index.json` 形态）；命名收敛方案（G3/G4）。
- 验收：现有 M00 与 SPIRITED_AWAY 能通过新 schema 校验且 SHA 不变；`visual_profile.py list` 改为读注册表。
- 风险：不得改写已锁定 Profile 的内容哈希。

### Phase 3：Profile 选择接入
- 产出：显式选择策略实现（在 Story Lock 之后、Visual Lock 之前产生 profile 决策证据）；M01/M02/M03 Profile 资产。
- 验收：新集能自动得到正确 `profile_id`，且决策可审计。
- 风险：G4 重复解析器必须先收敛，否则会接入到错误的解析链。

### Phase 4：Gate 验证
- 产出：Visual Lock / Frame Contract 增加 Profile 完整性校验（5.1 必含字段、禁止项不得被删除）。
- 验收：缺字段或不完整 Profile 必须 FAIL；历史集不追溯误伤。

### Phase 5：生产测试
- 产出：M01/M02/M03 各跑一集端到端，验证"同哲学不同世界"确实可区分。
- 验收：四集（M00/M01/M02/M03）放在一起时，视觉身份可辨识且不互相污染。

---

## 附录 A：当前视觉资产清单（审计证据）

| 类型 | 路径 | 数量 |
| --- | --- | --- |
| Visual Profile | `standards/visual_profiles/` | 2（M00、SPIRITED_AWAY_LIVE_ACTION_V1） |
| Capture Profile | `standards/capture_profiles/` | 8（CP01..CP08）+ index |
| Capture Grammar | `standards/capture_grammars/` | 1（FIRST_PERSON_CASUAL_SNAPSHOT_V1） |
| Sequence Grammar | `standards/sequence_grammars/` | 1（SG01） |
| Schema | `standards/schemas/` | 2（无 visual-profile schema） |
| 解析器 | `visual_profile.py`、`visual_profile_bridge_v224.py`、`capture_grammar_v228.py`、`capture_profile.py`、`sequence_grammar.py`、`frame_contract.py`、`environment_contract.py` | — |
| 第二套解析实现 | `visual_profile_resolver.py`（已被 `story_creator.py` 接入，尚未接入正式 Frame Contract 链） | 1 |

## 附录 B：待决问题（需用户裁决）

1. **M03 的 `era`**：地域母版还是古代母版？是否与 M01 合并？
2. **Base Reality Rules 是否物理抽取**：抽为 `standards/visual_profiles/_base_reality_rules.json`，还是仅保留为规范文档？
3. **M02 的 `diegetic_capture_device`**：天界的记录器具由谁定义，是否需要独立 Capture Profile？
4. **混合命名收敛**：`M00_HEAVEN_WORKER_DAILY_V1` / `M00_ANCIENT_DAILY_LIFE_V1` 是否重命名为 M02/M01，或直接废弃；已绑定该 id 的 `江南卖花姑娘的一天` 请求如何迁移。
5. **重复解析器处置**：`visual_profile_resolver.py` 是删除、合并，还是明确标记为 legacy；其静默回退必须优先改为 fail-fast。
