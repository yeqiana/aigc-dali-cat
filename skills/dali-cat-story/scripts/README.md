# Validators

| Script | Purpose |
|---|---|
| `bootstrap_episode.py` | 为新单集创建 `episode.yaml` 与字幕源模板 |
| `validate_episode.py` | schema、阶段状态、故事门禁、反同质化、四张视觉准入 |
| `validate_package.py` | publish 图数、连续编号、1080×1920 尺寸 |
| `validate_subtitles.py` | 声音卡、逐图字幕/静默覆盖、重复/AI腔提示、线索回收 |
| `validate_review_state.py` | review 状态与 release_required |
| `validate_locked_edits.py` | SHA-256 锁定底图/资产不被误改 |
| `hash_asset.py` | 生成锁定资产 SHA-256 |
| `validate_all.py` | 单集总门禁 |
| `validate_repo.py` | 扫描仓库内已有 `episode.yaml`；兼容未迁移旧集 |

开发阶段按 `stage` 渐进启用规则；`--release` 会强制打开发布门禁。
