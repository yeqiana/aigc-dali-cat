# Episodes 状态机 + Story OS 门禁 V1.4

本目录只建立**一套机器阶段状态**。

## 1. 三个 meta 文件，三种职责

```text
<episode>/
└── meta/
    ├── episode-state.json
    ├── release-manifest.json
    └── story-gates.json
```

- `episode-state.json`：唯一阶段事实源。
- `release-manifest.json`：最终发布版本事实。
- `story-gates.json`：故事/视觉/字幕/锁图门禁证据；**不保存 stage**。

禁止新增 `episode.yaml stage` 作为第二状态机。

## 2. 唯一状态机

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
→ PUBLISHED
→ DATA_REVIEWED
```

- 正向只能相邻推进。
- 正向推进前自动对目标状态运行 validator。
- 返工必须显式 `--rewind`。
- README 与机器状态冲突时，以 `episode-state.json` 为准。
- 旧剧集无需批量迁移；重新进入制作/发布时补 `story-gates.json`。

## 3. 新建剧集

```bash
python episodes/_system/episode_state.py init \
  episodes/10_新系列/01_新故事 \
  --id 10-01 \
  --series 10_新系列 \
  --title "新故事" \
  --frame-count 20

# 未传 --aspect-ratio 时默认 4:5 / 1080×1350
# 如需竖屏满屏版：追加 --aspect-ratio 9:16（1080×1920）
```

初始化同时创建三个 meta 文件。

## 4. 旧剧集接入 Story OS V1.1

```bash
python episodes/_system/episode_state.py migrate-gates \
  episodes/09_旧物怪谈/02_QQ面基_中元节
```

这一步：

- 不修改当前 state
- 不伪造 passed
- 只创建门禁骨架
- 之后需要按真实资料填写再继续 transition

## 5. Story OS 门禁

### 进入 STORYBOARD_LOCKED

`story-gates.json` 必须证明：

- recent5 已检查
- 四把锁差异 >= 2
- 未触发机制换皮 veto
- task_closed
- competing_explanations >= 2
- hook / climax / payoff 合法
- story review passed

### 进入 VISUAL_CALIBRATED

必须：

- 恰好 4 张视觉准入帧
- visual_admission review passed
- authenticity review passed
- `visual.continuity.required` 声明的锚点全部有值

默认必须锚定：

- location
- key_prop
- weather_time

有人物连续性需求时，把 `protagonist`、`wardrobe` 加进 required。

### 进入 PRODUCTION_PASSED

在原有 production_review / captions / production_gate=pass 基础上还必须：

- production review passed
- continuity review passed
- authenticity review passed
- 需要字幕时声音卡完成
- subtitle review passed

### 进入 PUBLISH_READY

在原有九项传播卡、标题/简介/话题、传播分、publish_decision=go 基础上还必须：

- recommendation_fit passed
- publish passed
- 本地发布图张数正确
- 本地发布图严格匹配 manifest：4:5=1080×1350（新篇默认），9:16=1080×1920
- 锁底图 SHA-256 未变化

CI 使用 `--metadata-only`，因此不会要求 Git 中不存在的 publish 图片/锁底图二进制文件。

## 6. 锁图

`story-gates.json`：

```json
{
  "locks": {
    "edit_mode": "subtitle_only",
    "assets": [
      {
        "path": "episodes/09_xxx/01_xxx/workbench/locked/19.png",
        "sha256": "64位SHA256",
        "reason": "底图锁定，只改字幕"
      }
    ]
  }
}
```

本地验收时 hash 不一致直接 FAIL。

## 7. 验收

当前状态：

```bash
python episodes/_system/validate_episode.py <episode_dir>
```

预检目标状态：

```bash
python episodes/_system/validate_episode.py <episode_dir> --target VISUAL_CALIBRATED
```

全仓库 CI：

```bash
python episodes/_system/validate_episode.py --all --metadata-only
```

## 8. 兼容规则

- tool_version 1.2 及以前且没有 `story-gates.json`：普通校验只 WARN。
- 旧剧集如果要继续向前 transition：必须先 `migrate-gates`。
- V1.4 新剧集缺 `story-gates.json`：FAIL。
