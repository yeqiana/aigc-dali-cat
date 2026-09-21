# Runtime Event / Trace Model

日期：2026-09-21

## 唯一模型

```text
TB_EVENT_LOG  (canonical Event Authority, append/upsert facts)
  EVENT_TYPE=RUNTIME_TRACE_EVENT
  payload.event = SPAN_START | SPAN_END | RUNNER_EXIT
  TRACE_ID / TASK_ID / EPISODE_ID + payload.run_id 等关联字段
          |
          +--> Runtime Events API：只读 projection，支持服务端 episode_id 过滤

Trace Observer 真实 Span facts
  TraceContract -> TraceRepository -> TB_TRACE_SPAN
  一条事实是一个 span，RUNNING -> terminal 使用同一 identity upsert
          |
          +--> Trace API / Trace Explorer
```

## 禁止的关系

`TB_EVENT_LOG row copy -> TB_TRACE_SPAN` 不存在，也不应建立。Event 是事件事实；Span 是 Observer 实际采集并持久化的执行事实。两者可通过 trace/run/episode 关联，但不互相冒充。

## 字段审计

legacy runtime trace 显式传递 `trace_id`、`run_id`、`span_id`；Platform Trace Contract 现在保留 `trace_id`、`span_id`、`run_id`，`run_id` 进入 `ATTRIBUTES`。`workflow_id` 在现有 Event/Trace typed contract 中没有稳定来源，暂不推断或补造。

## 当前事实

用户提供的生产事实是 Event Log 有真实 Runtime Trace Event，而 `TB_TRACE_SPAN` 当前为空。本次不改变这个事实，也不以空表推导“历史 Span 已存在”。
