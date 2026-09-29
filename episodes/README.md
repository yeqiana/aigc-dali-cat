# 剧集资产目录

每个剧集或系列独立维护自己的文档、图片、脚本和发布包。系列目录可以继续按篇章拆分，但不要把不同篇章的图片放回同一个根级图片目录。

## 当前目录

| 目录 | 类型 | 入口 |
|---|---|---|
| `00_独立篇/` | 规范独立篇生产线 | `01_五环外的浓雾/`、`02_埋儿那天_娘把我拦住了/`、`03_江南卖花姑娘的一天/` |
| `01_家教/` | 单篇已发布 | `docs/`、`images/publish/`、`scripts/` |
| `02_折多山守夜人/` | 单篇已发布 | `docs/`、`v3_final/publish/`、`scripts/` |
| `03_哀牢山三十六道班/` | 分镜验证样本 | `docs/` |
| `04_科考队系列/` | 系列生产线 | `S4_红外相机蹲着的人/`、`K1_水库退水门口泥人/`、`K2_冰川/`、`K4_溶洞/`、`K5_卡拉先格尔/`、`泥人续_送件/` |
| `05_神尸地图_嫦娥/` | 单篇系列分支 | `docs/`、`assets/`、`publish/`、`scripts/` |
| `06_神话遗址/` | 系列生产线 | `01_墨脱/`、`02_罗布泊/`、`06_东海龙宫/` |
| `07_误入/` | 系列生产线 | `docs/`、`images/`、`scripts/` |
| `08_古籍志怪/` | 古代志怪改编系列（方案可评审） | `S1_促织/README.md`、`S1_促织/docs/` |
| `09_旧物怪谈/` | 旧设备现实侵入式怪谈系列 | `01_回村中巴捡MP4/README.md`、`02_QQ面基_中元节/README.md` |
| `10_山难伪纪录片/` | 系列生产线 | `01_鳌太线_热汤/` |
| `11_仲夏夜惊魂/` | 系列生产线 | `01_停电夜蜕壳/`、`02_惊魂_重制版/` |
| `14_彼此的天上/` | 系列生产线 | `01_不存在的夜行路/`、`02_玻璃另一边的手/` |
| `15_天界生活日常/` | 系列生产线 | `01_天界普通女生的一天/` |
| `16_尸解仙/` | 系列生产线 | `01_尸解仙/` |
| `17_铁三角/` | 系列分支 | `01_墨脱/` |

## Episode 身份与编号

新建或仍在生产的 Episode 使用统一两级路径：`episodes/NN_系列名/EE_标题/`。

- `SERIES_ID` 与系列目录一致，例如 `14_彼此的天上`。
- `BUSINESS_EPISODE_ID` 固定为 `NN-EE`，例如 `14-02`。
- MySQL 的 `EPU_...` 是永久存储主键；目录、系列或业务编号规范化时不得为了“好看”重算。
- 同一个两位系列号 `NN` 只能对应一个系列；同一系列内 `EE` 不得重复。
- 一句话创建默认进入 `00_独立篇`，按现有最大编号顺延，例如 `00-01`、`00-02`。
- `_archive/` 可以保留历史 namespace，但归档行仍保留规范化后的业务编号和系列编号。
- 已发布、只读且未重新进入生产的早期单层目录（如 `01_家教/`）属于 legacy layout；不得作为新 Episode 模板。再次生产时先迁入两级编号结构。
- 历史 Runtime Request、Ledger、报告中的旧编号/旧路径属于审计证据，不回写；使用迁移报告追溯旧身份到规范身份。

## 目录规则

- `docs/` 只放创意、分镜、评审、发布清单和篇章说明。
- `images/` 或版本目录只放图像资产；中间稿、发布稿和带字幕稿按目录区分。
- `scripts/` 只放该篇章实际使用的处理脚本。
- 竞品和账号采集样本放在项目根目录 `research/`，不放进剧集目录。

## 机器状态与发布 Manifest

从 2026-08-26 起，新剧集接入轻量机器状态；旧项目不强制一次性迁移，在再次制作或复盘时补齐。

每个接入的**具体剧集目录**新增：

```text
meta/
├── episode-state.json
└── release-manifest.json
```

状态链固定为：

```text
IDEA_LOCKED
→ STORYBOARD_LOCKED
→ VISUAL_CALIBRATED
→ PRODUCTION_PASSED
→ PUBLISH_READY
→ PUBLISHED
→ DATA_REVIEWED
```

- `episode-state.json` 是阶段状态事实源；README 的“制作中/可发布/已发布”必须与其同步。
- `release-manifest.json` 冻结最终张数、发布目录、封面、字幕/发布文案、制作门禁、传播评分、实际发布信息和数据复盘节点。
- 正向状态推进必须相邻，且 `episode_state.py transition` 会先自动执行目标阶段验收；失败不改状态。
- 发布图片继续允许被 `.gitignore` 排除，完整图片数量检查在本地工作区执行。

工具与完整字段说明见：[`_system/README.md`](_system/README.md)。

常用命令：

```bash
# 初始化新剧集
python episodes/_system/episode_state.py init <episode-dir> \
  --id <series-episode-id> --series <series> --title <title>

# 推进状态（会先自动验收目标状态）
python episodes/_system/episode_state.py transition <episode-dir> STORYBOARD_LOCKED \
  --note "正式分镜已锁"

# 单集验收
python episodes/_system/validate_episode.py <episode-dir>

# 全量验收已接入剧集
python episodes/_system/validate_episode.py --all
```
