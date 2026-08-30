# Story OS V2.0.3.5 — Release Preflight Guard

> 身份：`standards/制作规范_正式版.md` 的 active subordinate。
> 本规范不增加 episode stage，只补发布前 P0 证据门禁。

## 1. 最近 5 篇不再允许布尔值自证

`story.recent5_checked=true` 不是充分证据。

V2.0.3.5 新篇或显式启用 Release Guard 的剧集，在 Story Lock 前必须存在：

`meta/recent5-review.json`

它必须绑定当前 episode fingerprint、账号 pattern registry、实际比较对象与相似度结论。历史 registry 为空时不得伪造历史 fingerprint。

本 Release Guard 对 55–69 采用保守策略：先阻断并要求重设 fingerprint，直到低于 55；不接受只写一段解释绕过。

## 2. 连续系列增加 Series Lock SHA

### V2.0.3.5.1 Series Detection Hotfix

**目录结构不得推断连续世界观。** 同一个栏目/题材目录下存在多个 episode，只代表内容归类，不代表这些故事共享人物、地点、道具或世界规则。

Series Lock 只在以下任一条件成立时启用：

1. `<series>/meta/series-lock.json` 已存在；
2. `<series>/meta/series-continuity.json` 显式声明 `enabled=true`。

推荐显式声明：

```json
{
  "schema_version": 1,
  "enabled": true,
  "series_id": "彼此的天上"
}
```

可执行：

`python episodes/_system/release_preflight.py declare-series <series_dir> --series-id <series_id>`

`init-series-lock` 会自动写入该连续性声明。没有声明、也没有 series lock 的普通栏目默认 **不触发** Series Lock。

连续世界观系列必须建立：

`<series>/meta/series-lock.json`

至少锁 `world_rules[]` 与 `anchors[]`。每个 anchor 至少包含 `id` 与 `contract`。

每集通过 `meta/series-lock-binding.json` 绑定 series lock SHA。

## 3. Release Semantic Review

PUBLISH_READY 前 fresh isolated critic 必须审实际最终：

cover + actual title + body 01–03 + climax + payoff + captions + publish copy + propagation card。

必须全部通过：

- cover_title_match
- cover_frame01_handoff
- first3_coherence
- climax_upgrade
- payoff_honesty
- description_consistency
- no_caption_invented_core_evidence

## 4. AI / Governance 发布合规

必须存在 `meta/publish-compliance.json`，至少声明：

- ai_generated=true
- platform_ai_label_required=true
- platform_ai_label_method=douyin_platform_declaration
- fiction_context_notice_required=true
- user_must_confirm_label_at_publish_time=true

机器门禁只能证明“发布前计划已准备”，不能代替用户在平台发布页实际确认 AI 内容声明。

## 5. 旧剧集兼容

V2.0.3.4 及更早 episode 不因安装自动失效。V2.0.3.5 新篇或显式 `release_preflight.py enable` 的剧集启用新门禁。

## 6. 命令

```bash
python episodes/_system/release_preflight.py bootstrap-registry
python episodes/_system/release_preflight.py enable <episode>
python episodes/_system/release_preflight.py build-recent5 <episode>
python episodes/_system/release_preflight.py declare-series <series_dir> --series-id <series_id>
python episodes/_system/release_preflight.py init-series-lock <series_dir> --source <series-lock-source.json>
python episodes/_system/release_preflight.py bind-series <episode>
python episodes/_system/release_preflight.py init-compliance <episode>
python episodes/_system/release_preflight.py run-release-critic <episode>
python episodes/_system/release_preflight.py verify <episode>
```


## 7. V2.0.3.6 Semantic Recent-5

V2.0.3.6 新篇在原 deterministic Recent-5 之外，必须执行 `standards/fingerprint_semantic_guard_V1.0.md`。
最终相似度取 exact-string 与 semantic-equivalence 两者较高值；mechanism veto 取 OR。
critic 不得自行给相似度数值，全部分数必须由 Python 根据固定九维权重计算。
V2.0.3.5.1 及更早 episode 不因仓库升级被强制迁移。
