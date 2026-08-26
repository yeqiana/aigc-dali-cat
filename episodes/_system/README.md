# Episodes 轻量状态机与发布 Manifest V1.2

本目录只解决三件事：

1. `meta/episode-state.json`：当前剧集处于哪个生产阶段；
2. `meta/release-manifest.json`：最终准备发布的版本到底是哪一套；
3. `validate_episode.py`：在状态推进前检查必要证据、发布文案和本地发布资产。

> V1.2 锁定：在 V1.1 状态机不变的前提下，为发布时间实验增加 `publication.timing_window` 与 `data_review.first_hour_metrics`。1h 只做冷启动实验快照，不新增生产阶段，也不替代 48h 的 `DATA_REVIEWED` 门禁。

它不是新的创作规范。剧情、真实性、字幕、传播评分仍以仓库根目录 `standards/制作规范_正式版.md` 及其从属细则为准。

## 一、状态机

只保留 7 个正向阶段：

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
→ PUBLISHED
→ DATA_REVIEWED
```

含义：

| 状态 | 含义 |
|---|---|
| `IDEA_LOCKED` | 选题、核心异常、人物动机与闭环已锁，可以开始正式分镜 |
| `STORYBOARD_LOCKED` | 正式分镜已锁，不再随意改剧情顺序 |
| `VISUAL_CALIBRATED` | 角色/地点/采集质感或关键样张已通过，可以批量生产 |
| `PRODUCTION_PASSED` | 正文图、连续性、字幕、真实性和制作完成度硬门禁通过 |
| `PUBLISH_READY` | 最终标题/封面/发布图/简介/话题已锁，九项传播卡已完成并明确决定发布 |
| `PUBLISHED` | 已真实发布，manifest 写入发布时间 |
| `DATA_REVIEWED` | 至少完成 48h 数据复盘，并写入数据报告 |

规则：

- 正向只能一次前进一级，禁止从 `STORYBOARD_LOCKED` 直接跳 `PRODUCTION_PASSED`。
- 每次正向 `transition` 会先自动按目标状态运行 validator；目标门禁失败时状态文件保持不变。
- 返工可以回退到任意更早阶段，但必须显式 `--rewind` 并写原因。
- `episode-state.json` 是机器状态事实源；README 中的“制作中/可发布/已发布”只是人类展示，漂移时以机器状态为准并修 README。
- 老项目不用一次性迁移。新项目从现在起创建 meta；旧项目在再次进入制作或复盘时补齐。

## 二、每集新增的两个文件

```text
<episode>/
└── meta/
    ├── episode-state.json
    └── release-manifest.json
```

### episode-state.json

只保存身份、当前状态、更新时间和状态历史，不保存复杂审查结果。

### release-manifest.json

只冻结“这一版到底发什么”：

- 剧集 ID / 系列 / 标题 / 形态 / 画幅；
- 正文张数、发布目录、封面、总览；
- 故事、分镜、画风、字幕、发布文案、制作验收、传播卡的文件路径；
- 制作门禁、传播评分与发布决定；
- 实际发布标题、简介、话题、置顶评论、发布时间，以及可选 `timing_window`（A/B/C/D/organic）；
- 数据报告和已完成的 6h/24h/48h/7d 正式节点；做发布时间实验时可额外记录 `1h` 与 `first_hour_metrics`。

时间字段规则：`published_at` 是发布时间事实源；`weekday` 从 `published_at` 派生，不在 manifest 重复手填。`first_hour_metrics` 未按时采集就保持 `null`，不得用 6h 或当前总览倒填。

所有路径统一写**仓库根目录相对路径**，例如：

```json
  "storyboard": "episodes/09_旧物怪谈/02_QQ面基_中元节/docs/02_最终分镜.md"
```

这样不同剧集仍可保留自己原有的 `docs/`、`images/`、`v3_final/` 等目录，不强制迁移成统一大目录。

## 三、使用

从仓库根目录执行。

### 1. 初始化新剧集

```bash
python episodes/_system/episode_state.py init \
  episodes/10_新系列/01_新故事 \
  --id 10-01 \
  --series 10_新系列 \
  --title "新故事" \
  --frame-count 20 \
  --aspect-ratio 9:16
```

初始化后会创建状态文件和一份 draft manifest。

### 2. 查看状态

```bash
python episodes/_system/episode_state.py show episodes/10_新系列/01_新故事
```

### 3. 推进状态

```bash
python episodes/_system/episode_state.py transition \
  episodes/10_新系列/01_新故事 \
  STORYBOARD_LOCKED \
  --note "20张正式分镜已锁"
```

### 4. 返工回退

```bash
python episodes/_system/episode_state.py transition \
  episodes/10_新系列/01_新故事 \
  STORYBOARD_LOCKED \
  --rewind \
  --note "图12导致核心因果断裂，退回分镜重构"
```

### 5. 只预检目标状态（不改状态）

```bash
python episodes/_system/validate_episode.py \
  episodes/09_旧物怪谈/02_QQ面基_中元节 \
  --target PRODUCTION_PASSED
```

`transition` 正向推进时会自动做同样的目标门禁检查。

### 6. 验收一集

```bash
python episodes/_system/validate_episode.py episodes/09_旧物怪谈/02_QQ面基_中元节
```

### 7. 验收全部已接入状态机的剧集

```bash
python episodes/_system/validate_episode.py --all
```

如果当前 Git checkout 不包含被 `.gitignore` 忽略的发布图片，只想校验状态和文档元数据：

```bash
python episodes/_system/validate_episode.py --all --metadata-only
```

## 四、自动验收门禁

validator 会随状态逐步加严：

- `STORYBOARD_LOCKED+`：必须存在正式分镜；
- `VISUAL_CALIBRATED+`：必须存在画风/真实性/校准证据；
- `PRODUCTION_PASSED+`：必须存在制作验收文件，且 `production_gate=pass`；
- `PUBLISH_READY+`：必须有最终版本、发布目录、封面、字幕、发布文案、传播卡、0–10 传播分、`s_min_score`、传播结论、实际标题/简介/话题，并且 `publish_decision=go`；
- 传播结论由 `propagation_score + s_min_score` 按推流规范当前门槛自动推导，手填结论不一致直接失败；
- `conditional` / `not_recommended` 仍决定发布时，必须填写 `decision_note`，不能静默放行；
- 非 `--metadata-only` 模式下，`PUBLISH_READY+` 会按 `body_glob` 实际数正文图，数量必须与 `body_frame_count` 一致；
- `PUBLISHED+`：必须写 `published_at`；若参与 V1.3 发布时间实验，同时填写 `timing_window` 并在发布后约 1h 记录 `first_hour_metrics`；
- `DATA_REVIEWED`：数据报告必须存在，且至少完成 `48h` 节点；
- manifest 中所有文件/目录路径必须使用仓库根相对路径；绝对路径、Windows 盘符/UNC、逃出仓库根目录的路径直接失败；
- state history 必须是合法的相邻前进/显式回退链；历史迁移允许首条 `mode=migration`；
- state 与 manifest 的 ID / 系列 / 标题不一致直接失败；
- README 和机器状态冲突给 `WARN`，不阻断历史项目，但必须修正。

## 五、边界

- 状态机不判断“故事好不好”，只判断是否具备进入下一阶段的证据。
- validator 不取代主规范的人工创作评审。
- 发布图片仍可继续被 `.gitignore` 排除；完整验收在本地工作区执行，Git 仓库只追踪 meta 和文档。
- 不要求所有历史项目立刻补 meta，避免一次性迁移造成大量伪状态。
