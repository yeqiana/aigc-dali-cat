import { useState } from 'react';
import { runtimeApi } from '../api/runtime';
import { RuntimeMonitor } from '../components/RuntimeMonitor';
import RuntimeTimeline from '../components/RuntimeTimeline';
import TraceGraph from '../components/TraceGraph';
import type { RuntimeExecutionState, RuntimeTraceState } from '../types/monitoring';

export default function RuntimeVisualization() {
  const [runtime, setRuntime] = useState<RuntimeExecutionState>();
  const [trace, setTrace] = useState<RuntimeTraceState>();
  const [executionId, setExecutionId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(id: string) {
    setLoading(true);
    setError(null);
    try {
      const [nextRuntime, nextTrace] = await Promise.all([
        runtimeApi.getExecutionRuntime(id),
        runtimeApi.getTrace(id),
      ]);
      setRuntime(nextRuntime);
      setTrace(nextTrace);
    } catch (cause) {
      setRuntime(undefined);
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
              Execution → Timeline → Trace，工程细节按需展开。
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

        {error && (
          <div className="storyos-surface px-3 py-2 text-xs text-[var(--danger)] border-[var(--danger)]">
            {error}
          </div>
        )}

        <RuntimeMonitor
          state={
            runtime
              ? {
                  executionId: runtime.executionId ?? executionId,
                  status: runtime.status ?? 'UNKNOWN',
                  currentStep: runtime.currentStep,
                  workerId: runtime.workerId,
                  heartbeatTime: runtime.heartbeatTime,
                }
              : undefined
          }
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <RuntimeTimeline steps={runtime?.steps ?? []} />
          <TraceGraph nodes={trace?.nodes ?? []} />
        </div>
      </div>
    </div>
  );
}
