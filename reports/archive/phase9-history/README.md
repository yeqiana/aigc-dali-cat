# Phase9 历史报告归档

本目录保存 2026-09 Phase9 改造期间形成的历史验收、方案、冻结与执行快照。

## 生命周期口径

- **归档不是删除**：原文件使用 `git mv` 迁入，Git 历史与内容保持可追溯。
- **这里不是当前生产事实源**：当前 Runtime 状态、生产接管、存储配置、运行证据应从现行代码、配置、Canonical 暴露问题清单及实时 Gate/Status 输出读取。
- **不得把历史 PASS 当成当前 PASS**：任何需要当前状态的验收必须重新执行对应 Gate/测试/状态命令。

## 顶层仍保留的 Phase9 报告

以下文件仍有 tracked consumer/现行脚本明确引用，因此继续保留在 `reports/` 顶层：

- `phase9_final_freeze_scope.md`
- `phase9_runtime_bootstrap_manifest.md`
- `phase9_runtime_canary_simulation_report.md`
- `phase9_runtime_recovery_drill_report.md`
- `phase9_runtime_recovery_real_validation.md`

除此之外的 `phase9_*` 历史报告统一归档到本目录，避免 `reports/` 顶层继续同时承载“当前入口”和“大量历史快照”。
