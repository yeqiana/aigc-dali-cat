# Story OS V3 Phase 8-P8.6 Canary Progressive Rollout 实现报告

更新时间：2026-09-09

## 1. 目标

建立 V3 Runtime 的渐进式灰度放量能力，默认阶段：

`1% -> 5% -> 10% -> 25% -> 50% -> 100%`

每一级在满足样本量并通过 P8.5 回滚策略后才允许晋级；异常则回滚到 V2。

## 2. 实现

新增：

- `platform/gateway/canary_progressive_rollout.py`
- `tests/platform/test_canary_progressive_rollout.py`

调整：

- `platform/gateway/canary_runtime_gateway.py`
- `platform/gateway/canary_auto_rollback.py`

## 3. Progressive Rollout 模型

核心类型：

- `CanaryRolloutPlan`
- `CanaryRolloutDecision`
- `CanaryProgressiveRollout`
- `CanaryProgressiveRolloutController`

决策状态：

- `HOLD`：当前阶段继续观察
- `PROMOTE`：进入下一灰度阶段
- `ROLLBACK`：恢复 V2
- `COMPLETE`：100% 阶段验证完成

默认每一级至少需要 20 个请求样本。

## 4. 与 Auto Rollback 集成

每次阶段评估都会调用 P8.5 `CanaryAutoRollbackPolicy`：

- error rate 超阈值 -> ROLLBACK
- latency 超阈值 -> ROLLBACK
- trace unhealthy -> ROLLBACK
- 样本不足 -> HOLD
- 健康 -> PROMOTE

Rollout Controller 只修改 Canary Gateway 配置，不修改 Episode / Workflow / Artifact。

## 5. Percentage Routing 修复

P8.2 原实现中只要 `canary_percent > 0` 就会全部路由到 V3，导致 1%、5%、10% 实际等价于 100%。

P8.6 修复为确定性哈希分桶：

`request_key -> SHA256 -> bucket(0..99) -> compare canary_percent`

同一 request_key 稳定命中同一 Runtime，避免请求在 V2/V3 间抖动。

调用方应优先提供稳定的 `request_key`（request_id / user_id / tenant cohort 等）；为了兼容旧调用，未提供时退化使用 episode_id。

## 6. 安全边界

本阶段不负责：

- 修改 `episode-state.json`
- 修改 Workflow 状态
- 切换 Production Runtime Ownership
- 删除 V2 Runtime
- 发布 Artifact

100% Canary 仍不等于正式 Production Switch；Production Ownership 切换应由后续阶段单独决策。

## 7. 验证

已执行针对当前未跟踪文件的静态 whitespace 校验：

- `git diff --no-index --check /dev/null platform/gateway/canary_progressive_rollout.py`
- `git diff --no-index --check /dev/null tests/platform/test_canary_progressive_rollout.py`
- `git diff --no-index --check /dev/null platform/gateway/canary_runtime_gateway.py`

结果：均无 whitespace error 输出。

同时通过 `where/which/find` 检查运行环境；当前 DevSpace Shell 没有可用的 `python` / `py` / `pytest`，仓库内也没有可直接使用的 Python 虚拟环境，因此 Python 单测尚未真实执行，不标记 pytest PASS。

## 8. 结论

P8.6 已形成“阶段放量 + 健康评估 + 自动回滚 + 稳定百分比分桶”的最小生产闭环。

下一步建议进入 P8.7 Canary Soak & Promotion Gate：要求每一级经过稳定观察窗口后才允许继续放量，并生成最终 Production Switch Evidence。
