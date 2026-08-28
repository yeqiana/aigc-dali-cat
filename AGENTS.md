# 项目协作规则（Codex 自动读取）

## Story OS V1.8 执行入口

涉及 `story` 分支的选题、分镜、出图、字幕、审核、发布、复盘任务，Codex 必须先读取仓库根目录 `START_HERE.md`，再读取 `SKILL.md`。

- `AGENTS.md`：Codex 自动入口与仓库协作规则。
- `SKILL.md`：Story OS 执行协议。
- `standards/制作规范_正式版.md`：唯一创作规范权威。
- `meta/episode-state.json`：唯一机器阶段事实源。
- `meta/story-gates.json`：门禁证据，不保存 stage，不得成为第二状态机。


唯一权威规范：[standards/制作规范_正式版.md](standards/制作规范_正式版.md)

传播评分与发布后数据诊断按 [standards/抖音推流评分与发布后漏斗规范_V1.4.md](standards/抖音推流评分与发布后漏斗规范_V1.4.md) 执行；该文件仅解释主规范 8.4/8.5/12.4/12.5，不建立第二权威，冲突时以主规范为准。V1.3 新增发布时间分层实验与 1h 冷启动快照：1h 仅用于时间实验，不替代主规范正式 6h/24h/48h/7d 验收窗口。

生产真实性、共享画风和字幕人话化按以下从属执行细则：
- [standards/风格锚点_MP4_网吧_流水席_旧数码_V1.2.md](standards/风格锚点_MP4_网吧_流水席_旧数码_V1.2.md)
- [standards/真实性与共享风格锚点规范_V1.1.md](standards/真实性与共享风格锚点规范_V1.1.md)
- [standards/字幕人话化与声音卡规范_V1.1.md](standards/字幕人话化与声音卡规范_V1.1.md)
- [standards/生产引擎与画幅规范_V1.2.md](standards/生产引擎与画幅规范_V1.2.md)

这些从属细则均不建立第二权威；冲突时以 `standards/制作规范_正式版.md` 为准。V1.8 起 M00「MP4 × 网吧 × 流水席旧数码质感校准版」在用户未指定时默认启用；显式视觉体系可覆盖，且年代/采集设备物理真实性永远高于母风格质感。


## 网页 GPT 出图与流量控制

1. 本项目的出图、修图默认由官方网页 ChatGPT 手动完成。Codex 仅使用 `$web-gpt-image-handoff` 基于当集最终分镜生成文字交接单；除非用户明确覆盖，不调用任何本地图片生成或编辑工具。
2. 交接单必须包含逐图提示词、画幅与尺寸、角色与场景锁定、负面约束、建议文件名及分批验收项；未指定画幅时默认 **4:5 / 1080×1350**，只有任务/分镜/manifest 明确指定时才使用 **9:16 / 1080×1920**；不得擅自改写正式分镜的剧情与镜头顺序。
3. 不自动打开或操作网页 ChatGPT，不要求上传整批图片给 Codex。网页生成后，用户仅按需回传本地路径或少量关键截图进行验收和重出建议。
4. 本规则不改变下列媒体提交白名单和 `.gitignore` 约束。

## Episodes 机器状态与发布清单

> Story OS V1.8：`episode-state.json` 仍是唯一阶段事实源；`story-gates.json` 只记录故事/视觉/字幕/锁图门禁证据，不得保存或覆盖 stage。

1. 新建具体剧集时，按 [`episodes/_system/README.md`](episodes/_system/README.md) 初始化 `meta/episode-state.json`、`meta/release-manifest.json` 与 `meta/story-gates.json`；历史剧集不批量伪造状态，只在重新进入制作/发布/复盘时迁移。
2. 机器状态固定为：`IDEA_LOCKED → STORYBOARD_LOCKED → VISUAL_CALIBRATED → PRODUCTION_PASSED → PUBLISH_READY → PUBLISHED → DATA_REVIEWED`。
3. `episode-state.json` 是阶段事实源；README 的状态文案与其冲突时必须修 README，不得反过来只改机器状态来迁就旧文案。
4. 正向推进必须使用 `episodes/_system/episode_state.py transition`，只能相邻前进。脚本会先用 `validate_episode.py --target` 验收目标门禁，失败时不得手工越级修改 JSON。
5. `release-manifest.json` 只记录实际发布版本事实，不替代分镜、制作规范或数据报告；路径统一使用仓库根目录相对路径。
6. `PUBLISH_READY` 前必须完成制作门禁与九项传播卡，并写明 `publish_decision=go`；`conditional/not_recommended` 若仍发布必须填写 `decision_note`。
7. 发布图可继续被 `.gitignore` 排除；完整张数/封面存在性校验在本地工作区执行。只检查 Git 元数据时才使用 `--metadata-only`。

## 提交规则

1. 允许提交 git 的图片/大文件仅限以下两类：
   - 角色参考图：`episodes/**/assets/characters/`
   - 竞品与账号截图：`research/competitors/`、`research/account/`
2. 其他图片、视频、音频、压缩包一律禁止提交，已由 `.gitignore` 默认忽略，包括：
   - 各集 `images/`、`publish/` 成片
   - `assets/` 下 frames、subtitled、references、shenshi、materials 等中间资产
   - 发布包 zip、`workbench/` 中间处理资产、`.playwright-cli/` 截图
3. 新增大文件前先 `git status` 确认只出现白名单文件；可用 `git check-ignore <文件>` 验证是否被忽略。
4. 已误提交的非白名单文件用 `git rm --cached` 移出索引（保留本地），不要删本地文件。

<!-- STORY_OS_V1_8_AGENTS_BEGIN -->
## V1.8 默认视觉路由

Codex 若未收到用户明确画风/质感指令，必须先解析 `M00 / MP4 × 网吧 × 流水席旧数码质感校准版`，再按本集真实性卡决定实际设备表现。不得把“默认 M00”误解成“所有作品都必须旧低清”。

V1.8 推进时除原 `validate_episode.py + machine_gate.py` 外，还必须通过 `v18_gate.py`：Story/Visual Approval SHA、最新 Text Audit、Release Package SHA 都不得漂移。
<!-- STORY_OS_V1_8_AGENTS_END -->
