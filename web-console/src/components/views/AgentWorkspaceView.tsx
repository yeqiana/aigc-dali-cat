import React, { useEffect, useState } from 'react';
import { AlertCircle, Bot, Database, Link2, RefreshCw, ShieldCheck } from 'lucide-react';
import { platformApi } from '../../api/platformApi';
import { MemorySearchPanel } from './MemorySearchPanel';

type AgentSummary = { id: string; name: string; description: string; status: string; tools: string[] };
const asText = (value: unknown): string => typeof value === 'string' ? value : '';
const asAgent = (value: unknown): AgentSummary | null => {
  if (!value || typeof value !== 'object') return null;
  const x = value as Record<string,unknown>;
  const id = asText(x.agent_id) || asText(x.id);
  const name = asText(x.name) || id;
  if (!name) return null;
  return { id: id || name, name, description: asText(x.description),
    status: asText(x.status), tools: Array.isArray(x.tools) ? x.tools.filter((v):v is string => typeof v === 'string') : [] };
};

export const AgentWorkspaceView: React.FC = () => {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [state, setState] = useState<'loading'|'available'|'error'>('loading');
  const [message, setMessage] = useState('');
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let alive = true;
    setState('loading');
    platformApi.agents().then(response => {
      if (!alive) return;
      setAgents((response.items ?? []).map(asAgent).filter((a):a is AgentSummary => a !== null));
      setMessage('');
      setState('available');
    }).catch(() => {
      if (!alive) return;
      setAgents([]);
      setMessage('当前 Platform API 尚未开放 Agent Registry 列表，无法展示实时 Agent 或启停状态。');
      setState('error');
    });
    return () => {alive=false;};
  }, [reload]);

  return <div className="mx-auto max-w-[1450px] space-y-5 pb-12 text-[var(--text-primary)]">
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4">
      <div><p className="mb-1 text-[11px] font-medium text-[var(--text-tertiary)]">智能体平台</p><h1 className="text-[22px] font-semibold tracking-tight">Agents</h1><p className="mt-2 text-[13px] text-[var(--text-secondary)]">查看智能体能力及接入状态，执行权限由 Runtime 控制。</p></div>
      <button type="button" onClick={() => setReload(v => v+1)} disabled={state==='loading'} className="flex h-9 items-center gap-2 rounded-[6px] border border-[var(--border-normal)] px-3 text-[12px] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] disabled:opacity-50"><RefreshCw size={15}/>刷新</button>
    </header>
    <section className="grid gap-3 border-b border-[var(--border-subtle)] pb-4 md:grid-cols-3">
      <div className="flex items-start gap-3 border-l-2 border-[var(--border-normal)] py-2 pl-3"><Bot size={18} className="shrink-0 text-[var(--text-tertiary)]"/><div><h2 className="text-[13px] font-semibold">Agent Registry</h2><p className="mt-1 text-[12px] leading-5 text-[var(--text-secondary)]">查询已注册 Agent，需由 Platform API 提供权威清单。</p></div></div>
      <div className="flex items-start gap-3 p-3"><Link2 size={18} className="shrink-0 text-[var(--text-tertiary)]"/><div><h2 className="text-[13px] font-semibold">Skills / MCP</h2><p className="mt-1 text-[12px] leading-5 text-[var(--text-secondary)]">能力注册表入口；当前无公开读接口，不显示假连接状态。</p></div></div>
      <div className="flex items-start gap-3 p-3"><Database size={18} className="shrink-0 text-[var(--text-tertiary)]"/><div><h2 className="text-[13px] font-semibold">Memory</h2><p className="mt-1 text-[12px] leading-5 text-[var(--text-secondary)]">经验检索服务需携带明确查询，不推测记忆条目数量。</p></div></div>
    </section>
    <div className="flex flex-wrap items-center justify-between gap-2"><h2 className="text-[15px] font-semibold">已注册 Agent</h2><span className="text-[12px] text-[var(--text-tertiary)]">{state==='available' ? `${agents.length} 个已返回` : '接口状态待确认'}</span></div>
    {state==='loading' && <div role="status" className="border-y border-[var(--border-subtle)] py-12 text-center text-[13px] text-[var(--text-secondary)]">正在读取 Platform API…</div>}
    {state==='error' && <div role="alert" className="flex items-start gap-3 rounded-[6px] border border-[var(--border-normal)] border-l-[3px] border-l-[var(--warning)] bg-[var(--bg-surface)] p-5"><AlertCircle size={19} className="shrink-0 text-[var(--warning)]"/><div><p className="font-semibold text-[13px]">Agent 能力尚未接通</p><p className="mt-2 text-[12px] text-[var(--text-secondary)]">{message}</p><p className="mt-2 text-[11px] text-[var(--text-tertiary)]">这是接口能力状态，不代表 Agent 运行失败。</p></div></div>}
    {state==='available' && agents.length===0 && <div className="border-y border-[var(--border-subtle)] py-10 text-center text-[13px] text-[var(--text-tertiary)]">接口已返回，但没有可展示的 Agent。</div>}
    {state==='available' && agents.length>0 && <div className="divide-y divide-[var(--border-subtle)] overflow-hidden rounded-[6px] border border-[var(--border-subtle)]">{agents.map(agent => <div key={agent.id} className="flex flex-wrap items-start justify-between gap-3 px-4 py-3 hover:bg-[var(--bg-hover)]">
      <div className="min-w-0"><h3 className="text-[13px] font-semibold truncate">{agent.name}</h3><p className="mt-1 text-[12px] text-[var(--text-secondary)]">{agent.description || '暂无描述'}</p><p className="mt-2 text-[11px] text-[var(--text-tertiary)]">{agent.tools.length ? `已披露工具：${agent.tools.join('、')}` : '未披露工具清单'}</p></div>
      <span className="shrink-0 text-[11px] font-medium text-[var(--text-tertiary)]">{agent.status || '状态未提供'}</span>
    </div>)}</div>}
    <MemorySearchPanel />
    <footer className="flex items-start gap-2 border-t border-[var(--border-subtle)] pt-3 text-[11px] text-[var(--text-tertiary)]"><ShieldCheck size={15} className="shrink-0"/> 此页为只读能力视图。创建、启动、停止 Agent 需要独立授权的后端契约，不会在前端模拟执行。</footer>
  </div>;
};
