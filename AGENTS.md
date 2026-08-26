# 项目协作规则（Codex 自动读取）

唯一权威规范：[standards/制作规范_正式版.md](standards/制作规范_正式版.md)

传播评分与发布后数据诊断按 [standards/抖音推流评分与发布后漏斗规范_V1.2.md](standards/抖音推流评分与发布后漏斗规范_V1.2.md) 执行；该文件仅解释主规范 8.4/12.4/12.5，不建立第二权威，冲突时以主规范为准。

## 网页 GPT 出图与流量控制

1. 本项目的出图、修图默认由官方网页 ChatGPT 手动完成。Codex 仅使用 `$web-gpt-image-handoff` 基于当集最终分镜生成文字交接单；除非用户明确覆盖，不调用任何本地图片生成或编辑工具。
2. 交接单必须包含逐图提示词、9:16/1080×1920、角色与场景锁定、负面约束、建议文件名及每 10 张验收项；不得擅自改写正式分镜的剧情与镜头顺序。
3. 不自动打开或操作网页 ChatGPT，不要求上传整批图片给 Codex。网页生成后，用户仅按需回传本地路径或少量关键截图进行验收和重出建议。
4. 本规则不改变下列媒体提交白名单和 `.gitignore` 约束。

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
