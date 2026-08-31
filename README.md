# 微恐故事 · 抖音 AI 悬疑图文系列

账号：啾啾脑洞故事。第一人称怪谈 / 规则怪谈图文，对标「鼠鼠脑洞批发」与「Zayn」，
目标 108 篇系列化世界观（108 道班 = 108 把锁 = 108 个守夜人）。

<!-- STORY_OS_RUNTIME_REQUEST_P0_BEGIN -->
## Story OS V2.1｜一句话全自动入口

当前 Story OS 支持先把自然语言编译为 `runtime-request`，再进入正式执行链。

最简单的调用：

```text
读取 story 分支。
全自动做一篇「仲夏夜惊魂」。
```

**不传剧情也可以。** 此时自动进入 `story_input.mode=auto_create`：Story OS 自己做 Recent-5 / Concept Ambition、发散 8–12 个方向、选最强候选、编写完整故事，再进入 Story Lock。

如果给粗剧情：

```text
读取 story 分支。
全自动做一篇「仲夏夜惊魂」。

剧情大概是：
……
```

粗剧情会被识别为 `user_seed`：保留核心意图，但必须强化机制、补逻辑、重写节奏/高潮，禁止直接机械拆成分镜。

如果写“必须保留 / 结尾必须”，进入 `core_constraints`；只有明确说“剧情已经定了 / 不要改剧情”才进入 `locked_story`。

### 图像模型

- 未指定：默认 `gpt-image-2`
- 显式 `image=gpt-image-2`：记为用户强绑定，Story OS 不允许静默换模型
- 可复现回归可使用固定快照 `gpt-image-2-2026-04-21`

### 当前 Visual Lock

V2.1 当前流程统一为 **4 张 Visual Lock**：

1. ordinary baseline
2. worst capture condition
3. first major anomaly
4. high-impact admission

不存在当前流程里的“3 张校准 + 4 张准入”双重口径；三图只属于 legacy compatibility。

规范：[`standards/Runtime_Request_Contract_V1.0.md`](standards/Runtime_Request_Contract_V1.0.md)

机器入口：

```bat
python -X utf8 episodes/_system/runtime_request.py compile --text-file request.txt
python -X utf8 episodes/_system/story_os.py request compile --text-file request.txt
```
<!-- STORY_OS_RUNTIME_REQUEST_P0_END -->

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

```text
standards/          系列规范（唯一权威：制作规范_正式版.md）
research/           竞品与账号原始采集样本
reports/            数据验收报告与会话交接
workbench/          临时修复和中间处理资产
episodes/
└── NN_故事名/      每集一个目录：顺序编号 + 故事名
    ├── docs/       创意、对标分析、Skill 约束、分镜、交接文档
    ├── scripts/    字幕渲染等工具脚本
    └── 版本目录/   如 v1_34ratio / v2_916 / v3_final（含 publish / subtitled）
```

图像提示词治理规范见根目录的 `现实侵入式伪纪录片_通用提示词模板_V1.0.md` 是图像提示词治理模板；`.codex/`、`.idea/`、`.playwright-cli/` 等为本地工具或运行状态目录，不属于发布资产。。


## 新篇执行

**新篇执行流程唯一入口：[`START_HERE.md`](START_HERE.md)。** README 不再维护第二份 Golden Path；选题、Story Lock、Visual Lock、Batch、text audit、Release 与发布后数据回填顺序均以该入口和根 `SKILL.md` 为准。
<!-- STORY_OS_V2_0_3_4_LAYOUT_BEGIN -->
## V2.0.3.4 新篇目录约定

新进入 Story OS 管理的具体篇章使用以下本地工作区：

```text
<episode>/
├─ story/                 # Story Lock / storyboard / visual lock / publish copy
├─ meta/                  # stage / gates / ledger / reviews / media-index
├─ assets/
│  ├─ characters/         # 可入 Git
│  └─ references/         # 本地，不入 Git
├─ media/                 # 本地，不入 Git
│  ├─ calibration/
│  ├─ raw/
│  ├─ candidates/
│  ├─ approved/
│  ├─ publish/
│  ├─ review/
│  └─ archive/
└─ release/               # cover / FINAL.zip，本地，不入 Git
```

旧篇不做破坏式全仓重排；只有重新进入制作且已有 `meta/episode-state.json` 的篇章才由迁移器安全归档本地媒体。
<!-- STORY_OS_V2_0_3_4_LAYOUT_END -->
