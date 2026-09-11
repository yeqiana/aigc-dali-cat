# Story OS Visual Profile Selector V1.0

- 文档状态：设计稿（Design Only，Visual Profile Governance Phase 3.1）
- 适用范围：为新建 Episode 选择 Visual Profile ID
- 唯一存在性来源：`standards/visual_profiles/index.json`（Registry）
- 不建立第二权威：与 `standards/制作规范_正式版.md` 冲突时以主规范为准
- 本阶段不落地：不接入 Runtime、不改 machine_gate / frame_contract、不生成 Episode、不执行图片生产

---

## 0. 当前选择链审计（Phase 3.1 起点）

现状入口（`episodes/_system/`）：

1. `story_creator.create_episode(root, title, visual_profile)`
   - 调用方未传 id 时调用 `visual_profile_resolver.infer_profile(title)` 按标题关键词路由；传入时直接使用调用方 id。
   - 随后 `resolve_profile()` 经 Registry 解析，未注册即 fail-closed（VISUAL_PROFILE_NOT_REGISTERED）。
   - 结果写入 `meta/runtime-request.json` 的 `visual_profile` / `visual_profile_resolution`。
2. `visual_profile_resolver.infer_profile()`
   - `KEYWORD_ROUTES` 指向 `M00_HEAVEN_WORKER_DAILY_V1` / `M00_ANCIENT_DAILY_LIFE_V1`，二者是未注册的 deprecated 占位 id。
   - 路由目标未注册即被跳过，结果恒为 Registry 默认 `M00`。当前关键词路由实际是"死"的。
3. `visual_profile.resolve_base_profile(ep)`
   - 读 `meta/story-gates.json` 的 `visual_profile.mode`：`default` → 硬默认 `M00`；`override` → 要求 `profile_id`+`profile_path`+`override_reason` 并按路径校验文件（不经 Registry）。
4. `visual_profile_bridge_v224.episode_meta(ep)`
   - 读 Episode 本地 `meta/visual-profile.json`；与 story-gates override 的 id 不一致时硬失败 VISUAL_PROFILE_AUTHORITY_MISMATCH。
5. `compile_prompt_contract()` 把 `visual_dna` 编译进 prompt 文本——属于 Prompt 层，Selector 不进入。

结论：当前真正的来源只有四个——调用方显式指定、Episode meta 锁定、story-gates override、默认 M00。**没有**基于故事世界/年代/地域/受众的选择能力。Selector 只补这一层，且只补这一层。

---

## 1. 目标

Selector 负责：把 Story Intent + Episode Context + Audience Expectation 收敛成一个**已注册**的 `profile_id`，并留下可审计的**选择证据**。

Selector 不负责：Prompt 生成、图片生成、审核、Gate、状态机推进、Visual Lock 落盘。

一句话边界：Selector 输出"选哪个"，不输出"怎么拍"。

---

## 2. 输入模型

```json
{
  "story_intent": {
    "genre": "daily_life | work_life | anomaly_mystery | folk_life | travel_life",
    "theme": "string",
    "world": "real | historical_real | fictional",
    "era": "modern | ancient | unspecified",
    "location": "string",
    "experience_type": "observed | immersive_first_person"
  },
  "episode_context": {
    "account": "string",
    "series": "string",
    "previous_profile": "profile_id"
  },
  "audience_expectation": {
    "realism": "maximum | high",
    "immersion": "low | medium | high",
    "fantasy_level": "none | low | high"
  },
  "user_override": {
    "forced_profile_id": "profile_id | null"
  }
}
```

字段说明：

| 字段 | 必填 | 取值 | 来源 |
| --- | --- | --- | --- |
| story_intent.world | 是 | real / historical_real / fictional | Story Intent 解析结果 |
| story_intent.genre | 否 | 枚举 | Story Intent 解析结果 |
| story_intent.theme | 否 | 自由文本 | Story Intent 解析结果 |
| story_intent.era | 否 | modern / ancient / unspecified | 缺省 unspecified，禁止默认 ancient |
| story_intent.location | 否 | 自由文本（江南、水乡…） | Story Intent 解析结果 |
| story_intent.experience_type | 否 | observed / immersive_first_person | Story Intent 解析结果 |
| episode_context.series | 否 | 系列标识 | 系列锁定时提供 |
| episode_context.previous_profile | 否 | 上一集 profile_id | 同系列上一集 |
| audience_expectation.* | 否 | 枚举 | 受众预期 |
| user_override.forced_profile_id | 否 | profile_id | 等价于现有 --profile-id / runtime-request.visual_profile |

约束：world / era 解析不出来时不得靠标题猜，直接走默认。

---

## 3. Profile Selection Matrix

