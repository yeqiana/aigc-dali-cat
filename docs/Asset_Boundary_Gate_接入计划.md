# Asset Boundary Gate 接入计划

状态：Shadow Mode

日期：2026-09-11

## 当前策略

Asset Boundary Gate 当前只观察，不阻断生产。

目的：

- 不影响正在生产中的 EP003。
- 提前发现测试资产与生产资产混用风险。
- 为后续生产流程强制接入准备证据。

## Shadow Mode 行为

检查：

- placeholder 是否被引用到 production media。
- fixture/demo 资产是否进入 episode media。
- publish/evidence 是否引用非生产资产。

行为：

- 记录问题。
- 输出报告。
- 不修改 episode-state。
- 不阻断 Visual Lock / Production / Release。

## 后续正式接入计划

新生产流程：

```
Generation
    ↓
Candidate
    ↓
Asset Boundary Gate
    ↓
Approved
    ↓
Publish
```

正式启用后：

- 测试资产进入生产链直接 FAIL CLOSED。
- publish 前必须通过资产边界检查。
- evidence 必须绑定 production asset SHA。

## EP003 特别说明

EP003 当前生产不受影响：

- 不迁移历史媒体。
- 不重新计算 SHA。
- 不触发现有门禁。
- 不改变生产状态。

待 EP003 发布闭环完成后，再评估全量启用。
