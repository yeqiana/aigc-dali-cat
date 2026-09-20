import { AlertCircle, CheckCircle2, Circle, LoaderCircle, RotateCw } from 'lucide-react';
import type { RuntimeStep } from '../types/monitoring';

function runtimeStepMeta(status: string) {
  const normalized = status.toUpperCase();
  if (['COMPLETED', 'PASSED', 'SUCCESS'].includes(normalized)) {
    return { label: normalized, tone: 'text-[var(--success)]', Icon: CheckCircle2 };
  }
  if (['FAILED', 'BLOCKED', 'ERROR'].includes(normalized)) {
    return { label: normalized, tone: 'text-[var(--danger)]', Icon: AlertCircle };
  }
  if (['RETRYING', 'RECOVERING'].includes(normalized)) {
    return { label: normalized, tone: 'text-[var(--retry)]', Icon: RotateCw };
  }
  if (['RUNNING', 'ACTIVE', 'IN_PROGRESS'].includes(normalized)) {
    return { label: normalized, tone: 'text-[var(--info)]', Icon: LoaderCircle };
  }
  return { label: normalized || 'WAITING', tone: 'text-[var(--text-tertiary)]', Icon: Circle };
}

export default function RuntimeTimeline({ steps = [] }: { steps?: RuntimeStep[] }) {
  return (
    <section className="storyos-surface overflow-hidden">
      <header className="h-9 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
        <h3 className="text-[12px] font-semibold text-[var(--text-primary)]">Execution Timeline</h3>
        <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{steps.length} STEPS</span>
      </header>
      {steps.length === 0 ? (
        <div className="px-3 py-8 text-center text-[11px] text-[var(--text-tertiary)]">
          暂无 Runtime step。加载 Execution 后显示完整生产链。
        </div>
      ) : (
        <ol className="divide-y divide-[var(--border-subtle)]">
          {steps.map((step, index) => {
            const meta = runtimeStepMeta(step.status);
            const Icon = meta.Icon;
            return (
              <li key={`${step.name}-${index}`} className="h-10 px-3 flex items-center gap-3 hover:bg-[var(--bg-hover)]">
                <span className="w-5 text-right text-[10px] font-mono text-[var(--text-disabled)]">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <Icon
                  className={`w-3.5 h-3.5 shrink-0 ${meta.tone} ${
                    meta.label === 'RUNNING' || meta.label === 'IN_PROGRESS' ? 'animate-spin' : ''
                  }`}
                />
                <span className="flex-1 min-w-0 truncate text-[12px] font-medium text-[var(--text-primary)]">
                  {step.name}
                </span>
                <span className={`text-[10px] font-mono font-medium ${meta.tone}`}>{meta.label}</span>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
