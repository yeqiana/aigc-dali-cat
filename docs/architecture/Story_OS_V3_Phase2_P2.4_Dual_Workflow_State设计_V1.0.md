# Story OS V3 Phase 2-P2.4 Dual Workflow State 设计 V1.0

## 目标

在不替换 V2.7 Runtime 状态的情况下，对比：

- episode-state.json（Runtime事实）
- workflow_projection（平台投影）

验证两者一致性。

## 原则

Dual State 不是双状态机。

Runtime 仍然负责执行事实。
Workflow Projection 只负责平台查询。

## 架构

```
Runtime
  |
  +--> episode-state.json
  |
  +--> Event
          |
          v
   Workflow Projection
          |
          v
   workflow state
```

## 校验

输入：

- runtime_state
- projected_state

输出：

- matched
- mismatch details

## 禁止

- 修改 runtime state
- 自动修正状态
- 推进 workflow
- 调度任务

## 验收标准

1. 可以发现状态差异
2. 不影响生产链
3. 支持后续 Workflow Engine 接管评估
