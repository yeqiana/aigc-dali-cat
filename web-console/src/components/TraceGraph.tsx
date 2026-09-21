import type { TraceRecord } from '../types/platform';

export default function TraceGraph({ trace, error }: { trace?: TraceRecord; error?: string | null }) {
  return (
    <section className="storyos-surface overflow-hidden">
      <header className="h-9 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
        <h3 className="text-[12px] font-semibold text-[var(--text-primary)]">Trace Fact</h3>
        <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{trace ? trace.status : 'NO TRACE'}</span>
      </header>
      {error ? (
        <div className="px-3 py-8 text-center text-[11px] text-[var(--warning)]">{error}</div>
      ) : !trace ? (
        <div className="px-3 py-8 text-center text-[11px] text-[var(--text-tertiary)]">
          暂无 Trace 证据。
        </div>
      ) : (
        <div className="divide-y divide-[var(--border-subtle)] text-[11px]">
          <div className="px-3 py-2 grid grid-cols-[90px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Operation</span><code>{trace.operation}</code></div>
          <div className="px-3 py-2 grid grid-cols-[90px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Trace ID</span><code className="break-all">{trace.trace_id}</code></div>
          <div className="px-3 py-2 grid grid-cols-[90px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Span ID</span><code className="break-all">{trace.span_id}</code></div>
          <div className="px-3 py-2 grid grid-cols-[90px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Task</span><code>{trace.task_id ?? '-'}</code></div>
          <div className="px-3 py-2 grid grid-cols-[90px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Episode</span><code>{trace.episode_id ?? '-'}</code></div>
          <div className="px-3 py-2 grid grid-cols-[90px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Duration</span><code>{trace.duration_ms ?? '-'} ms</code></div>
        </div>
      )}
    </section>
  );
}
