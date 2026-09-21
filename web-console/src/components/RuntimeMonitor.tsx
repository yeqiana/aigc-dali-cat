import type { ExecutionRecord } from '../types/platform';

export function RuntimeMonitor({ execution }: { execution?: ExecutionRecord }) {
  const status = (execution?.status ?? 'UNKNOWN').toUpperCase();
  const statusTone =
    ['FAILED', 'BLOCKED', 'ERROR'].includes(status)
      ? 'text-[var(--danger)]'
      : ['RUNNING', 'ACTIVE'].includes(status)
        ? 'text-[var(--info)]'
        : ['COMPLETED', 'PASSED', 'HEALTHY'].includes(status)
          ? 'text-[var(--success)]'
          : 'text-[var(--text-secondary)]';

  return (
    <section className="storyos-surface min-h-14 px-3 py-2 flex flex-wrap items-center gap-x-6 gap-y-2">
      <div>
        <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Runtime</div>
        <div className={`mt-0.5 flex items-center gap-1.5 text-[12px] font-mono font-medium ${statusTone}`}>
          <span className="w-1.5 h-1.5 rounded-full bg-current" />
          {status}
        </div>
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Agent</div>
        <div className="mt-0.5 text-[12px] font-mono text-[var(--text-primary)]">{execution?.agent_code ?? '-'}</div>
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Execution Type</div>
        <div className="mt-0.5 text-[12px] font-mono text-[var(--text-secondary)]">{execution?.execution_type ?? '-'}</div>
      </div>
      <div className="ml-auto">
        <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Updated</div>
        <div className="mt-0.5 text-[11px] font-mono text-[var(--text-secondary)]">{execution?.updated_time ?? '-'}</div>
      </div>
    </section>
  );
}
