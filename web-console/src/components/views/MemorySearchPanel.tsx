import React, { useState } from 'react';
import { Database, Search } from 'lucide-react';
import { platformApi } from '../../api/platformApi';

export const MemorySearchPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [rows, setRows] = useState<Array<Record<string, unknown>>>([]);
  const [total, setTotal] = useState<number | null>(null);
  const search = async (event: React.FormEvent) => {
    event.preventDefault();
    const q = query.trim();
    if (q.length < 2 || status === 'loading') return;
    setStatus('loading');
    setRows([]); setTotal(null);
    try {
      const response = await platformApi.memory(q);
      setRows(Array.isArray(response.items) ? response.items : []);
      setTotal(typeof response.total === 'number' ? response.total : null);
      setStatus('success');
    } catch {
      setStatus('error');
    }
  };
  return <section aria-label="Memory 经验检索" className="space-y-3 border-t border-[var(--border-subtle)] pt-5">
    <div className="flex items-center gap-2"><Database size={17} className="text-[var(--text-tertiary)]"/><h2 className="text-[14px] font-semibold">Memory 经验检索</h2></div>
    <p className="text-[12px] text-[var(--text-secondary)]">主动向现有 /api/v1/memory/search 提交检索词；这里只读，不创建、修改或删除记忆。</p>
    <form onSubmit={search} className="flex items-center gap-2">
      <label className="relative flex-1 min-w-0"><Search size={15} className="absolute left-3 top-2.5 text-[var(--text-tertiary)]" aria-hidden="true"/>
        <input aria-label="输入经验检索词" value={query} onChange={e => setQuery(e.target.value)} maxLength={160} placeholder="输入至少 2 个字符的检索词" className="h-9 w-full pl-9 pr-3 border border-[var(--border-normal)] bg-[var(--bg-surface)] rounded-[5px] text-[12px] outline-[#58A6FF]"/>
      </label>
      <button type="submit" disabled={query.trim().length < 2 || status === 'loading'} className="h-9 rounded-[6px] bg-[var(--text-primary)] px-4 text-[12px] font-medium text-[var(--bg-app)] disabled:opacity-40">{status === 'loading' ? '查询中…' : '搜索'}</button>
    </form>
    {status === 'error' && <p role="alert" className="text-[12px] text-[var(--warning)]">Memory API 无法检索。没有返回结果不代表记忆为空。</p>}
    {status === 'success' && <div aria-live="polite" className="space-y-2">
      <p className="text-[12px] text-[var(--text-secondary)]">本次查询返回 {rows.length} 条{total !== null ? '，接口报告总数 ' + total : ''}；以下直接展示接口记录。</p>
      {rows.length === 0 ? <p className="py-4 text-[12px] text-[var(--text-tertiary)]">本次检索没有可展示的结果。</p> : rows.slice(0, 8).map((row,i) => <pre key={i} className="whitespace-pre-wrap break-all text-[11px] leading-5 p-3 border-b border-[var(--border-subtle)] text-[var(--text-secondary)]">{JSON.stringify(row,null,2).slice(0,1600)}</pre>)}
      {rows.length > 8 && <p className="text-[11px] text-[var(--text-tertiary)]">仅展示前 8 条结果。</p>}
    </div>}
  </section>;
};
