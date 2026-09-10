# Story OS V3 Phase9 Runtime Deploy（P9.34.1）

更新时间：

2026-09-10

## 1. 目标

P9.34 已交付常驻编排入口，但「系统服务 / 计划任务部署」仍待授权。本批把部署的可执行性补齐：交付 schtasks 部署脚本，默认 dry-run，只打印将要执行的命令，不改变系统状态；授权后加 --apply 才真正注册。

## 2. 交付内容

- scripts/phase9_runtime_deploy.py：install / uninstall / status 三个子命令
- tests/platform/test_phase9_runtime_deploy.py：离线回归 5 例

方案取舍：

- 选用 Windows 计划任务（schtasks /sc onstart /ru SYSTEM），不引入 NSSM 等第三方工具
- 开机自启 ONSTART，任务名 StoryOSRuntime，指向 launcher（常驻 Worker + Metrics 端点）
- 不写凭据；SYSTEM 账户运行依赖 python.exe 在系统 PATH（脚本默认取当前解释器绝对路径）

安全边界：

- 默认 dry-run，不改变系统状态
- --apply 才注册计划任务，属副作用操作，需用户明确授权后使用
- 不自动开启自愈 / 不自动重启 Worker（自愈由后续 policy 决策，需单独授权）

## 3. 验证证据

### 离线回归

tests/platform：310 passed（基线 305 + deploy 新增 5）

新增 5 例覆盖：

- build_launcher_command 路径引号
- install 命令形状（/create /tn /sc onstart /ru SYSTEM /f，/tr 含 python 与 launcher 路径）
- uninstall 命令形状
- status 命令形状
- 未知 action 抛 ValueError

### dry-run 真机验证（2026-09-10）

- install 默认 dry-run：正确打印注册命令（绝对 python 路径 + launcher 路径 + --metrics-port 18081）
- status --apply 只读查询：rc=1「系统找不到指定文件」，确认任务 StoryOSRuntime 当前未注册

## 4. 边界

- 未执行 install --apply（注册计划任务需用户明确授权）。
- 未执行 uninstall --apply。
- 自愈 wrapper / 自动重启仍为后续工作，需单独授权。

## 5. 结论

部署脚本已交付并 dry-run 验证。阻塞项 #1 由「可部署单元已交付、注册待授权」收敛为「部署脚本已交付，授权后一条命令即可注册」。
