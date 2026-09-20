import type { RuntimeState } from '../types/monitoring';

export function RuntimeMonitor({ state }: { state?: RuntimeState }) {
  const status = (state?.status ?? 'UNKNOWN').toUpperCase();
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
        <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Current Step</div>
        <div className="mt-0.5 text-[12px] text-[var(--text-primary)]">{state?.currentStep ?? '-'}</div>
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Worker</div>
        <div className="mt-0.5 text-[12px] font-mono text-[var(--text-secondary)]">{state?.workerId ?? '-'}</div>
      </div>
      <div className="ml-auto">
        <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Heartbeat</div>
        <div className="mt-0.5 text-[11px] font-mono text-[var(--text-secondary)]">{state?.heartbeatTime ?? '-'}</div>
      </div>
    </section>
  );
}
