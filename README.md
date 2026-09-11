# 微恐故事 · 抖音 AI 悬疑图文系列

账号：啾啾脑洞故事。第一人称怪谈 / 规则怪谈图文，对标「鼠鼠脑洞批发」与「Zayn」，
目标 108 篇系列化世界观（108 道班 = 108 把锁 = 108 个守夜人）。

## 配置与目录入口

生产前先看 [`config/storyos.yaml`](config/storyos.yaml)：模型、Quality、画幅、M00、Normalize、并发和返修策略都集中在这里，并带有中文注释。

Agent/脚本随后读取 [`config/index.yaml`](config/index.yaml)，只加载当前阶段声明的最小文件集，避免递归扫描整个仓库。

```bash
python episodes/_system/story_os.py config validate
python episodes/_system/story_os.py config show
```

目录职责和兼容边界见 [`docs/architecture/仓库目录与配置治理.md`](docs/architecture/仓库目录与配置治理.md)。

## 执行入口

本 README 不保存 Story OS 规则副本，创作与执行规则只在以下入口维护：

- [`AGENTS.md`](AGENTS.md)：仓库协作规则（Codex 自动读取，含 Story OS 协议块）
- [`SKILL.md`](SKILL.md)：Story OS Agent 执行协议
- [`START_HERE.md`](START_HERE.md)：新篇执行流程唯一入口（只负责路由，不建立第二套规范）
- [`standards/制作规范_正式版.md`](standards/制作规范_正式版.md)：唯一创作规范权威
- [`standards/AUTHORITY_INDEX.json`](standards/AUTHORITY_INDEX.json)：从属细则路由索引
- [`config/index.yaml`](config/index.yaml)：目录布局（`episode_layout`）与阶段最小读取集（`stage_read_sets`）

## 剧集索引

| 剧集 | 目录 | 状态 |
|------|------|------|
| 01 家教 | episodes/01_家教/ | 已发布（2026-08-08，20 张） |
| 02 折多山守夜人 | episodes/02_折多山守夜人/ | 已发布（35 张） |
| 03 哀牢山三十六道班 | episodes/03_哀牢山三十六道班/ | 分镜验证样本（20 张规格） |
| 04 科考队系列 | episodes/04_科考队系列/ | S4/K1/K5/泥人续 V2 已发布；K3 盐湖路径型结构通过、待四图视觉准入；K2 V2.1 转储备（旧发布包作废）；K4 暂缓 |
| 05d 神尸地图·嫦娥 | episodes/05d_神尸地图_嫦娥/ | 成片验收有条件通过（8.7 分，20 张有效）；发布时补发布包与作者声明 |
| 06 神话遗址 | episodes/06_神话遗址/ | S1 墨脱发布包就绪（待发布）；S2 罗布泊 发布通过（9.08 分，发布图 20 张就绪）；S6 东海龙宫带字幕图已评审 |
| 06a 铁三角 | episodes/06a_铁三角/ | S1 墨脱 V2.1 成片就绪（待人工总审）；系列人物与父亲长期线已落盘 |
| 07 误入 | episodes/07_误入/ | A《古镇茶馆·还席》发布图就绪（9.00 分）；B《中元节误入流水席》最终交付 V1.1 就绪 |
| 08 古籍志怪 | episodes/08_古籍志怪/ | S1 促织、S2 种梨已发布；S3 画工画僵尸分镜草案完成，待正式生图 |
| 09 旧物怪谈 | episodes/09_旧物怪谈/ | 第一集《回村中巴捡MP4》已发布；第二集《QQ面基·中元节》已建目录，状态以当集 README 为准 |

## 规范

- 唯一权威规范：[standards/制作规范_正式版.md](standards/制作规范_正式版.md)
- 传播评分、推荐适配与发布后漏斗执行细则：[standards/抖音推流评分与发布后漏斗规范_V1.4.md](standards/抖音推流评分与发布后漏斗规范_V1.4.md)（仅为主规范执行细则）
- 可选共享视觉母风格：[standards/风格锚点_MP4_网吧_流水席_旧数码_V1.2.md](standards/风格锚点_MP4_网吧_流水席_旧数码_V1.2.md)
- 真实性逐图审查：[standards/真实性与共享风格锚点规范_V1.1.md](standards/真实性与共享风格锚点规范_V1.1.md)
- 字幕声音与人话化：[standards/字幕人话化与声音卡规范_V1.1.md](standards/字幕人话化与声音卡规范_V1.1.md)
- 逐帧生产、失败恢复与默认画幅：[standards/生产引擎与画幅规范_V1.2.md](standards/生产引擎与画幅规范_V1.2.md)（未指定默认 4:5 / 1080×1350）

以上均为 `制作规范_正式版.md` 的从属执行细则，不与主规范并列。

## 目录约定

目录职责与剧集内部布局的唯一索引事实在 [`config/index.yaml`](config/index.yaml)：
`episode_layout` 按 authority / evidence / derived / local_derived / media 五类声明
`<episode>/meta/`、`<episode>/media/`、`<episode>/release/` 等路径职责，不再由 README 维护第二份目录树。

- 新篇像素资产（`media/`、`release/` 等）默认不入 Git；正式剧集的 Git 只跟踪路径与 SHA 索引。
- 历史剧集的旧版目录不做破坏式重排；重新进入制作需要迁移本地媒体时，
  走 `episodes/_system/media_workspace.py` 的 copy → SHA verify → reference rewrite → remove-old 流程。
- 图像提示词治理模板见 `library/visual-patterns/documentary-realism/现实侵入式伪纪录片_通用提示词模板_V1.0.md`（Visual Pattern Source，参考材料，冲突以唯一权威规范为准）。
- `.codex/`、`.idea/`、`.playwright-cli/`、`.storyos_cache/` 等是本地工具或运行状态目录，不属于发布资产。

## 新篇执行

新篇执行流程唯一入口：[`START_HERE.md`](START_HERE.md)。README 不再维护第二份 Golden Path；
选题、Story Lock、Visual Lock、Batch、text audit、Release 与发布后数据回填顺序均以该入口为准；
规则正文见 [`AGENTS.md`](AGENTS.md) 与 [`SKILL.md`](SKILL.md)。