| Profile | world | era | theme | location | experience | fantasy_level |
| --- | --- | --- | --- | --- | --- | --- |
| M00_REAL_WORLD_DOCUMENTARY_V1 | real | modern（任意，设备物理优先） | daily_life / everyday_anomaly | 任意现实地点 | observed | none / low |
| M01_ANCIENT_MUNDANE_LIFE_V1 | historical_real | ancient | ordinary_people / market_life | 古代城镇乡野 | observed / immersive | none / low |
| M02_HEAVEN_MUNDANE_WORKER_V1 | fictional | fictional | workplace / mundane_work | 天界岗点 | observed / immersive | high |
| M03_JIANGNAN_IMMERSIVE_LIFE_V1 | real | modern / historical / unspecified | immersive_place_life | 江南 / 水乡 | immersive_first_person | none / low |

匹配语义（供 3.3 实现参考，本阶段只定义）：

- M00 适合：world=real，theme=daily_life，强调日常生活与关系密度，非电影化。
- M01 适合：world=historical_real 且 era=ancient，theme=ordinary_people；**不因区名含江南就命中**。
- M02 适合：world=fictional 且 fantasy_level=high，theme=workplace；仅标题出现"仙"不构成命中。
- M03 适合：location 命中江南/水乡，experience_type=immersive_first_person；era 由实例声明，M03 自身不绑定古代。

---

## 4. 选择优先级

```text
1. user_override.forced_profile_id      用户强制
2. episode_context.series / previous_profile   系列锁定
3. story world match                    故事世界匹配
4. location match                       地域匹配
5. audience expectation                 受众预期
6. default M00                          默认兜底
```

高优先级一旦命中即终止后续匹配；除第 6 级外，命中仍须产出选择证据。

禁止关键词覆盖强规则：标题出现"仙"≠M02，必须 world=fictional 且 theme 匹配才有资格进入 M02 候选。关键词只能作为 **signal 提示**，不能作为唯一判据。

---

## 5. 冲突处理

多候选时返回候选集，不静默选择。例如输入"古代 + 江南"：

```json
{
  "status": "needs_confirmation",
  "candidates": [
    {"profile": "M01_ANCIENT_MUNDANE_LIFE_V1", "matched_rules": ["era=ancient"]},
    {"profile": "M03_JIANGNAN_IMMERSIVE_LIFE_V1", "matched_rules": ["location=jiangnan"]}
  ]
}
```

规则：

- 单一候选 → `status=selected`。
- 多候选 → `status=needs_confirmation`，交人工确认（由后续 Visual Lock 阶段的人审承接）。
- 0 候选 → `status=default_with_reason`（M00）并记录未命中原因。
- 任何分支都不得返回未注册 id。

---

## 6. Selector Evidence

```json
{
  "schema_version": 1,
  "status": "selected",
  "selected_profile": "M01_ANCIENT_MUNDANE_LIFE_V1",
  "reason": ["world=historical_real", "era=ancient", "theme=ordinary_daily"],
  "rejected": [
    {"profile": "M03_JIANGNAN_IMMERSIVE_LIFE_V1", "reason": "location not matched"}
  ],
  "candidates": [],
  "source": "rule_engine",
  "registry": "standards/visual_profiles/index.json",
  "inputs_digest": "sha256:..."
}
```

原则：配置存在 ❌，选择事实存在 ✅。证据必须记录"用了哪些输入、命中了哪些规则、排除了哪些候选"。

Evidence 归属建议：写入 `meta/runtime-request.json` 的 `visual_profile_selection`（派生证据，不覆盖既有 `visual_profile` / `visual_profile_resolution`），或独立 `meta/visual-profile-selection.json`。最终落盘位置在 Phase 3.4 与 Visual Lock 一起定。

---

## 7. 禁止规则

Selector 不能：

1. 创建或虚构不存在的 Profile。
2. 自动 fallback 到未知 Profile（未注册即失败）。
3. 修改历史绑定（已锁 Episode 的 profile 不得被重写）。
4. 覆盖 `user_override.forced_profile_id`。
5. 输出未注册 id。
6. 仅凭标题关键词直接定 profile。
7. 输出 prompt 或视觉细节（越界到 Prompt 层）。
8. 写状态机字段或 Gate 结论。

---

## 8. 后续实施计划

| 阶段 | 内容 | 产出 |
| --- | --- | --- |
| Phase 3.1 | Selector 设计文档 | 本文 |
| Phase 3.2 | Selector JSON Schema | 输入 / 输出 / 证据契约 |
| Phase 3.3 | Rule Engine 实现 | 纯函数 + Registry fail-closed + 单测（不接 Runtime） |
| Phase 3.4 | Visual Lock 接入 | needs_confirmation 交人工；写入 Episode |
| Phase 3.5 | Gate 验证 | 只验证"选择证据存在且自洽" |

---

## 附录 A：与现有链路的关系

- Selector 复用现有 `visual_profile_resolver.resolve_profile()` 的 Registry fail-closed 语义，不新增存在性判定。
- Selector 替代（而非并存）`infer_profile()` 的关键词路由：关键词降级为 signal，最终仍走优先级与冲突处理。
- Selector 输出进入 Visual Lock / story-gates override / Episode meta 三条既有通道之一，由 Phase 3.4 决定，不新增第四状态机。
- `compile_prompt_contract()` 及其 `visual_dna` 编译属 Prompt 层，Selector 不触碰。

