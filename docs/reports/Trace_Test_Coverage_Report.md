# Trace Test Coverage Report

日期：2026-09-21

## 已执行

- `python -m pytest tests/platform tests/system -q -p no:cacheprovider`
- targeted Trace/Runtime/API tests：31 passed（首轮修复后）
- `npm run lint`（`web-console`）：通过

## 覆盖范围

- TraceObserver RUNNING → terminal 同 identity 保存；
- Agent Runtime 的 `workflow_run_id -> TraceContract.run_id`；
- MySQL Trace save/get/list 分页 SQL；
- Trace API 的有界 list 参数与兼容 get；
- legacy runtime trace 无上下文时拒绝写入 Span；
- 既有 Runtime Event route catalog 与 Web Console contract。

## 现有缺口

本地 MySQL 3306 当前未监听，无法在本轮执行真实 `TB_TRACE_SPAN` 写后读、索引 migration 和生产数据行级验收；这些不能用 mock 结果替代。需在 MySQL 可用的环境补做 live smoke，并确认首个真实 Span 后再宣布最终 Production Ready。
