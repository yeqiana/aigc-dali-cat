# Story OS 升级说明（历史入口）

> **HISTORICAL_ONLY**：本文件只保留旧安装路径的历史说明入口，不再提供当前安装/执行命令。

当前 Story OS 产品版本只认根目录 `story_os_manifest.json`。
当前执行入口只认 [`START_HERE.md`](START_HERE.md)。
当前 canonical engine 只认 `episodes/_system/`。

旧版文档中出现的 `episode.yaml`、`skills/dali-cat-story/requirements.txt`、`.codex/skills/...`、覆盖式 `INSTALL_WINDOWS.ps1` 等做法已经退出当前执行契约，不得作为新篇或返修任务的执行依据。

需要检查当前仓库是否健康：

```bash
python episodes/_system/story_os.py doctor
python episodes/_system/contract_sync.py
```

版本化的 `README_UPGRADE_V*.md` 仅用于历史追溯；发生冲突时，以 `START_HERE.md`、根 `SKILL.md`、`story_os_manifest.json` 和 canonical engine 为准。
