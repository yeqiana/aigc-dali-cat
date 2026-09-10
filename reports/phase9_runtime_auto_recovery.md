# Story OS V3 Phase9 Runtime Auto-Recovery（P9.34.2）

更新时间：

2026-09-10

## 1. 目标

阻塞项 #8「Recovery 自动执行」此前只有执行器（P9.31），「tick 内自动触发」未开启。本批把自动触发接线补齐：新增自愈编排模块，并把 Worker 挂上 --auto-recover 开关。默认关闭，不改变现有生产行为；只有显式开启并配置重启命令，才对 CRITICAL 事件自动执行恢复决策。

## 2. 交付内容

- platform/operations/runtime_auto_recovery.py：自愈编排（AutoRecoveryEvent / component_for_reason / orchestrate）
- scripts/phase9_runtime_worker.py：--auto-recover 与 --restart-agent-command 开关（默认关闭），tick 内 _run_auto_recovery 接线
- tests/platform/test_runtime_auto_recovery.py：编排离线 6 例
- tests/platform/test_phase9_runtime_worker_auto_recovery.py：Worker 接线离线 6 例

接线链路：

    CRITICAL incident → component 推导 → RuntimeRecoverySelfHealing 决策
        → RecoveryExecutor 执行注入 handler（--restart-agent-command）

component 推导：

- health_model 告警回看 detail.reasons 原始信号：agent_success_rate_low → AGENT_RUNTIME，workflow_success_rate_low → WORKFLOW
- 心跳 / 依赖探针 → RUNTIME（默认无回退动作）

安全姿态：

- 默认 auto_recover=False，不执行任何恢复动作
- 无 restart command 时如实记录 FAILED（no_executor_for_action），不静默
- handler 抛异常如实记 FAILED，不吞掉

## 3. 验证证据

### 离线回归

tests/platform：322 passed（基线 310 + 编排 6 + Worker 接线 6）

### 真机 E2E（2026-09-10，真实 Redis 127.0.0.1:6379，--no-mysql 隔离）

- 注入 agent.execute FAILED + workflow.step FAILED + 卡住 RUNNING span → health UNHEALTHY → CRITICAL runtime_unhealthy
- auto-recover 触发 RESTART_AGENT：executed=true，restart command echo 返回 0
- auto_recovery_result 落盘 alert_log（record.status=EXECUTED）
- evidence config：auto_recover_configured=true，restart_agent_command_configured=true

证据：.storyos/auto-recovery/（gitignored）

## 4. 边界

- 默认关闭；开启 --auto-recover 属副作用操作，需显式授权。
- 真正重启动作由 --restart-agent-command 注入；Worker 自身不管理 agent 进程。
- 未做生产归属切换、未接真实 Prometheus / 告警外部端点。

## 5. 结论

自愈自动触发已交付并真机 E2E 验证。阻塞项 #8 由「执行器已交付、tick 内自动触发未开启」收敛为「自动触发已接线（默认关闭），开启待授权」。
