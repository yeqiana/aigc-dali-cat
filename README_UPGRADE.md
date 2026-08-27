# aigc-dali-cat / story 执行层升级包 V1.0

适配基线：`yeqiana/aigc-dali-cat` 的 `story` 分支，核对基线提交 `b742aca4ee2a1ece2d197cc1fff990d1559786f6`（2026-08-27 检查）。

本包**不替换**现有 `standards/`、`episodes/`、`research/`、`reports/`、`workbench/` 和图片资产。它只新增一层“可执行规范”，解决“规范写得很全，但 Agent 仍可能漏读、漏审、误改锁定底图”的问题。

## 新增内容

- `SKILL.md`：仓库级执行入口，规定 Agent 的读取顺序、状态机、硬门禁和改图边界。
- `skills/dali-cat-story/`：可移植 Story Skill，包含 references、模板、validators、测试。
- `standards/templates/episode.template.yaml`：每篇故事的机器可读 manifest 模板。
- `standards/templates/subtitles.template.yaml`：字幕声音卡、逐图字幕、静默图和线索回收模板。
- `.agents/skills/dali-cat-story/SKILL.md`、`.codex/skills/dali-cat-story/SKILL.md`：不同 Agent 环境的轻量入口。
- `.github/workflows/story-gates.yml`：只对已经存在 `episode.yaml` 的剧集执行门禁，不会强迫旧剧集一次性迁移。

## 安装

把本 ZIP 的内容覆盖/复制到 `story` 分支仓库根目录即可。它默认只新增文件，不要求修改你现有作品。

安装依赖：

```bash
python -m pip install -r skills/dali-cat-story/requirements.txt
```

为某一篇建立 manifest：

```bash
python skills/dali-cat-story/scripts/bootstrap_episode.py episodes/09_旧物怪谈/你的单集目录
```

制作过程中检查：

```bash
python skills/dali-cat-story/scripts/validate_all.py episodes/09_旧物怪谈/你的单集目录/episode.yaml
```

发布前严格检查：

```bash
python skills/dali-cat-story/scripts/validate_all.py episodes/09_旧物怪谈/你的单集目录/episode.yaml --release
```

## 迁移原则

1. **主规范仍是唯一权威。** `standards/制作规范_正式版.md` 永远高于本 Skill；本 Skill 只是把其中能机器化的规则做成执行门禁。
2. **旧作品不强制迁移。** 新篇从现在开始使用 `episode.yaml`；旧篇只有在返修/重制时再补。
3. **不复制规范全文。** references 只做索引、执行解释与机器化映射，避免两份规范长期漂移。
4. **锁底图时输出分离。** 例如“图19底图一像素尽量不动，只改字幕”，应把无字幕底图锁定并把字幕版输出到独立目录；validator 可用 SHA-256 检查锁定资产是否被改动。
5. **WARN 不等于 FAIL。** AI 腔、字幕重复开头等难以完全程序判断的项目只报警；尺寸、缺图、编号、硬门禁、锁定资产改变等直接失败。

## 推荐落地顺序

- P0：新篇全部添加 `episode.yaml`。
- P0：每次发布前跑 `validate_all.py --release`。
- P0：任何“只改字幕/只改文字”的图先登记 `locks.assets`。
- P1：逐步给历史高价值作品补 manifest。
- P1：再把你现有的人工审核报告字段映射进 `review`。

## 与当前 story 分支的关系

当前 README 已明确：主规范是 `standards/制作规范_正式版.md`，新篇流程包含最近5篇同质化检查、四张视觉准入、分镜、出图、字幕、制作验收、发布前传播评分与发布后漏斗复盘。本升级包不改变这个流程，而是把关键节点变成可检查状态。
