import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, Clapperboard, RefreshCw, Search } from 'lucide-react';
import { runtimeApi } from '../../api/runtime';
import type { RuntimeEpisodeStatus } from '../../types/platform';

const PAGE_SIZE = 100;

function displayTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

export const SeriesLibraryView: React.FC = () => {
  const [rows, setRows] = useState<RuntimeEpisodeStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStage, setFilterStage] = useState('ALL');
  const [total, setTotal] = useState<number | null>(null);
  const [stageCounts, setStageCounts] = useState<Record<string, number>>({});
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);

  async function load(pageOffset = offset) {
    setLoading(true);
    setError(null);
    try {
      const page = await runtimeApi.listEpisodeStatuses(PAGE_SIZE, pageOffset);
      setRows(page.items);
      setOffset(page.offset);
      setTotal(page.total ?? null);
      setStageCounts(page.stage_counts ?? {});
      setHasMore(page.has_more);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Episode Index 读取失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(offset);
  }, [offset]);

  const stages = useMemo(() => {
    const fromMetrics = Object.keys(stageCounts).filter((stage) => stage !== 'NO_STATE');
    if (fromMetrics.length) return fromMetrics.sort();
    return Array.from(new Set(rows.map((row) => row.production_stage).filter((stage): stage is string => Boolean(stage)))).sort();
  }, [rows, stageCounts]);

  const filteredRows = useMemo(() => {
    const keyword = searchQuery.trim().toLowerCase();
    return rows.filter((row) => {
      if (filterStage !== 'ALL' && (row.production_stage || 'NO_STATE') !== filterStage) return false;
      if (!keyword) return true;
      return [row.title, row.episode, row.episode_ref, row.business_episode_id]
        .some((value) => String(value || '').toLowerCase().includes(keyword));
    });
  }, [rows, searchQuery, filterStage]);

  return (
    <div id="series-library-view" className="space-y-3 text-[var(--text-secondary)]">
      <header className="flex flex-col gap-3 border-b border-[var(--border-subtle)] pb-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Production / Episode Index</div>
          <div className="mt-1 flex items-center gap-2">
            <Clapperboard className="h-4 w-4 text-[var(--primary)]" />
            <h2 className="text-[18px] font-semibold text-[var(--text-primary)]">剧集资产全景总览</h2>
            <span className="storyos-status storyos-status--success font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--success)]" />
              MYSQL AUTHORITY
            </span>
          </div>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">只读展示 TB_EPISODE + TB_EPISODE_STATE，不用本地 Demo Episode 补字段。</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))} disabled={loading || offset === 0} className="storyos-control h-8 px-2.5 text-[11px] font-mono disabled:opacity-50">PREV</button>
          <button type="button" onClick={() => setOffset((value) => value + PAGE_SIZE)} disabled={loading || !hasMore} className="storyos-control h-8 px-2.5 text-[11px] font-mono disabled:opacity-50">NEXT</button>
          <button type="button" onClick={() => void load(offset)} disabled={loading} className="storyos-control h-8 px-2.5 inline-flex items-center gap-1.5 text-[11px] font-mono disabled:opacity-50">
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            REFRESH
          </button>
        </div>
      </header>

      {error && (
        <div className="storyos-surface flex items-center gap-2 px-3 py-2 text-xs text-[var(--danger)]">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <section className="storyos-surface overflow-hidden">
        <div className="min-h-11 px-3 py-1.5 border-b border-[var(--border-subtle)] flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 items-center gap-2 min-w-0">
            <div className="relative flex-1 min-w-[180px] max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[var(--text-tertiary)]" />
              <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="搜索标题 / namespace / business id" className="storyos-control h-8 w-full pl-8 pr-3 text-xs font-mono outline-none focus:border-[var(--focus)]" />
            </div>
            <select value={filterStage} onChange={(event) => setFilterStage(event.target.value)} className="storyos-control h-8 min-w-[180px] px-2 text-xs font-mono" aria-label="Episode 阶段筛选">
              <option value="ALL">ALL STAGES</option>
              <option value="NO_STATE">NO STATE</option>
              {stages.map((stage) => <option key={stage} value={stage}>{stage}</option>)}
            </select>
          </div>
          <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
            PAGE {Math.floor(offset / PAGE_SIZE) + 1} · {rows.length ? `${offset + 1}-${offset + rows.length}` : '0'} · FILTERED {filteredRows.length}{hasMore ? ' · MORE AVAILABLE' : ''} · TOTAL {total ?? rows.length}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[880px] text-left text-xs">
            <thead className="h-9 border-b border-[var(--border-subtle)] bg-[var(--bg-workspace)] text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">
              <tr>
                <th className="px-3">Episode</th>
                <th className="px-3">Business ID</th>
                <th className="px-3">Namespace</th>
                <th className="px-3">Current State</th>
                <th className="px-3">Source</th>
                <th className="px-3">Updated</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.length === 0 ? (
                <tr><td colSpan={6} className="px-3 py-10 text-center font-mono text-[var(--text-tertiary)]">{loading ? '正在读取 Episode Index…' : '没有匹配的生产 Episode。'}</td></tr>
              ) : filteredRows.map((row) => (
                <tr key={row.episode_id || row.episode_ref} className="h-11 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
                  <td className="px-3 font-medium text-[var(--text-primary)]">{row.title || row.episode || 'Untitled'}</td>
                  <td className="px-3 font-mono text-[11px] text-[var(--text-secondary)]">{row.business_episode_id || '—'}</td>
                  <td className="px-3 max-w-[300px] truncate font-mono text-[11px] text-[var(--text-secondary)]" title={row.episode_ref}>{row.episode_ref}</td>
                  <td className="px-3 font-mono text-[11px] text-[var(--text-primary)]">{row.production_stage || 'NO_STATE'}</td>
                  <td className="px-3 font-mono text-[11px] text-[var(--text-tertiary)]">{row.state_source || '—'}</td>
                  <td className="px-3 whitespace-nowrap font-mono text-[11px] text-[var(--text-tertiary)]">{displayTime(row.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="text-[10px] font-mono text-[var(--text-tertiary)]">
        新建 Episode / 状态推进属于写操作能力；当前 Web Console 未接入该 capability，因此本页保持只读。
      </div>
    </div>
  );
};
