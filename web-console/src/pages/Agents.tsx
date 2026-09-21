import { FormEvent, useState } from 'react';
import { AlertTriangle, Bot, Search } from 'lucide-react';
import { agentApi } from '../api/agent';
import { PlatformPageHeader } from '../components/PlatformPageHeader';
import type { Agent, ExecutionRecord } from '../types/platform';

export default function Agents() {
  const [agentId, setAgentId] = useState('');
  const [agent, setAgent] = useState<Agent | null>(null);
  const [executions, setExecutions] = useState<ExecutionRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load(event?: FormEvent) {
    event?.preventDefault();
    const id = agentId.trim();
    if (!id || loading) return;
    setLoading(true);
    setError(null);
    try {
      const [nextAgent, nextExecutions] = await Promise.all([
        agentApi.getAgent(id),
        agentApi.listExecutions(id),
      ]);
      setAgent(nextAgent);
      setExecutions(Array.isArray(nextExecutions) ? nextExecutions : []);
    } catch (cause) {
      setAgent(null);
      setExecutions([]);
      setError(cause instanceof Error ? cause.message : 'Agent 查询失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6">
      <div className="max-w-5xl mx-auto space-y-4">
        <PlatformPageHeader
          section="Agents"
          title="Agent Console"
          description="按 Agent ID 查询 Registry 定义与 Execution Records。"
        />

        <form onSubmit={load} className="storyos-surface min-h-12 px-3 py-2 flex flex-col sm:flex-row sm:items-center gap-2">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <input value={agentId} onChange={(event) => setAgentId(event.target.value)} placeholder="agent id" aria-label="Agent ID" className="storyos-control w-full h-8 pl-8 pr-3 font-mono text-xs outline-none focus:border-[var(--focus)]" />
          </div>
          <button type="submit" disabled={!agentId.trim() || loading} className="h-8 px-3 rounded-[var(--radius-md)] bg-[var(--primary)] text-white text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed">{loading ? '查询中…' : '查询 Agent'}</button>
        </form>

        {error && <div className="storyos-surface px-3 py-2 flex items-start gap-2 text-xs text-[var(--danger)] border-[var(--danger)]"><AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /><span>{error}</span></div>}

        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <div className="flex items-center gap-2"><Bot className="w-3.5 h-3.5 text-[var(--info)]" /><h2 className="text-xs font-semibold">Agent Definition</h2></div>
            <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{agent ? 'LIVE API' : 'NO RESULT'}</span>
          </header>
          {agent ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-[var(--border-subtle)] text-xs">
              <div className="p-3"><div className="text-[10px] text-[var(--text-tertiary)]">ID</div><code className="font-mono">{agent.id}</code></div>
              <div className="p-3"><div className="text-[10px] text-[var(--text-tertiary)]">Code</div><div>{agent.agent_code}</div></div>
              <div className="p-3"><div className="text-[10px] text-[var(--text-tertiary)]">Name</div><div>{agent.agent_name}</div></div>
              <div className="p-3"><div className="text-[10px] text-[var(--text-tertiary)]">Type</div><div>{agent.agent_type}</div></div>
            </div>
          ) : <div className="px-3 py-8 text-center text-xs text-[var(--text-tertiary)]">查询 Agent 后显示 Registry 定义。</div>}
        </section>

        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between"><h2 className="text-xs font-semibold">Execution Records</h2><span className="text-[10px] font-mono text-[var(--text-tertiary)]">{executions.length} ROWS</span></header>
          {executions.length > 0 ? (
            <div className="overflow-x-auto"><table className="w-full min-w-[720px] text-xs"><thead className="h-9 border-b border-[var(--border-subtle)] text-[var(--text-tertiary)]"><tr><th className="px-3 text-left">Execution ID</th><th className="px-3 text-left">Type</th><th className="px-3 text-left">Status</th><th className="px-3 text-left">Trace ID</th><th className="px-3 text-left">Updated</th></tr></thead><tbody>{executions.map((row) => <tr key={row.execution_id} className="h-11 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]"><td className="px-3 font-mono"><a className="text-[var(--text-primary)] hover:text-[var(--primary)] hover:underline" href={`/executions?execution=${encodeURIComponent(row.execution_id)}`}>{row.execution_id}</a></td><td className="px-3 font-mono text-[var(--text-secondary)]">{row.execution_type}</td><td className="px-3 font-mono">{row.status}</td><td className="px-3 font-mono text-[var(--text-tertiary)]">{row.trace_id ? <a className="hover:text-[var(--primary)] hover:underline" href={`/traces?trace=${encodeURIComponent(row.trace_id)}`}>{row.trace_id}</a> : '-'}</td><td className="px-3 font-mono text-[var(--text-tertiary)]">{row.updated_time}</td></tr>)}</tbody></table></div>
          ) : <div className="px-3 py-8 text-center text-xs text-[var(--text-tertiary)]">暂无 Execution Record。</div>}
        </section>
      </div>
    </main>
  );
}
