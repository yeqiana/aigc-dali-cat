# Trace Context Audit

日期：2026-09-21  
范围：Runtime Request → Workflow Execution → Agent Runtime → Trace Observer → Trace Repository

## 结论

- legacy StoryOS Runtime Trace 在 `episodes/_system/runtime_trace.py` 的 `start_run()` 生成 `ST_...` trace_id，`start_span()` 生成 `SP_...` span_id；workflow DAG 将同一 `trace_id/run_id` 显式传入 span。
- Platform Agent Runtime 在 `TraceObserver.start()` 生成 `trace_.../span_...`，原先只在内存中保存完成态；默认应用现在把同一个 Observer 接到 `MySqlTraceRepository`，RUNNING 与完成态使用同一 span identity upsert。
- `AgentContext.workflow_run_id` 现在进入 `TraceContract.run_id`，并由 repository 放入 `TB_TRACE_SPAN.ATTRIBUTES.run_id`。这是真实关联，不把 Event Log 复制为 Span。
- 原有风险是 current pointer 丢失时仍会生成无 trace_id 的 `SPAN_START/SPAN_END`。已改为 fail-closed：上下文不可解析时抛出 `TraceContextUnavailable`，不写入不可关联事件。

## 生命周期

```text
Runtime Request
  -> workflow run_id
  -> AgentContext.workflow_run_id
  -> TraceObserver.start(trace_id, span_id, run_id)
  -> TB_TRACE_SPAN (RUNNING)
  -> TraceObserver.save(same trace_id/span_id)
  -> TB_TRACE_SPAN (terminal)
```

## 未决项

当前 `TB_TRACE_SPAN` 没有独立 `WORKFLOW_RUN_ID` / `WORKFLOW_ID` typed 列；本次只用已有 ATTRIBUTES 保存 `run_id`，不执行 schema 扩张。若未来需要按 workflow 高选择性查询，应单独评审 migration。
