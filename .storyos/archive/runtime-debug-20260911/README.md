# Runtime Debug Archive

日期：2026-09-11

状态：Completed（2026-09-11 完成归档迁移）

用途：归档生产过程中的临时调试产物，不属于正式 Runtime 资产。

归档范围：

### 批次 1（.storyos 调试产物）

- _ep003_prod_driver.py（迁移前已由其他进程移除，本次未归档）
- dump_task.ps1
- task_dump.txt
- runtime-launcher-validation/
- runtime-requests/

### 批次 2（根目录临时产物，2026-09-11 追加）

- _tmp_contact_sheet.py
- _tmp_critic_decode.txt
- _tmp_review_out.txt
- _tmp_validate_out.txt
- _tmp_codex_shim_0153.py（已失效的历史 Codex shim；迁移后 contract_sync 的根目录守卫按“不存在即通过”处理）
- runtime-smoke-report.json（2026-09-10 快照；runtime smoke 脚本仍会在仓库根目录重新生成同名默认输出）

### 批次 3（workbench 活动日志，2026-09-11 19:08 追加）

- workbench/_f01_run.log
- workbench/_ve.log

迁入本目录下的 workbench-logs/ 子目录。

迁移方式：git mv（文件内容不变、SHA-256 不变、Git 历史可追踪）。批次 2 共 6 个文件，迁移前后逐文件 SHA-256 一致（hashDiff=0）。

### 批次 4（运行时与根目录日志，2026-09-11 19:08 追加）

- .storyos/fc.log、.storyos/na.log、.storyos/rebind.log、.storyos/transition.log（2026-09-11 18:14–18:15 由 EP003 运行写出）
- reports/debug.log（Chromium/crashpad 杂项日志，2026-09-11 15:26）

迁入本目录下的 runtime-logs/ 子目录，共 5 个文件约 2.8KB。

至此原「未纳入迁移」清单已全部归档，本目录不存在挂起项。

版本库边界（2026-09-11 起）：

- 本目录内的归档物通过 `!/.storyos/archive/**` 豁免，保留跟踪（该豁免需排在全局 `_tmp_*` 规则之后）。
- 仍被拦截的是本地派生证据：.storyos 版面探查产物（bands / strip / under / zbox / bandpreview
  下的 PNG、layout_final.json、layoutprobe.json，共 55 张约 54.7MB）。
- `/.storyos/*.log` 与 `/reports/debug.log` 的拦截保留，用于阻止同名新日志再次落到原路径被误暂存；
  已归档的这 5 份不受影响（路径在本目录下）。

原则：

- 不影响 EP003 当前生产。
- 不进入正式生产资产链。
- 保留调试证据，便于问题追踪。
- 后续确认无价值后再评估清理。
