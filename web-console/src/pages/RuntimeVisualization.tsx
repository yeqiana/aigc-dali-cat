import { useEffect, useState } from 'react';
import { runtimeApi } from '../api/runtime';
import { RuntimeMonitor } from '../components/RuntimeMonitor';
import RuntimeTimeline from '../components/RuntimeTimeline';
import TraceGraph from '../components/TraceGraph';
import type { ExecutionRecord, RuntimeEpisodeStatusPage, TraceRecord } from '../types/platform';

export default function RuntimeVisualization() {
  const [episodeStatuses, setEpisodeStatuses] = useState<RuntimeEpisodeStatusPage>();
  const [episodeStatusLoading, setEpisodeStatusLoading] = useState(false);
  const [episodeStatusError, setEpisodeStatusError] = useState<string | null>(null);
  const [execution, setExecution] = useState<ExecutionRecord>();
  const [trace, setTrace] = useState<TraceRecord>();
  const [executionId, setExecutionId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [traceError, setTraceError] = useState<string | null>(null);

  async function loadEpisodeStatuses() {
    setEpisodeStatusLoading(true);
    setEpisodeStatusError(null);
    try {
      setEpisodeStatuses(await runtimeApi.listEpisodeStatuses(20, 0));
    } catch (cause) {
      setEpisodeStatuses(undefined);
      setEpisodeStatusError(cause instanceof Error ? cause.message : 'Episode Runtime Status 查询失败');
    } finally {
      setEpisodeStatusLoading(false);
    }
  }

  useEffect(() => {
    void loadEpisodeStatuses();
  }, []);

  async function load(id: string) {
    setLoading(true);
    setError(null);
    setTraceError(null);
    setTrace(undefined);
    try {
      const nextExecution = await runtimeApi.getExecution(id);
      setExecution(nextExecution);
      if (nextExecution.trace_id) {
        try {
          setTrace(await runtimeApi.getTrace(nextExecution.trace_id));
        } catch (cause) {
          setTraceError(cause instanceof Error ? cause.message : 'Trace 查询失败');
        }
      }
    } catch (cause) {
      setExecution(undefined);
      setTrace(undefined);
      setError(cause instanceof Error ? cause.message : 'Runtime 查询失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="storyos-shell min-h-screen p-4 lg:p-6">
      <div className="max-w-6xl mx-auto space-y-4">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between pb-3 border-b border-[var(--border-subtle)]">
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Platform / Runtime</div>
            <h2 className="text-[20px] leading-7 font-semibold text-[var(--text-primary)]">Runtime</h2>
            <p className="mt-0.5 text-[12px] text-[var(--text-tertiary)]">
              Episode Runtime Status 为只读生产投影；Execution → Timeline → Trace 为 Agent 执行事实。
            </p>
          </div>
          <form
            className="flex items-center gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (executionId.trim()) load(executionId.trim());
            }}
          >
            <input
              value={executionId}
              onChange={(event) => setExecutionId(event.target.value)}
              className="storyos-control h-8 w-56 px-2.5 font-mono text-[11px] outline-none focus:border-[var(--focus)]"
              aria-label="Execution ID"
              placeholder="execution id"
            />
            <button
              type="submit"
              disabled={!executionId.trim() || loading}
              className="storyos-control h-8 px-3 text-[12px] font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading…' : 'Load Runtime'}
            </button>
          </form>
        </header>

        <section className="storyos-surface overflow-hidden">
          <header className="min-h-10 px-3 py-2 border-b border-[var(--border-subtle)] flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-[12px] font-semibold text-[var(--text-primary)]">Episode Runtime Status</h3>
              <p className="text-[10px] text-[var(--text-tertiary)]">LIVE API · read-only projection · 不推进 Episode stage</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
                {episodeStatuses ? `${episodeStatuses.count} EPISODES${episodeStatuses.has_more ? ' · MORE' : ''}` : 'NO DATA'}
              </span>
              <button
                type="button"
                onClick={() => void loadEpisodeStatuses()}
                disabled={episodeStatusLoading}
                className="storyos-control h-7 px-2 text-[10px] font-mono disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {episodeStatusLoading ? 'REFRESHING…' : 'REFRESH'}
              </button>
            </div>
          </header>
          {episodeStatusError ? (
            <div className="px-3 py-6 text-center text-[11px] text-[var(--danger)]">{episodeStatusError}</div>
          ) : episodeStatuses?.items.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-[11px]">
                <thead className="h-9 border-b border-[var(--border-subtle)] text-[var(--text-tertiary)]">
                  <tr>
                    <th className="px-3 text-left">Episode</th>
                    <th className="px-3 text-left">Stage</th>
                    <th className="px-3 text-left">Execution</th>
                    <th className="px-3 text-left">Current Action</th>
                    <th className="px-3 text-left">Images</th>
                    <th className="px-3 text-left">Heartbeat</th>
                    <th className="px-3 text-left">User</th>
                  </tr>
                </thead>
                <tbody>
                  {episodeStatuses.items.map((row) => {
                    const generated = row.image_progress?.generated_frames ?? 0;
                    const expected = row.image_progress?.expected_frames ?? 0;
                    return (
                      <tr key={row.episode_ref} className="h-11 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
                        <td className="px-3 font-mono text-[var(--text-primary)]">{row.episode_ref}</td>
                        <td className="px-3 font-mono">{row.production_stage ?? '-'}</td>
                        <td className="px-3 font-mono">{row.execution_status}</td>
                        <td className="px-3 font-mono text-[var(--text-secondary)]">{row.current_action ?? row.next_step ?? '-'}</td>
                        <td className="px-3 font-mono">{generated}/{expected || '-'}</td>
                        <td className="px-3 font-mono text-[var(--text-secondary)]">{row.heartbeat?.health ?? '-'}</td>
                        <td className="px-3 font-mono">{row.needs_user ? 'NEEDS_USER' : '-'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="px-3 py-8 text-center text-[11px] text-[var(--text-tertiary)]">
              {episodeStatusLoading ? '正在读取 Episode Runtime Status…' : '没有可用 Episode Runtime Status。'}
            </div>
          )}
        </section>

        <div className="pt-1 text-[10px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Agent Execution Inspector</div>
        {error && (
          <div className="storyos-surface px-3 py-2 text-xs text-[var(--danger)] border-[var(--danger)]">
            {error}
          </div>
        )}

        <RuntimeMonitor execution={execution} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <RuntimeTimeline execution={execution} />
          <TraceGraph trace={trace} error={traceError} />
        </div>
      </div>
    </div>
  );
}
