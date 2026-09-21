import { FormEvent, useState } from 'react';
import { AlertTriangle, Brain, Search } from 'lucide-react';
import { memoryApi } from '../api/memory';
import { PlatformPageHeader } from '../components/PlatformPageHeader';
import type { MemoryItem } from '../types/platform';

export default function Memory() {
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<MemoryItem[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function search(event?: FormEvent) {
    event?.preventDefault();
    const keyword = query.trim();
    if (!keyword || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await memoryApi.search(keyword);
      setItems(Array.isArray(result) ? result : []);
      setSearched(true);
    } catch (cause) {
      setItems([]);
      setSearched(true);
      setError(cause instanceof Error ? cause.message : 'Memory 检索失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6">
      <div className="max-w-5xl mx-auto space-y-4">
        <PlatformPageHeader
          section="Memory"
          title="Memory Console"
          description="检索 Experience / Memory Store，结果直接来自 Platform API。"
        />
        <form onSubmit={search} className="storyos-surface min-h-12 px-3 py-2 flex flex-col sm:flex-row sm:items-center gap-2">
          <div className="relative flex-1 min-w-0">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="memory search query" aria-label="Memory search query" className="storyos-control w-full h-8 pl-8 pr-3 text-xs outline-none focus:border-[var(--focus)]" />
          </div>
          <button type="submit" disabled={!query.trim() || loading} className="h-8 px-3 rounded-[var(--radius-md)] bg-[var(--primary)] text-white text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed">{loading ? '检索中…' : '检索 Memory'}</button>
        </form>
        {error && <div className="storyos-surface px-3 py-2 flex items-start gap-2 text-xs text-[var(--danger)] border-[var(--danger)]"><AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /><span>{error}</span></div>}
        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <div className="flex items-center gap-2"><Brain className="w-3.5 h-3.5 text-[var(--info)]" /><h2 className="text-xs font-semibold">Memory Results</h2></div>
            <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{searched ? String(items.length) + ' RESULTS' : 'NOT QUERIED'}</span>
          </header>
          {items.length > 0 ? (
            <div className="divide-y divide-[var(--border-subtle)]">
              {items.map((item) => (
                <article key={item.id} className="px-3 py-2.5 hover:bg-[var(--bg-hover)]">
                  <div className="flex items-center justify-between gap-3 text-[11px]"><code className="font-mono text-[var(--text-secondary)] truncate">{item.id}</code><span className="font-mono text-[var(--text-tertiary)] shrink-0">{item.memory_type || 'memory'}</span></div>
                  <p className="mt-1 text-xs leading-5 text-[var(--text-primary)] whitespace-pre-wrap">{item.content}</p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] font-mono text-[var(--text-tertiary)]">
                    <span>outcome: {item.outcome || '-'}</span>
                    <span>confidence: {typeof item.confidence === 'number' ? item.confidence.toFixed(2) : '-'}</span>
                    <span className="truncate">evidence: {item.evidence_ref || '-'}</span>
                  </div>
                </article>
              ))}
            </div>
          ) : <div className="px-3 py-10 text-center text-xs text-[var(--text-tertiary)]">{searched ? '没有匹配的 Memory。' : '输入关键词后检索。'}</div>}
        </section>
      </div>
    </main>
  );
}
