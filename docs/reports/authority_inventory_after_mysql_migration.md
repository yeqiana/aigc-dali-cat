# Authority Inventory After MySQL Migration

日期：2026-09-20  
范围：Production / Character / Recovery 相关 JSON authority 残留审计。

## 1. 当前存储模式

`config/storyos.yaml` 当前配置：
- `storage.runtime_store.mode=mysql`
- `storage.episode_meta_store.mode=mysql`
- `storage.hot_state.mode=redis`

因此：
- Runtime durable facts：MySQL authority
- Episode structured metadata：MySQL authority
- Hot/rebuildable state：Redis authority
- 文件仍可作为 Artifact、derived cache、projection、legacy compatibility 或 export，但不得在 MySQL 模式下静默重新成为结构化状态 authority。

## 2. 分类清单

| 对象 | 当前真实 authority / 角色 | JSON 当前分类 | 迁移状态 | 结论 |
|---|---|---|---|---|
| `meta/production-ledger.json` | `TB_PRODUCTION_LEDGER_AUTHORITY`；typed frame/attempt 表为 query projection | projection / compatibility / export | authority 已切 MySQL；legacy 路径字符串仍广泛存在 | **不是 authority**。MySQL 模式必须经 `production_ledger.load_authority()` |
| `meta/character-contract.json` | MySQL Episode Contract repository，经 `episode_contract_persistence.load_latest()` | projection / legacy compatibility / export | authority 已切 MySQL | **不是 authority**。当前文件 SHA 可与 MySQL authority SHA 不同 |
| `meta/character-visual-contract.json` | MySQL Episode Contract repository，经 `episode_contract_persistence.load_latest()` | projection / legacy compatibility / export | authority 已切 MySQL | **不是 authority** |
| `meta/runtime/contracts/character-appearance-anchor.json` | 由 MySQL Character Contract + Character Visual Contract + World Identity 派生 | cache | derived cache 仍保留文件；Storage Policy 目标为 MySQL / REMOVE_AFTER_CUTOVER | **不是独立 authority**；`verify()` 以当前 authority 重建后比对 |
| `meta/runtime/production-commit-journal.json` | `TB_PRODUCTION_RECOVERY_JOURNAL` 保存 mutable recovery transaction | compatibility / export（json/dual 模式） | authority 已迁 MySQL；MySQL 模式 `_journal()` persist 后直接 return，不写 JSON | **不是 MySQL 模式 authority**；JSON 仅兼容 |
| `meta/runtime/production-reconciliation.json` | reconcile 结果摘要 | artifact / projection | 每次 reconcile 仍写 JSON；Storage Policy 目标 MySQL / REMOVE_AFTER_CUTOVER | **不是业务 authority**，但仍是待迁移 durable evidence |
| `meta/image-workers/*.lifecycle.json` | worker-local lifecycle evidence | artifact / local recovery evidence | Storage Policy 将 image-worker logs 定义为 LOCAL_ONLY；durable attempt facts 进 MySQL | **不是最终 Ledger authority** |
| `meta/provider-receipts/*.json` | Provider 调用执行证据 | artifact | Storage Policy 目标 MySQL；Frame05 Ledger 显示 receipt `storage_source=mysql` | **证据，不是 authority** |
| `meta/production-queue.json` | Redis Production Queue hot-state authority（canonical loader） | cache / compatibility | 当前 Redis 模式禁止文件 fallback；本轮已移除 `QUEUE` 1800 秒 TTL | **文件不是 authority**；Redis pending Queue 当前无 TTL，避免空闲验收窗口静默丢 item |

## 3. Production Ledger

### Authority

当前完整文档 authority：
- 表：`TB_PRODUCTION_LEDGER_AUTHORITY`
- 内容字段：`DOCUMENT_BLOB`
- 完整性：`SHA256 + BYTE_SIZE`
- typed query projection：`TB_PRODUCTION_FRAME` / `TB_PRODUCTION_ATTEMPT`

`production_ledger_persistence.py` 明确声明 typed frame/attempt 表只是 query projection，完整 Ledger 文档由 `TB_PRODUCTION_LEDGER_AUTHORITY` 保存。

### 已验证的无文件回退

系统测试覆盖：
- MySQL 模式存在 stale `meta/production-ledger.json` 时，`load_authority()` 返回 DB 文档。
- `get_ledger()` 也使用 DB authority，不接受 stale compatibility file。

本轮真实 MySQL drill 进一步验证：
- begin/pending 持久化
- 进程退出
- 新进程 recover
- success 写回
- 再读一致

结论：Production Ledger 的 authority 切换已经成立。

### 残留字符串不等于残留 authority

扫描仍发现大量 `meta/production-ledger.json` 字符串，主要分为：
1. 测试 fixture：直接造 legacy JSON 测试数据。
2. evidence 路径名：Runtime DAG、resume capsule、final snapshot 等用逻辑名称表达证据。
3. compatibility/export 路径：导出、迁移、历史兼容。
4. 少量需继续治理的 direct file consumer。

