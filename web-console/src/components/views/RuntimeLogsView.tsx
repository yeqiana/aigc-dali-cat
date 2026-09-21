import React from 'react';
import { AlertTriangle, Terminal } from 'lucide-react';

export const RuntimeLogsView: React.FC = () => {
  return (
    <div id="runtime-logs-view" className="space-y-3 text-[var(--text-secondary)]">
      <header className="border-b border-[var(--border-subtle)] pb-3">
        <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Production / Logs</div>
        <div className="mt-1 flex items-center gap-2">
          <Terminal className="h-4 w-4 text-[var(--text-tertiary)]" />
          <h2 className="text-[18px] font-semibold text-[var(--text-primary)]">Runtime Logs</h2>
          <span className="storyos-status storyos-status--warning font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-[var(--warning)]" />
            CAPABILITY NOT CONNECTED
          </span>
        </div>
        <p className="mt-1 text-xs text-[var(--text-tertiary)]">当前 Platform API 没有生产日志流接口，因此这里不展示前端伪造日志。</p>
      </header>

      <section className="storyos-surface px-4 py-5">
        <div className="flex items-start gap-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--warning)]" />
          <div>
            <div className="text-xs font-medium text-[var(--text-primary)]">没有可验证的 Runtime Log Source</div>
            <p className="mt-1 max-w-2xl text-xs leading-5 text-[var(--text-secondary)]">
              在后端提供日志/事件查询 capability 之前，Web Console 不会用静态数组模拟 Scheduler、QualityGate 或 Provider 实时日志。
            </p>
            <div className="mt-3 flex items-center gap-2">
              <a href="/runtime" className="storyos-control h-8 px-2.5 inline-flex items-center text-[11px] font-mono">RUNTIME STATUS</a>
              <a href="/traces" className="storyos-control h-8 px-2.5 inline-flex items-center text-[11px] font-mono">TRACE EXPLORER</a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
