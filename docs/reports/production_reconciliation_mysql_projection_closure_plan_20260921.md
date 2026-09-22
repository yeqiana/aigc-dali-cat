# Production Reconciliation MySQL Projection 收口方案

日期：2026-09-21  
状态：DESIGN ONLY / NOT IMPLEMENTED  
范围：`meta/runtime/production-reconciliation.json`

## 1. 目标

将 Production Reconciliation 从“运行后直接落一个 JSON report”收口为：

`reconcile_locked() → MySQL durable evidence → optional JSON export/projection`

边界保持不变：

- Production Ledger 继续是生产结果 authority。
- Production Recovery Journal 继续是 mutable recovery transaction authority。
- Redis Production Queue 继续是 hot-state authority。
- Episode stage 继续由 canonical Episode State 管理。
- Reconciliation 只记录“这次 reconcile 看到了什么、做了什么、结果是什么”，不得成为第二状态机或下一轮 recovery 的决定来源。

## 2. 当前现状

当前 `episodes/_system/production_recovery.py::reconcile_locked()`：

1. 从 MySQL Production Ledger authority + Redis Queue + worker lifecycle 计算 reconcile 结果。
2. 对每条 item 形成 `item_id / frame / outcome / ledger_status / lifecycle_state`。
3. 最后调用 `atomic_write_json(ep / "meta/runtime/production-reconciliation.json", report)`。

因此当前 JSON 是 projection / evidence，不是业务 authority；但 durable evidence 仍没有数据库化。

## 3. 目标数据模型

建议新增独立 repository，不复用 Recovery Journal 表，避免把 immutable reconcile evidence 与 mutable transaction authority 混在一起。

建议表：`TB_PRODUCTION_RECONCILIATION`

| 字段 | 说明 |
|---|---|
| `RECONCILIATION_ID` | 每次 reconcile 唯一 ID |
| `EPISODE_ID` | Episode storage identity |
| `RECONCILED_AT` | 本次 reconcile 时间 |
| `ROW_COUNT` | report rows 数 |
| `DOCUMENT_BLOB` | canonical JSON bytes |
| `SHA256` | blob SHA-256 |
| `BYTE_SIZE` | blob 长度 |
| `CREATE_TIME` | DB 创建时间 |

可选 query projection 表 `TB_PRODUCTION_RECONCILIATION_ROW` 只在确有按 frame/outcome 查询需求时再加；第一阶段不必为了“拆 JSON”提前制造复杂表。

## 4. 写入语义

新增 `production_reconciliation_persistence.persist(ep, report)`：

- `mysql`：只写 MySQL。
- `dual`：MySQL 保存 durable evidence，同时写 JSON compatibility projection。
- `json`：保留现状。
- persist 失败时 reconcile 不得伪装成功；返回明确 persistence error，但不得因此二次调用 Provider。
- MySQL document 使用 canonical serialization，并校验 `SHA256 + BYTE_SIZE`。

`reconcile_locked()` 的业务计算保持不变，只替换最后的 persistence sink，不改变任何 Queue / Ledger / Recovery 决策。

## 5. 读取语义

生产恢复逻辑**不读取 Reconciliation 作为输入**。

仅提供审计 / Console / 报告读取：

`load_latest(ep)`
- mysql 模式 → MySQL
- dual 模式 → MySQL 优先，JSON 仅兼容
- json 模式 → JSON

禁止：
- 根据 reconciliation report 推导 Ledger status。
- 根据 reconciliation report 重放 Queue。
- 让 reconciliation report 参与 Episode stage transition。
- MySQL 读失败时静默 fallback 到 stale JSON。

## 6. JSON 文件最终角色

`meta/runtime/production-reconciliation.json` 最终分类：

- projection
- compatibility
- export artifact

默认 MySQL 模式：
- 不再由核心 runtime 自动写。
- 如需要人工审计文件，通过显式 export 命令生成。
- export 必须带 source DB row ID / SHA，避免被误认为 authority。

## 7. 迁移与兼容

不要求批量迁移所有历史 JSON。

建议：
1. 新 reconcile 从 cutover 后直接写 MySQL。
2. 历史 JSON 保留只读，不反向写回业务状态。
3. 如有审计需求，可一次性 import 为 `source=legacy_json_import` evidence。
4. import 保留原文件 SHA、原 `reconciled_at`，禁止伪造新运行时间。
5. 不因历史 JSON 缺失阻断 Production。

## 8. 实施顺序

Phase A：
- schema / repository
- persistence facade
- repository unit tests

Phase B：
- `reconcile_locked()` 切 persistence facade
- mysql 模式停止 runtime JSON write
- dual/json 兼容保持

Phase C：
- audit/export CLI
- Storage Policy / Runtime Asset Policy 同步
- Console 查询如需要再接入

## 9. 验收测试

必须覆盖：

1. mysql 模式 reconcile 后：MySQL 有 report，JSON 不新增/不更新。
2. dual 模式：MySQL 与 JSON report SHA 对齐。
3. mysql 模式存在 stale JSON：`load_latest()` 返回 DB report。
4. DB document byte-size mismatch / SHA mismatch 均 FAIL。
5. Ledger/Queue recovery 已完成但 reconciliation persist 失败时，不重复调用 Provider。
6. report 不可驱动 Queue mutation、Ledger mutation、Episode stage transition。
7. Frame05 类 `LEDGER_READY_REPLAYED` 能完整保存和审计。
8. migration/import 不改变原始 `reconciled_at`。

## 10. 不做事项

本方案不实现：
- 不修改 image scheduler。
- 不新增 scheduler。
- 不改变 Production Ledger authority。
- 不改变 Recovery Journal authority。
- 不引入新的 state machine。
- 不把 reconciliation report 变成恢复输入。
- 不在本轮修改代码或 schema。

## 11. 最终目标状态

`MySQL Production Ledger = production result authority`

`MySQL Production Recovery Journal = mutable recovery transaction authority`

`Redis Production Queue = hot-state authority`

`MySQL Production Reconciliation = durable audit evidence`

`production-reconciliation.json = optional projection/export`

这样可以完成 JSON durable evidence 收口，同时保持现有 recovery 决策边界不变。