因此不能仅按 grep 命中数判断“还在用 JSON authority”；必须看调用是否经过 authority facade。

## 4. Character Contract / Character Visual Contract

两者当前 loader 都是：
`episode_contract_persistence.load_latest(..., legacy_path=...)`

在 `episode_meta_store.mode=mysql` 下，MySQL 是 authority。

《尸解仙》本轮观测到：
- Character Contract 文件 SHA：`cd14312235a129548d6ad3cae5764c1974433b0f9ec71c2705c37c23c88ae84f`
- Character Contract MySQL authority SHA：`52e49fd5007bbbed4b5085d9bbcdd3299c5b483cb2dc0569163b9db62f5be785`
- Character Visual 文件 SHA：`2786f92c3f05a8be2e0b82f8e44fb477330cfea44c0c629c546b6510f033c514`
- Character Visual MySQL authority SHA：`6a891ab430e27bab5f770668265b25fb5df43d1846b160cd6e9d32090e2fe2fa`

这类 SHA 差异本身不是 authority drift 证据，因为文件已经不是主 authority。比较生产依赖时必须使用模块的 `authority_sha256()`，不能直接对 legacy JSON 文件做 SHA 判断。

## 5. Character Appearance Anchor

`character-appearance-anchor.json` 是明确的 `derived_cache=true`。

本轮：
- 文件 SHA：`ff63746e0540eb432477ed4f3ff7b37c0f00e71a6fc2321c61d62884b5281310`
- 内部 Character Contract authority SHA：`52e49fd5007bbbed4b5085d9bbcdd3299c5b483cb2dc0569163b9db62f5be785`
- 内部 Character Visual authority SHA：`6a891ab430e27bab5f770668265b25fb5df43d1846b160cd6e9d32090e2fe2fa`
- `character_appearance_anchor.py verify episodes/尸解仙`：PASS

结论：Appearance Anchor 本身未 stale；它正确跟随 MySQL authority，而不是 legacy 文件 SHA。

## 6. Runtime Journal

Production Recovery Journal authority 已完成 MySQL 迁移。

代码现状：
- `production_recovery_persistence.mode()` 读取 `episode_meta_store.mode`，当前为 `mysql`。
- `production_recovery._journal()` 在 mysql/dual 模式调用 `production_recovery_persistence.update_transaction()`。
- `production_recovery_persistence` 通过 `MySqlProductionRecoveryJournalRepository` 将 transaction 写入 `TB_PRODUCTION_RECOVERY_JOURNAL`。
- 表内保存 `TRANSACTION_ID / EPISODE_ID / PHASE / ITEM_ID / FRAME_NO / DOCUMENT_BLOB / SHA256 / BYTE_SIZE`，读取时校验 byte-size 与 SHA。
- MySQL 模式 persist 完成后 `_journal()` 立即 return，不会再原子更新 `meta/runtime/production-commit-journal.json`。
- 旧 JSON 路径只在 json/dual 兼容模式保留；它不再是 MySQL 模式 recovery authority。

结论：**Production Recovery Journal 的 JSON authority residual 已收口；MySQL 为唯一生产 authority。**

## 7. Reconciliation

`meta/runtime/production-reconciliation.json`：
- 每次 `reconcile_locked()` 最后写出 report。
- report 包含 item/frame/outcome/ledger_status/lifecycle_state。
- Frame05 本轮实际为：
  - `LEDGER_READY_REPLAYED`
  - `ORIGINAL_READY`
  - `SUCCEEDED`

该文件不驱动 Ledger、Queue 或 Episode stage，不参与下一轮 recovery 决策，属于 derived recovery evidence / projection。

结论：**projection / artifact，不是 authority。** 下一步只需要做持久化治理：MySQL durable evidence + 可选 JSON export/projection，不能把它升级成新的状态 authority。

## 8. 《尸解仙》Frame02 人物链检查

目标链：

`Frame Contract → Character Visual Contract → Appearance Anchor → Pixel Master → Reference Arbitration → Prompt Package → Redis Queue`

