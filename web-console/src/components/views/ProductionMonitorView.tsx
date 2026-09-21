import React, { useEffect, useMemo, useState } from 'react';
import { AlertTriangle, RefreshCw, Search, X } from 'lucide-react';
import { runtimeApi } from '../../api/runtime';
import type { RuntimeEpisodeStatus } from '../../types/platform';

interface ProductionMonitorViewProps {
  onShowToast: (msg: string) => void;
}

const PAGE_SIZE = 50;
const AUTO_REFRESH_MS = 15_000;

function displayTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function stageTone(stage?: string | null) {
  if (!stage) return 'text-[var(--text-tertiary)]';
  if (['PUBLISH_READY', 'PUBLISHED', 'DATA_REVIEWED'].includes(stage)) return 'text-[var(--success)]';
  if (stage === 'PRODUCTION_PASSED') return 'text-[var(--info)]';
  if (stage === 'VISUAL_CALIBRATED') return 'text-[var(--primary)]';
  return 'text-[var(--text-secondary)]';
}

function executionTone(status?: string | null) {
  const normalized = String(status || '').toUpperCase();
  if (['BLOCKED', 'ERROR', 'FAILED', 'NEEDS_USER', 'HARD_STOP'].includes(normalized)) return 'text-[var(--danger)]';
  if (['RUNNING', 'READY'].includes(normalized)) return 'text-[var(--info)]';
  if (['COMPLETE', 'COMPLETED'].includes(normalized)) return 'text-[var(--success)]';
  return 'text-[var(--text-secondary)]';
}

