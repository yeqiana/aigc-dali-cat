import { useEffect, useState } from 'react';
import { Activity, Brain, GitBranch, Workflow } from 'lucide-react';
import { apiGet } from '../api/client';

type Health = { status?: string };

export default function Dashboard() {
  const [status, setStatus] = useState('CHECKING');

  useEffect(() => {
    apiGet<Health>('/healthz')
      .then((row) => setStatus(row.status ?? 'UNKNOWN'))
      .catch(() => setStatus('DOWN'));
  }, []);

  const healthy = ['OK', 'HEALTHY', 'UP'].includes(status.toUpperCase());
  const tools = [
    { href: '/runtime', label: 'Runtime', desc: 'Episode Runtime Status + Execution / Trace', Icon: Activity },
    { href: '/executions', label: 'Executions', desc: '按 Execution ID 查询事实记录', Icon: Workflow },
    { href: '/traces', label: 'Traces', desc: '按 Trace ID 查询链路记录', Icon: GitBranch },
    { href: '/memory', label: 'Memory', desc: '检索 Experience / Memory Store', Icon: Brain },
  ];

  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6">
      <div className="max-w-5xl mx-auto space-y-4">
        <header className="pb-3 border-b border-[var(--border-subtle)]">
          <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">StoryOS / Platform</div>
          <h1 className="mt-1 text-xl font-semibold">Platform Console</h1>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">只展示已接入真实 Platform API 的能力，不为未实现模块伪造状态。</p>
        </header>

        <section className="storyos-surface min-h-14 px-3 py-2 flex flex-wrap items-center gap-x-6 gap-y-2">
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--text-tertiary)]">Platform API</div>
            <div className={healthy ? 'mt-0.5 flex items-center gap-1.5 text-xs font-mono text-[var(--success)]' : 'mt-0.5 flex items-center gap-1.5 text-xs font-mono text-[var(--warning)]'}>
              <span className="w-1.5 h-1.5 rounded-full bg-current" />
              <span>{status}</span>
            </div>
          </div>
          <div className="text-xs text-[var(--text-secondary)]">Health source: <code className="font-mono text-[var(--text-primary)]">/healthz</code></div>
        </section>

        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <h2 className="text-xs font-semibold">Platform Tools</h2>
            <a href="/" className="text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">返回 Production Console</a>
          </header>
          <div className="divide-y divide-[var(--border-subtle)]">
            {tools.map(({ href, label, desc, Icon }) => (
              <a key={href} href={href} className="min-h-12 px-3 py-2 flex items-center gap-3 hover:bg-[var(--bg-hover)]">
                <Icon className="w-4 h-4 text-[var(--info)] shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium text-[var(--text-primary)]">{label}</div>
                  <div className="text-[11px] text-[var(--text-tertiary)]">{desc}</div>
                </div>
                <span className="font-mono text-[10px] text-[var(--text-disabled)]">{href}</span>
              </a>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
