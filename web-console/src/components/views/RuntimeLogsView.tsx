import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, RefreshCw, Search, Terminal } from 'lucide-react';
import { runtimeApi } from '../../api/runtime';
import type { RuntimeEventItem } from '../../types/platform';

const PAGE_SIZE = 50;

function displayTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export const RuntimeLogsView: React.FC = () => {
  const [rows, setRows] = useState<RuntimeEventItem[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [episodeDraft, setEpisodeDraft] = useState('');
  const [episodeId, setEpisodeId] = useState('');

  async function load(pageOffset = offset, activeEpisodeId = episodeId) {
    setLoading(true);
    setError(null);
    try {
      const page = await runtimeApi.listEvents(PAGE_SIZE, pageOffset, activeEpisodeId);
      setRows(page.items);
      setOffset(page.offset);
      setHasMore(page.has_more);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Runtime Event 读取失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(offset, episodeId);
  }, [offset, episodeId]);

  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    if (!keyword) return rows;
    return rows.filter((row) =>
      [row.event_type, row.aggregate_type, row.aggregate_id, row.episode_id, row.trace_id, row.task_id]
        .some((value) => String(value || '').toLowerCase().includes(keyword))
    );
  }, [query, rows]);

  return (
    <div id="runtime-logs-view" className="space-y-3 text-[var(--text-secondary)]">
      <header className="flex flex-col gap-3 border-b border-[var(--border-subtle)] pb-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Production / Events</div>
          <div className="mt-1 flex items-center gap-2">
            <Terminal className="h-4 w-4 text-[var(--primary)]" />
            <h2 className="text-[18px] font-semibold text-[var(--text-primary)]">Runtime Events</h2>
            <span className="storyos-status storyos-status--success font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--success)]" />
              MYSQL TB_EVENT_LOG · READ ONLY
            </span>
          </div>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">
            只读展示 Runtime Event 标量摘要；PAYLOAD / METADATA 不在列表 API 暴露。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))} disabled={loading || offset === 0} className="storyos-control h-8 px-2.5 text-[11px] font-mono disabled:opacity-50">PREV</button>
          <button type="button" onClick={() => setOffset((value) => value + PAGE_SIZE)} disabled={loading || !hasMore} className="storyos-control h-8 px-2.5 text-[11px] font-mono disabled:opacity-50">NEXT</button>
          <button type="button" onClick={() => void load(offset, episodeId)} disabled={loading} className="storyos-control h-8 px-2.5 inline-flex items-center gap-1.5 text-[11px] font-mono disabled:opacity-50">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            REFRESH
          </button>
        </div>
      </header>

      {error && (
        <div className="storyos-surface flex items-center gap-2 px-3 py-2 text-xs text-[var(--danger)]">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <section className="storyos-surface overflow-hidden">
        <div className="min-h-11 px-3 py-1.5 border-b border-[var(--border-subtle)] flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-1 flex-col gap-2 lg:flex-row">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[var(--text-tertiary)]" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="当前页搜索 event / aggregate / trace / task" className="storyos-control h-8 w-full pl-8 pr-3 text-xs font-mono outline-none focus:border-[var(--focus)]" />
            </div>
            <form
              className="flex items-center gap-1.5"
              onSubmit={(event) => {
                event.preventDefault();
                setOffset(0);
                setEpisodeId(episodeDraft.trim());
              }}
            >
              <input
                value={episodeDraft}
                onChange={(event) => setEpisodeDraft(event.target.value)}
                placeholder="Episode ID · server filter"
                className="storyos-control h-8 w-[250px] max-w-full px-2.5 text-xs font-mono outline-none focus:border-[var(--focus)]"
                aria-label="Runtime Event Episode ID 服务端筛选"
              />
              <button type="submit" className="storyos-control h-8 px-2.5 text-[11px] font-mono">APPLY</button>
              {episodeId && (
                <button
                  type="button"
                  onClick={() => {
                    setEpisodeDraft('');
                    setOffset(0);
                    setEpisodeId('');
                  }}
                  className="storyos-control h-8 px-2.5 text-[11px] font-mono"
                >
                  CLEAR
                </button>
              )}
            </form>
          </div>
          <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
            {episodeId ? `EP ${episodeId} · ` : ''}PAGE {Math.floor(offset / PAGE_SIZE) + 1} · {rows.length ? `${offset + 1}-${offset + rows.length}` : '0'} · FILTERED {filtered.length}{hasMore ? ' · MORE AVAILABLE' : ''}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left text-xs">
            <thead className="h-9 border-b border-[var(--border-subtle)] bg-[var(--bg-workspace)] text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">
              <tr><th className="px-3">Time</th><th className="px-3">Event</th><th className="px-3">Aggregate</th><th className="px-3">Episode</th><th className="px-3">Trace</th><th className="px-3">Task</th></tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={6} className="px-3 py-10 text-center font-mono text-[var(--text-tertiary)]">{loading ? '正在读取 TB_EVENT_LOG…' : '没有匹配的 Runtime Event。'}</td></tr>
              ) : filtered.map((row) => (
                <tr key={row.event_id || `${row.event_type}-${row.occurred_at}`} className="h-11 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
                  <td className="px-3 whitespace-nowrap font-mono text-[11px] text-[var(--text-tertiary)]">{displayTime(row.occurred_at)}</td>
                  <td className="px-3 font-mono text-[11px] font-medium text-[var(--text-primary)]">{row.event_type || '—'}</td>
                  <td className="px-3 font-mono text-[11px] text-[var(--text-secondary)]">{row.aggregate_type || '—'} · {row.aggregate_id || '—'}</td>
                  <td className="px-3 font-mono text-[11px] text-[var(--text-secondary)]">{row.episode_id || '—'}</td>
                  <td className="px-3 font-mono text-[11px]">{row.trace_id ? <a href={`/traces?trace=${encodeURIComponent(row.trace_id)}`} className="text-[var(--text-secondary)] hover:text-[var(--primary)] hover:underline">{row.trace_id}</a> : '—'}</td>
                  <td className="px-3 font-mono text-[11px] text-[var(--text-tertiary)]">{row.task_id || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
