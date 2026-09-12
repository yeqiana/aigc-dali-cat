# Story OS Runtime Node Contract V1.0

版本：V1.0
日期：2026-09-12
范围：V3 Runtime DAG 生产调度第一阶段

## 目的与边界

Node Contract 只描述一次 Runtime 调度中的任务依赖、输入、输出、重试和优先级。它不是 Episode 阶段事实，不写入 `episode-state.json`，也不向 `story-gates.json` 写入阶段。

节点完成只代表执行器已返回一个结果；不代表 Story、Visual、Production 或 Release Gate 通过。Gate 仍由既有 Runtime、Workflow、Evidence 与 `machine_gate.py` / `evidence_gate.py` 裁决。

```json
{
  "node_id": "string",
  "node_type": "concept|story|character|environment|frame_contract|image_generation|review|repair|release",
  "depends_on": [],
  "input_contract": {},
  "output_contract": {},
  "retry_policy": {},
  "priority": "HIGH|MEDIUM|LOW",
  "evidence_required": []
}
```

## 字段约束

- `node_id`：本次 Contract 内唯一标识。
- `depends_on`：前置节点 ID 列表；全部完成后才能释放当前节点。
- `input_contract` / `output_contract`：调用方声明的输入输出边界，不授予 Evidence 或 PASS。
- `retry_policy`：执行器可用的重试规则；技术重试、内容返修、人工阻塞仍由既有流程实际记录。
- `priority`：`HIGH`、`MEDIUM`、`LOW`。同一优先级按 Contract 原始顺序稳定排序。
- `evidence_required`：该节点后续需要的证据路径或证据类型；调度器不生成也不验证它们。

## failure、retry、blocked

- `failure`：调用方已知节点执行失败。调度器只接收该事实，不分类、不写 Ledger。
- `retry`：调用方按既有 retry policy 再次提交任务；调度器只重算依赖与优先级。
- `blocked`：节点的任一直接或间接依赖失败，因此本轮不能调度。无依赖分支继续可执行。

所有这些都是一次调度计算的输入或输出，不保存为第二状态机。真实 Evidence 仍由原执行器、Production Ledger、Review 与 Gate 体系产生和验证。
