# Phase 9 - P9.26.5 Runtime Data Dual Write Migration

日期：2026-09-10
分支：story-platform-v3
验证方式：本机 Python 3.12.10 + pymysql 1.4.6，真实实例 121.89.82.216:9000

## 结论

P9.26.5 完成：Legacy(JSONL) 与 MySQL 已建立双写通道，三条事实（Event / Trace / Artifact）通过统一的 DualWrite 包装同时落两侧，并保留 `secondary_enabled` 作为回滚开关。真实 MySQL 实例上写入验证通过。

## 1. 背景

P9.26.4 只完成了 MySQL 侧持久化能力，生产写入链路仍然只走 JSONL。本阶段在不改变既有 Legacy 语义的前提下补上副写通道，为一致性校验（P9.26.6）提供双份数据。

## 2. 写入语义

```
save(entity)
  -> legacy.append(entity)        # 主链路，语义不变
  -> mysql.save(entity)           # 副写，幂等 upsert
```

- 主写先执行。Legacy 仍是当前唯一被读取的事实来源。
- `secondary_enabled=False` 或未注入 MySQL Repository 时返回 `{"legacy": "OK", "mysql": "SKIPPED"}`，即回滚开关。
- MySQL 写失败时异常向上抛出（fail-loud），不做静默降级；由此产生的不一致由 P9.26.6 巡检发现并补偿。

## 3. 代码改动

新增双写层：

- platform/repository/dual_write/__init__.py
- platform/repository/dual_write/runtime_dual_write.py —— DualWriteEventRepository / DualWriteTraceRepository / DualWriteArtifactRepository

为巡检补齐读取能力：

- platform/event/jsonl_event_store.py、platform/trace/jsonl_trace_store.py、platform/artifact/jsonl_artifact_store.py 各增加 read_all() 与 read_by_id()
- 三个 MySQL Repository 各增加 list_all()

向后兼容：

- platform/repository/event_repository.py 改为从 dual_write 包 re-export `DualWriteEventRepository`，既有导入路径继续可用（有测试锁定）。

## 4. 测试

tests/platform/test_runtime_dual_write.py：4 例

| 用例 | 覆盖 |
| --- | --- |
| test_dual_write_writes_both_stores | 两侧均写 |
| test_dual_write_skips_mysql_when_disabled | secondary_enabled=False 回滚开关 |
| test_dual_write_legacy_only_without_mysql | 未注入 MySQL 时仅写 Legacy |
| test_event_repository_reexport_backward_compatible | 旧导入路径兼容 |

tests/platform 全量：137 passed / 0 failed。

## 5. 风险与限制

- 双写不是事务：Legacy 与 MySQL 之间没有跨存储原子性，只能靠一致性巡检收敛。
- 无生产调用方接线：本阶段的 DualWrite 目前只被测试与验证脚本使用，正式接线在 P9.27 生产数据基础阶段决定。
- MySQL 写失败当前逐条抛出，未做重试/缓冲；是否需要降级或补偿队列，留到 P9.27 结合真实生产链路决定。