当前结果：
- Character Contract：MySQL authority 存在。
- Character Visual Contract：MySQL authority 存在。
- Appearance Anchor：verify PASS。
- Pixel Master：已恢复，SHA=`d6aaf0f185b21895128fe8b911902a12096487d19ede01a5244aa7dc3dba71c7`，与冻结元数据一致。
- P01 crop：已恢复，SHA=`3c6fb2aec0da6a4032eed3e7f862d4a61538aa5d592c4d47c287b4610dea87c8`。
- P02 crop：已恢复，SHA=`76117ea5e0e5aa28197a3584175ab671638eb5f8712a4fffc1de9753ac0d7d4f`。
- Frame02：当前 `contract_sha256=13a41c746c21fa45e471b94bf70a515e3b8cbecb6a2d800ed0cc0a91269db5a7`，`verify_frame()` PASS。
- Identity Requirements：P02、P01 均为 `anchor_state=bound`，各自 anchor SHA 与 crop SHA 一致。
- Reference Arbitration（batch）：PASS；最终两条引用为 P02 crop + P01 crop。
- Prompt Package：MySQL persistence 已存在，`frame_contract_sha256` 与当前合同一致，`package_sha256=ff0d868f8736d7679bd62ac75bdcf568a81697bad87614bd7f908ab7f237e6e8`。
- Redis Queue：初次审计 Frame02 item=`c1554c7d2741`，`status=queued`、`attempts=0`；Queue 中合同、Prompt Package、P01/P02 reference SHA 均对齐。
- 收尾复核发现 Redis Queue key 已消失，而 Ledger 仍为 `PENDING / attempts=[]` 且无 Frame02 worker/receipt/candidate；定位为 `QUEUE` 固定 1800 秒 TTL 到期，不是生产消费。
- 已将 `QUEUE` TTL 改为 `None`，并在重新校验 Contract / prompt / crop SHA 后恢复原 item。
- 随后通过现有 image scheduler 单 worker 消费该 item；最终 Queue=`generated / attempts=1`，execution phase=`COMMITTED`。
- RAW SHA=`ae3c99093e12f6b9641efbfad87d320b758cc391ace22f3009436353684f8951`；Candidate SHA=`48c558b1dc8125dc8b49bde9f1b2c7b930bfe9abcf6579f8771f3ca97cb5f9d7`。
- Provider Receipt authority 已写 MySQL，receipt id=`PR_9838f9fa3434ba1f80fa8ad2100f97ecdd472289`；旧 JSON path 仅为 legacy locator。
- MySQL Ledger=`ORIGINAL_READY`，Provider status=`COMPLETED`，reference execution=`verified=true`。
- Recovery transaction=`506e5a730be7429c8ba61d30bd2a548f`，phase=`COMMITTED`；reconcile 复跑=`LEDGER_READY_REPLAYED` 且 attempt 数仍为 1。
- 单图规则审计 identity continuity findings=0、Visual Profile PASS；最终语义 Critic 仍需等待整集 frame-set 可审核。

## 9. 当前分类汇总

### authority

- MySQL：Production Ledger、Character Contract、Character Visual Contract 等结构化 durable facts。
- Redis：Production Queue hot-state authority；本轮已将 pending Queue 调整为无 TTL，避免未消费任务因空闲时间过期。
- Production Recovery Journal：MySQL `TB_PRODUCTION_RECOVERY_JOURNAL` authority；旧 JSON 仅 json/dual compatibility/export。

### projection

- legacy `production-ledger.json`（MySQL 模式下仅 compatibility/export 视图）
- legacy Character Contract / Character Visual JSON（MySQL 模式下不应作为结构化 authority）
- `production-reconciliation.json` 的当前 report 视图

### cache

- `character-appearance-anchor.json`
- Frame Contract JSON
- Frame Contract index
- Prompt Package 等可从 authority 重建的派生资产

### artifact

- worker lifecycle/log
- provider receipt
- candidate/raw image
- reconciliation evidence
- export/snapshot evidence

## 10. 后续治理优先级

P2：
- 按 `docs/reports/production_reconciliation_mysql_projection_closure_plan_20260921.md` 收口 `production-reconciliation.json`：MySQL 保存 durable evidence，JSON 仅作为可选 export/projection；不得成为 recovery authority。

P2：
- 继续收敛 active runtime 中直接检查 legacy JSON 文件存在性的 consumer；逻辑 evidence 名称可保留，但 authority read 必须统一走 repository/facade。

Production 执行项：
- Frame02 已完成真实 Provider 出图、Candidate commit、MySQL Ledger 与 Recovery 闭环，不应再次生成。
- 后续只需在整集生产资产齐全后进入 Final Semantic Critic；不得为了单图验收提前绕过 frame-set 审核边界。

## 11. 本轮结论

MySQL migration 的核心 Production Ledger authority 与 Production Recovery Journal authority 均已完成数据库化，并由定向测试覆盖。

当前明确仍需治理的 `production-reconciliation.json` 是 **projection / durable evidence**，不是 authority；其收口目标是 MySQL evidence + 可选 JSON export，而不是创建新的恢复状态机。

Frame02 的 Pixel Master、P01/P02 crop、Frame Contract、Identity Requirements、Reference Arbitration、Prompt Package 已对齐。本轮额外发现并修复 Redis Queue 1800 秒 TTL 导致待生产 item 静默过期的问题，并完成一次真实 Provider 出图：当前 Queue=`generated`、Ledger=`ORIGINAL_READY`、Recovery=`COMMITTED`、Candidate SHA=`48c558b1dc8125dc8b49bde9f1b2c7b930bfe9abcf6579f8771f3ca97cb5f9d7`。最终 Semantic PASS 仍按整集 frame-set gate 等待其余生产帧，不提前放行。
