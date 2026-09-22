# Trace DB Governance

日期：2026-09-21

## 当前索引

`TB_TRACE_SPAN` 已有：

- `PRIMARY KEY (SPAN_ID)`：物理幂等键；
- `INDEX_TB_TRACE_SPAN_TRACE_ID (TRACE_ID)`：按 Trace 查询；
- `INDEX_TB_TRACE_SPAN_EPISODE (EPISODE_ID)`：按 Episode 查询；
- 本次补入 canonical schema 的 `INDEX_TB_TRACE_SPAN_START_TIME (START_TIME)`：支撑最近 Span 排序。

`SPAN_ID` 主键已经覆盖单列 span 查询；没有另建第二套表或 authority。

## Migration 状态

`CREATE TABLE IF NOT EXISTS` 不会为已存在表增加新索引，因此 `scripts/phase9_storage_cutover_finalize.py` 已增加幂等 `_ensure_index()`，下次明确执行 storage cutover/upgrade 时会只补缺失索引。当前本机 MySQL 3306 未监听，本轮没有伪造“已执行 migration”的结果。

## 查询能力

Trace API 采用有界分页：`TRACE_ID` 精确筛选、`EPISODE_ID` 筛选、`START_TIME DESC, SPAN_ID DESC` 排序，limit 1–100，offset 非负。列表只读 `TB_TRACE_SPAN`。

## 架构决策记录

是否把物理主键迁移为 `(TRACE_ID, SPAN_ID)`、是否增加 typed `WORKFLOW_RUN_ID/WORKFLOW_ID`，需要基于现网索引/数据量和查询负载单独决策；本次保留现有兼容 schema。
