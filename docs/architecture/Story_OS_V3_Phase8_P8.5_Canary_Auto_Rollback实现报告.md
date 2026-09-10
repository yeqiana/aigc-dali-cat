# Story OS V3 Phase 8-P8.5 Canary Auto Rollback 实现报告

更新时间：2026-09-09

## 1. 目标

为 V3 Canary Runtime 建立自动风险判断与安全回退能力：当错误率、平均延迟或 Trace 健康度超过阈值时，输出回滚决策，并将 Canary Gateway 恢复为 V2_RUNTIME。

## 2. 实现

新增：

- `platform/gateway/canary_auto_rollback.py`
- `tests/platform/test_canary_auto_rollback.py`

核心组件：

- `CanaryRollbackPolicy`：阈值配置。
- `CanaryAutoRollbackPolicy`：只负责风险评估。
- `CanaryRollbackDecision`：输出 KEEP_CANARY / ROLLBACK_TO_V2。
- `CanaryRollbackController`：只修改 Canary Gateway 路由开关，不修改 Episode、Workflow 或 Artifact。

## 3. 默认策略

- `max_error_rate = 0.05`
- `max_avg_latency_ms = 30000`
- `min_sample_size = 5`
- `rollback_on_trace_failure = true`

样本不足时不会自动回滚，避免小样本误判。

## 4. 回滚边界

触发回滚后仅执行：

- `gateway.canary_enabled = False`
- `gateway.canary_percent = 0`
- 后续路由恢复 `V2_RUNTIME`

明确不做：

- 不修改 `episode-state.json`
- 不修改 Workflow 状态
- 不删除 V3 Trace / Execution evidence
- 不修改或删除 Production Artifact

## 5. 验证

新增单测覆盖：

1. 样本不足保持 Canary。
2. 错误率超阈值触发回滚。
3. 延迟或 Trace 异常触发回滚。
4. 回滚控制器将 Gateway 恢复到 V2_RUNTIME。

`git diff --check` 已通过。

当前 DevSpace shell 未发现可用 `python` / `py` 命令，因此本轮无法在该 shell 中实际执行 pytest；需要在具备项目 Python 环境的宿主执行单测。

## 6. 结论

P8.5 已形成 `Metrics -> Risk Evaluation -> Rollback Decision -> Gateway -> V2_RUNTIME` 最小闭环，并保持生产状态与业务资产隔离。
