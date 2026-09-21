import { FormEvent, useState } from 'react';
import { AlertTriangle, GitBranch, Search } from 'lucide-react';
import { traceApi } from '../api/trace';
import type { TraceRecord } from '../types/platform';

export default function TraceExplorer() {
  const [id, setId] = useState('');
  const [trace, setTrace] = useState<TraceRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(event?: FormEvent) {
    event?.preventDefault();
    const traceId = id.trim();
    if (!traceId || loading) return;
    setLoading(true);
    setError(null);
    try {
      setTrace(await traceApi.get(traceId));
    } catch (cause) {
      setTrace(null);
      setError(cause instanceof Error ? cause.message : 'Trace 查询失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6">
      <div className="max-w-5xl mx-auto space-y-4">
        <header className="pb-3 border-b border-[var(--border-subtle)]">
          <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Platform / Trace</div>
          <h1 className="mt-1 text-xl font-semibold">Trace Explorer</h1>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">按 Trace ID 读取 Platform Trace 事实记录。</p>
        </header>
        <form onSubmit={load} className="storyos-surface min-h-12 px-3 py-2 flex flex-col sm:flex-row sm:items-center gap-2">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <input value={id} onChange={(event) => setId(event.target.value)} placeholder="trace id" aria-label="Trace ID" className="storyos-control w-full h-8 pl-8 pr-3 font-mono text-xs outline-none focus:border-[var(--focus)]" />
          </div>
          <button type="submit" disabled={!id.trim() || loading} className="h-8 px-3 rounded-[var(--radius-md)] bg-[var(--primary)] text-white text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed">{loading ? '查询中…' : '查询 Trace'}</button>
        </form>
        {error && <div className="storyos-surface px-3 py-2 flex items-start gap-2 text-xs text-[var(--danger)] border-[var(--danger)]"><AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /><span>{error}</span></div>}
        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <div className="flex items-center gap-2"><GitBranch className="w-3.5 h-3.5 text-[var(--info)]" /><h2 className="text-xs font-semibold">Trace Record</h2></div>
            <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{trace ? 'LIVE API' : 'NO RESULT'}</span>
          </header>
          {trace ? (
            <div className="divide-y divide-[var(--border-subtle)] text-xs">
              <div className="min-h-10 px-3 py-2 grid grid-cols-[120px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Trace ID</span><code className="font-mono text-[var(--text-primary)] break-all">{trace.trace_id}</code></div>
              <div className="min-h-10 px-3 py-2 grid grid-cols-[120px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Span ID</span><code className="font-mono break-all">{trace.span_id}</code></div>
              <div className="min-h-10 px-3 py-2 grid grid-cols-[120px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Operation</span><code className="font-mono">{trace.operation}</code></div>
              <div className="min-h-10 px-3 py-2 grid grid-cols-[120px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Status</span><span className="font-mono text-[var(--text-primary)]">{trace.status}</span></div>
              <div className="min-h-10 px-3 py-2 grid grid-cols-[120px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Task / Episode</span><code className="font-mono">{trace.task_id ?? '-'} / {trace.episode_id ?? '-'}</code></div>
              <div className="min-h-10 px-3 py-2 grid grid-cols-[120px_1fr] gap-3"><span className="text-[var(--text-tertiary)]">Duration</span><code className="font-mono">{trace.duration_ms ?? '-'} ms</code></div>
            </div>
          ) : <div className="px-3 py-10 text-center text-xs text-[var(--text-tertiary)]">输入 Trace ID 后查询。</div>}
        </section>
      </div>
    </main>
  );
}
