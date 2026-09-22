# Story OS V3 Phase9 Runtime Launcher（P9.34）

更新时间：

2026-09-10

## 1. 目标

P9.28-P9.33 已交付常驻 Worker、Metrics 端点、告警通道与存活观察者，但这些命令此前需要分别拉起。本批交付一个单一编排入口，把「常驻 Worker + Metrics 端点」作为一个可部署单元统一启动、统一优雅退出，作为系统服务 / 计划任务部署（阻塞项 #1）的直接前置。

## 2. 交付内容

- scripts/phase9_runtime_launcher.py：RuntimeLauncher 编排入口
- tests/platform/test_phase9_runtime_launcher.py：离线回归 5 例

编排内容（常驻）：

- metrics exporter：把 Worker 的 Prometheus textfile 暴露在 /metrics
- worker：心跳 / 探针 / 巡检 / 健康 / 告警 / 指标

关键语义：

- build_children 构造 Worker 与 Metrics 端点两个子进程，两者共享同一 metrics 文件
- start / stop 统一拉起与优雅退出
- run 采用 fail-fast：任一子进程提前退出即返回，不自动重启
- 退出码 0 = 收到停止信号或达到 max-seconds 优雅退出；4 = 子进程提前退出

明确不做：

- 不自己注册系统服务 / 计划任务（部署需单独授权）
- 不自动重启失联 Worker（自愈由后续 policy 决策，需单独授权）
- 不把 Watchdog 当作常驻子进程（Watchdog 是「跑 N 轮」的一次性巡检，应由调度器周期性拉起）
- 不写凭据；证据只记 host / port / database 与布尔

## 3. 验证证据

### 离线回归

tests/platform：305 passed（基线 300 + launcher 新增 5）

新增 5 例覆盖：

- build_children 构造两个子进程并共享 metrics 文件
- alert-webhook 可选注入
- start / stop 统一优雅退出
- run 正常 max-seconds 到期优雅返回（exited_early 为空）
- run fail-fast 检测子进程提前退出（exited_early 非空）

### 真机 E2E（2026-09-10，真实 Redis 127.0.0.1:6379）

- /metrics：HTTP 200，60 行 Prometheus exposition
- /healthz：HTTP 200
- launcher 退出码 0（max-seconds 到期优雅退出，exited_early=None）
- 证据落盘：.storyos/runtime-launcher/launcher-evidence.json（gitignored）

## 4. 边界

- 编排入口只把「可部署单元」做好；注册 Windows 系统服务 / 计划任务、开启 tick 自动重启进程均需单独授权，本批未执行。
- 子进程被 launcher 主动 terminate 时，Windows 下退出码非 0 属正常（常驻进程被优雅终止），不影响 launcher 自身退出码 0。

## 5. 结论

常驻 Runtime 编排入口已交付并真机 E2E 验证。阻塞项 #1 由「载体已交付、未部署」收敛为「可部署单元已交付，系统服务注册仍待授权」。
