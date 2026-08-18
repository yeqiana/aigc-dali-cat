# 项目协作规则（Codex 自动读取）

唯一权威规范：[standards/制作规范_正式版.md](standards/制作规范_正式版.md)

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
