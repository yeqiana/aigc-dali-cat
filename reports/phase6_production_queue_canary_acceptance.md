# Phase 6 Production Queue Canary Acceptance

更新时间：2026-09-16

## 1. 范围

本阶段只验收 Production Queue authority 的隔离 Canary 切换，不迁移、不激活任何真实 Episode。

目标链路：

`Legacy authority → guarded activate → Runtime Workspace authority → Scheduler 写入 → RuntimeStatus / Recovery 读取边界验证 → guarded rollback → Legacy authority`

## 2. 安全前置

- [x] 当前无正在跑批故事。
- [x] 仓库真实 Episode 中 `production-queue-activation.json` 扫描结果为 **0**。
- [x] Canary 使用 disposable temp root，不复用任何真实 Episode 路径。
- [x] Legacy Queue 在 ACTIVE 期间保留且冻结，不删除。
- [x] Formal Evidence / Episode stage authority 不参与本次迁移。

## 3. Go / No-Go 清单

| 验收项 | 状态 | 说明 |
|---|---|---|
| 隔离 Canary 不触碰真实 Episode | ✅ | 临时 Episode + 临时 Runtime Workspace |
| 激活前 authority = Legacy | ✅ | 无 receipt 时保持历史语义 |
| activate 受统一 Scheduler Queue Lock 保护 | ✅ | 复用 `scheduler_core.queue_transaction()` |
| Legacy → Workspace copy + checksum verify | ✅ | stale/conflicting shadow fail-closed |
| activation receipt 最后写入 | ✅ | receipt 生效后 Store 才切换 authority |
| Scheduler 激活后只写 Workspace | ✅ | Legacy bytes 保持冻结 |
| RuntimeStatus 能识别 Queue source_kind | ✅ | Legacy=`episode`，ACTIVE=`runtime_workspace` |
| Recovery 读取当前 Store authority | ✅ | `production_queue_store.read_path(ep)` |
| Recovery 写回中央 Queue sink | ✅ | `scheduler_core.save_queue(ep, queue)` |
| rollback 前同步 Workspace 最新 Queue 回 Legacy | ✅ | 不丢 ACTIVE 期间最新 Queue |
| rollback 后 authority = Legacy | ✅ | receipt state=`ROLLED_BACK` |
| receipt 损坏 | ✅ | `invalid_fail_closed`，不静默回 Legacy |
| receipt 写失败（未提交） | ✅ | 明确 `BLOCKED`，不返回未知状态 |
| receipt 写后报错（已原子提交） | ✅ | 重新 inspect 后确认真实 state |
| 真实 Episode activation receipt | ✅ | **0 个** |

### NO-GO 条件

出现任一情况禁止真实 Episode 切换：

- Scheduler Queue 锁无法取得；
- Workspace shadow 与 Legacy checksum 冲突且没有已验证 activation receipt；
- activation receipt 结构、checksum、episode namespace 或 authority 文件无效；
- RuntimeStatus 无法解释当前 Queue authority；
- Recovery 绕过 Queue Store 或中央 `scheduler_core.save_queue()`；
- rollback 无法先同步 ACTIVE 期间最新 Workspace Queue；
- full System / Platform 回归失败；
- 真实 Episode 正在跑批或存在无法确认的 writer。

## 4. 本阶段故障注入

覆盖：

1. activation receipt 写入失败，marker 未提交；
2. activation marker 已原子提交，但写函数随后抛异常；
3. rollback receipt 写入失败，ACTIVE authority 必须维持；
4. rollback marker 已提交但随后抛异常；
5. receipt 字段/checksum 损坏；
6. stale/conflicting Workspace shadow。

设计原则：**宁可 BLOCKED，也不猜测 authority；可以通过重新 inspect 证明的已提交事务，不误报失败。**

## 5. 真实生产影响

本 Phase 6 **未对任何真实 Episode 执行 activate 或 rollback**。

真实 Episode 数据信息仅做只读扫描；Canary 的 Episode、Queue、receipt、lock 和 Workspace 全部位于临时目录并在运行结束后删除。

## 6. 提交边界

建议精确分组：

1. Canary Harness：`production_queue_canary.py` + 对应测试；
2. Cutover Fault Hardening：`production_queue_cutover.py` + 故障注入测试；
3. Cross-module Acceptance：Canary integration 测试 + 本验收报告；
4. Canonical Audit：最终全量回归通过后单独更新架构审计文档。

禁止混入：历史 Episode 资产、provider receipts、`docs/img*.png`、`unused/`、生产 prompts/queue/ledger 等既有脏区。

## 7. 验证结果

- Isolated Canary CLI：✅ PASS
- Queue Phase 6 聚焦回归：✅ **81 passed**
- RuntimeStatus / Recovery 集成：✅ **44 passed**
- Platform 全量：✅ **373 passed**
- System 全量：✅ **1038 passed / 1 skipped / 90 subtests passed**
- `git diff --check`：✅ PASS
- 真实 Episode activation receipt 终检：✅ **0 个**

## 8. 下一阶段边界

Phase 6 已全量通过，因此已经具备进入“**单个明确 opt-in、当前 idle 的真实 Episode**”切换验证的技术条件。但该步骤不属于本阶段，也不会自动执行；在没有明确选定 Canary Episode、确认 idle、定义观测窗口与回滚触发条件前，继续保持真实 Episode authority 不变。