export const ProductionMonitorView: React.FC<ProductionMonitorViewProps> = ({ onShowToast }) => {
  const [rows, setRows] = useState<RuntimeEpisodeStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [stageFilter, setStageFilter] = useState('ALL');
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [detail, setDetail] = useState<RuntimeEpisodeStatus>();
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [lastLoadedAt, setLastLoadedAt] = useState<string | null>(null);
  const [total, setTotal] = useState<number | null>(null);
  const [stageCounts, setStageCounts] = useState<Record<string, number>>({});
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);

  async function loadSummaries(pageOffset = offset, { announce = false }: { announce?: boolean } = {}) {
    setLoading(true);
    setError(null);
    try {
      const page = await runtimeApi.listEpisodeStatuses(PAGE_SIZE, pageOffset);
      setRows(page.items);
      setOffset(page.offset);
      setTotal(page.total ?? null);
      setStageCounts(page.stage_counts ?? {});
      setHasMore(page.has_more);
      setLastLoadedAt(new Date().toISOString());
      if (announce) onShowToast(`已刷新 ${page.items.length} 条 MySQL Episode 状态投影`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '生产状态列表读取失败');
    } finally {
      setLoading(false);
    }
  }

  async function inspect(row: RuntimeEpisodeStatus) {
    setSelectedRef(row.episode_ref);
    setDetail(undefined);
    setDetailError(null);
    setDetailLoading(true);
    try {
      setDetail(await runtimeApi.getEpisodeStatus(row.episode_ref));
    } catch (cause) {
      setDetailError(cause instanceof Error ? cause.message : 'Episode Full Snapshot 读取失败');
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    void loadSummaries(offset);
    const timer = window.setInterval(() => void loadSummaries(offset), AUTO_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [offset]);

  const stages = useMemo(() => {
    const fromMetrics = Object.keys(stageCounts).filter((stage) => stage !== 'NO_STATE');
    if (fromMetrics.length) return fromMetrics.sort();
    return Array.from(new Set(rows.map((row) => row.production_stage).filter((value): value is string => Boolean(value)))).sort();
  }, [rows, stageCounts]);

  const filteredRows = useMemo(() => {
    const keyword = searchKeyword.trim().toLowerCase();
    return rows.filter((row) => {
      if (stageFilter !== 'ALL' && (row.production_stage || 'NO_STATE') !== stageFilter) return false;
      if (!keyword) return true;
      return [row.title, row.episode, row.episode_ref, row.business_episode_id, row.episode_id]
        .some((value) => String(value || '').toLowerCase().includes(keyword));
    });
  }, [rows, searchKeyword, stageFilter]);

  const activeTotal = total ?? rows.length;
  const publishReady = stageCounts.PUBLISH_READY ?? rows.filter((row) => row.production_stage === 'PUBLISH_READY').length;
  const productionPassed = stageCounts.PRODUCTION_PASSED ?? rows.filter((row) => row.production_stage === 'PRODUCTION_PASSED').length;
  const visualCalibrated = stageCounts.VISUAL_CALIBRATED ?? rows.filter((row) => row.production_stage === 'VISUAL_CALIBRATED').length;
  const missingState = stageCounts.NO_STATE ?? rows.filter((row) => !row.production_stage).length;

  return (
    <div id="storyos-production-monitor-view" className="space-y-3 pb-12 text-[var(--text-primary)]">
      <header className="flex flex-col gap-3 border-b border-[var(--border-subtle)] pb-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Production / Runtime Projection</div>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <h1 className="text-[18px] font-semibold tracking-tight">StoryOS 生产监控台</h1>
            <span className="storyos-status storyos-status--success font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-[var(--success)]" />
              MYSQL AUTHORITY · READ ONLY
            </span>
          </div>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">
            主表只读取 TB_EPISODE + TB_EPISODE_STATE；运行细节仅在点击 Full Snapshot 后按需加载。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
            {lastLoadedAt ? `PAGE ${Math.floor(offset / PAGE_SIZE) + 1} · UPDATED ${displayTime(lastLoadedAt)} · AUTO 15s` : 'NOT LOADED'}
          </span>
          <button
            type="button"
            onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
            disabled={loading || offset === 0}
            className="storyos-control h-8 px-2.5 text-[11px] font-mono disabled:opacity-50"
          >
            PREV
          </button>
          <button
            type="button"
            onClick={() => setOffset((value) => value + PAGE_SIZE)}
            disabled={loading || !hasMore}
            className="storyos-control h-8 px-2.5 text-[11px] font-mono disabled:opacity-50"
          >
            NEXT
          </button>
          <button
            type="button"
            onClick={() => void loadSummaries(offset, { announce: true })}
            disabled={loading}
            className="storyos-control h-8 px-2.5 inline-flex items-center gap-1.5 text-[11px] font-mono disabled:opacity-50"
          >
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

      <section className="storyos-surface min-h-14 px-4 py-2 flex items-center gap-6 overflow-x-auto text-xs font-mono">
        <div className="shrink-0"><span className="text-[var(--text-tertiary)]">ACTIVE EPISODES</span> <strong className="ml-2 text-lg text-[var(--text-primary)]">{activeTotal}</strong></div>
        <div className="h-4 w-px bg-[var(--border-subtle)] shrink-0" />
        <div className="shrink-0"><span className="text-[var(--text-tertiary)]">PUBLISH READY</span> <strong className="ml-2 text-[var(--success)]">{publishReady}</strong></div>
        <div className="h-4 w-px bg-[var(--border-subtle)] shrink-0" />
        <div className="shrink-0"><span className="text-[var(--text-tertiary)]">PRODUCTION PASSED</span> <strong className="ml-2 text-[var(--info)]">{productionPassed}</strong></div>
        <div className="h-4 w-px bg-[var(--border-subtle)] shrink-0" />
        <div className="shrink-0"><span className="text-[var(--text-tertiary)]">VISUAL CALIBRATED</span> <strong className="ml-2 text-[var(--primary)]">{visualCalibrated}</strong></div>
        <div className="h-4 w-px bg-[var(--border-subtle)] shrink-0" />
        <div className="shrink-0"><span className="text-[var(--text-tertiary)]">MISSING STATE</span> <strong className={`ml-2 ${missingState ? 'text-[var(--warning)]' : 'text-[var(--text-secondary)]'}`}>{missingState}</strong></div>
      </section>

      <section className="storyos-surface overflow-hidden">
        <div className="min-h-11 px-3 py-1.5 border-b border-[var(--border-subtle)] flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 items-center gap-2 min-w-0">
            <div className="relative flex-1 min-w-[180px] max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[var(--text-tertiary)]" />
              <input
                value={searchKeyword}
                onChange={(event) => setSearchKeyword(event.target.value)}
                placeholder="搜索标题 / namespace / business id"
                className="storyos-control h-8 w-full pl-8 pr-3 text-xs font-mono outline-none focus:border-[var(--focus)]"
              />
            </div>
            <select
              value={stageFilter}
              onChange={(event) => setStageFilter(event.target.value)}
              className="storyos-control h-8 min-w-[180px] px-2 text-xs font-mono"
              aria-label="生产阶段筛选"
            >
              <option value="ALL">ALL STAGES</option>
              <option value="NO_STATE">NO STATE</option>
              {stages.map((stage) => <option key={stage} value={stage}>{stage}</option>)}
            </select>
          </div>
          <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
            {filteredRows.length} / {rows.length} PAGE ROWS{hasMore ? ` · MORE AVAILABLE · TOTAL ${activeTotal}` : ''}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] text-left text-xs">
            <thead className="h-9 border-b border-[var(--border-subtle)] bg-[var(--bg-workspace)] text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">
              <tr>
                <th className="px-3 w-10 text-center">#</th>
                <th className="px-3">Episode</th>
                <th className="px-3">Namespace</th>
                <th className="px-3">Stage</th>
                <th className="px-3">State Source</th>
                <th className="px-3">Updated</th>
                <th className="px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.length === 0 ? (
                <tr><td colSpan={7} className="px-3 py-10 text-center font-mono text-[var(--text-tertiary)]">{loading ? '正在读取 MySQL Episode Summary…' : '没有匹配的生产 Episode。'}</td></tr>
              ) : filteredRows.map((row, index) => {
                const selected = selectedRef === row.episode_ref;
                return (
                  <tr
                    key={row.episode_id || row.episode_ref}
                    className={`h-11 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)] ${selected ? 'bg-[var(--bg-selected)]' : ''}`}
                  >
                    <td className="px-3 text-center font-mono text-[var(--text-tertiary)]">{offset + index + 1}</td>
                    <td className="px-3">
                      <div className="font-medium text-[var(--text-primary)]">{row.title || row.episode || row.business_episode_id || 'Untitled'}</div>
                      <div className="mt-0.5 text-[10px] font-mono text-[var(--text-tertiary)]">{row.business_episode_id || row.episode_id || '—'}</div>
                    </td>
                    <td className="px-3 max-w-[280px] truncate font-mono text-[11px] text-[var(--text-secondary)]" title={row.episode_ref}>{row.episode_ref}</td>
                    <td className={`px-3 font-mono text-[11px] font-medium ${stageTone(row.production_stage)}`}>{row.production_stage || 'NO_STATE'}</td>
                    <td className="px-3 font-mono text-[11px] text-[var(--text-secondary)]">{row.state_source || '—'}</td>
                    <td className="px-3 font-mono text-[11px] text-[var(--text-tertiary)] whitespace-nowrap">{displayTime(row.updated_at)}</td>
                    <td className="px-3 text-right">
                      <button
                        type="button"
                        onClick={() => void inspect(row)}
                        disabled={detailLoading && selected}
                        className="storyos-control h-7 px-2 text-[10px] font-mono disabled:opacity-50"
                      >
                        {detailLoading && selected ? 'LOADING…' : 'FULL SNAPSHOT'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {selectedRef && (
        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <div className="min-w-0">
              <span className="text-xs font-medium text-[var(--text-primary)]">Runtime Inspector</span>
              <span className="ml-2 text-[10px] font-mono text-[var(--text-tertiary)]">{selectedRef}</span>
            </div>
            <button type="button" onClick={() => { setSelectedRef(null); setDetail(undefined); setDetailError(null); }} className="h-7 w-7 inline-flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--text-primary)]" aria-label="关闭 Runtime Inspector">
              <X className="h-3.5 w-3.5" />
            </button>
          </header>
          {detailLoading ? (
            <div className="px-3 py-8 text-center text-[11px] font-mono text-[var(--text-tertiary)]">正在读取 Full Runtime Snapshot…</div>
          ) : detailError ? (
            <div className="px-3 py-5 text-xs text-[var(--danger)]">{detailError}</div>
          ) : detail ? (
            <div className="grid grid-cols-2 lg:grid-cols-4 border-b border-[var(--border-subtle)]">
              <div className="px-3 py-3 border-r border-[var(--border-subtle)]"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Execution</div><div className={`mt-1 font-mono text-xs font-medium ${executionTone(detail.execution_status)}`}>{detail.execution_status || '—'}</div></div>
              <div className="px-3 py-3 border-r border-[var(--border-subtle)]"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Current Action</div><div className="mt-1 font-mono text-xs text-[var(--text-primary)]">{detail.current_action || detail.next_step || '—'}</div></div>
              <div className="px-3 py-3 border-r border-[var(--border-subtle)]"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Images</div><div className="mt-1 font-mono text-xs text-[var(--text-primary)]">{detail.image_progress ? `${detail.image_progress.generated_frames ?? 0}/${detail.image_progress.expected_frames ?? '—'}` : '—'}</div></div>
              <div className="px-3 py-3"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Heartbeat</div><div className="mt-1 font-mono text-xs text-[var(--text-primary)]">{detail.heartbeat?.health || '—'}</div></div>
              <div className="px-3 py-3 border-r border-t border-[var(--border-subtle)]"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Needs User</div><div className={`mt-1 font-mono text-xs ${detail.needs_user ? 'text-[var(--danger)]' : 'text-[var(--text-secondary)]'}`}>{detail.needs_user ? 'YES' : 'NO'}</div></div>
              <div className="px-3 py-3 border-r border-t border-[var(--border-subtle)]"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Blocking Reason</div><div className="mt-1 font-mono text-xs text-[var(--text-secondary)]">{detail.blocking_reason || '—'}</div></div>
              <div className="px-3 py-3 border-r border-t border-[var(--border-subtle)]"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Observed</div><div className="mt-1 font-mono text-[11px] text-[var(--text-tertiary)]">{displayTime(detail.observed_at)}</div></div>
              <div className="px-3 py-3 border-t border-[var(--border-subtle)]"><div className="text-[10px] uppercase text-[var(--text-tertiary)]">Warnings</div><div className="mt-1 font-mono text-xs text-[var(--warning)]">{detail.consistency_warnings?.length ? detail.consistency_warnings.join(', ') : '—'}</div></div>
            </div>
          ) : null}
          <div className="px-3 py-2 text-[10px] font-mono text-[var(--text-tertiary)]">
            Full Snapshot 是按需只读投影；本页不提供 Pause / Retry / Stage Transition 写操作。
          </div>
        </section>
      )}
    </div>
  );
};
