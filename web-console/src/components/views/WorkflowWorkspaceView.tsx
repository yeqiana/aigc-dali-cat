import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, Check, GitBranch, RefreshCw } from 'lucide-react';
import { platformApi, RuntimeStatusSummary, stageLabel } from '../../api/platformApi';
import { WorkflowDetailPanel } from './WorkflowDetailPanel';

const STAGE_ORDER = ['IDEA_LOCKED','STORYBOARD_LOCKED','VISUAL_CALIBRATED','PRODUCTION_PASSED','PUBLISH_READY','PUBLISHED','DATA_REVIEWED'];
export const WorkflowWorkspaceView: React.FC = () => {
  const [items,setItems] = useState<RuntimeStatusSummary[]>([]);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState<string | null>(null);
  const [reload,setReload] = useState(0);
  const [hasMore,setHasMore] = useState(false);
  const [loadingMore,setLoadingMore] = useState(false);
  const [total,setTotal] = useState<number | null>(null);
  const [filter,setFilter] = useState('ALL');
  const [selected,setSelected] = useState<RuntimeStatusSummary | null>(null);
  const generation = useRef(0);
  const pagingInFlight = useRef(false);
  const nextOffset = useRef(0);
  useEffect(() => {
    let active=true;
    const requestId = ++generation.current;
    pagingInFlight.current = false;
    nextOffset.current = 0;
    setLoading(true);
    platformApi.runtimeStatuses(100,0).then(data => {
      if(!active || requestId !== generation.current)return;
      setItems(data.items ?? []);
      nextOffset.current = (data.items ?? []).length;
      setSelected(null);
      setHasMore(Boolean(data.has_more));
      setTotal(typeof data.total === 'number' ? data.total : null);
      setError(data.errors?.length ? '部分状态数据读取失败，以下仅展示成功返回的阶段投影。' : null);
    }).catch(() => {
      if(!active || requestId !== generation.current)return;
      setItems([]);
      setHasMore(false);
      setTotal(null);
      setError('无法连接 Platform API，暂不能读取生产阶段。');
    }).finally(() => {if(active && requestId === generation.current)setLoading(false)});
    return () => {active=false;generation.current += 1;pagingInFlight.current=false};
  },[reload]);
  const filtered=items.filter(x => filter==='ALL' || x.production_stage===filter);
  const loadNext = async () => {
    if (!hasMore || pagingInFlight.current || loading) return;
    const requestId = generation.current;
    const offset = nextOffset.current;
    pagingInFlight.current = true;
    setLoadingMore(true);
    try {
      const data = await platformApi.runtimeStatuses(100, offset);
      if (requestId !== generation.current) return;
      const page = Array.isArray(data.items) ? data.items : [];
      nextOffset.current = offset + page.length;
      setItems(current => {
        // 服务端数据可能跨页重复；按明确身份去重，不影响后续 offset 计算。
        const ids = new Set(current.map(x => x.episode_id || x.episode_ref).filter(Boolean));
        return [...current, ...page.filter(x => {
          const id = x.episode_id || x.episode_ref;
          if (!id || ids.has(id)) return false;
          ids.add(id);
          return true;
        })];
      });
      setHasMore(Boolean(data.has_more) && page.length > 0);
      if (typeof data.total === 'number') setTotal(data.total);
      if (data.errors?.length) setError('后续分页返回部分错误，列表可能不完整。');
    } catch {
      if (requestId === generation.current) setError('加载更多阶段记录失败，已保留此前成功读取的列表。可重试加载。');
    } finally {
      if (requestId === generation.current) {
        pagingInFlight.current = false;
        setLoadingMore(false);
      }
    }
  };
  return <div className="mx-auto max-w-[1440px] space-y-5 pb-16 text-[var(--text-primary)]">
    <header className="os-card flex flex-wrap items-center justify-between gap-5 px-6 py-6 md:px-8">
      <div><p className="mb-2 os-eyebrow">PRODUCTION WORKFLOW</p><h1 className="os-page-heading">生产流程</h1><p className="mt-2 text-[13px] leading-6 text-[var(--text-secondary)]">从创意锁定到发布复盘，一眼了解阶段顺序与每个作品的当前位置。只读，不绕过门禁。</p></div>
      <button type="button" onClick={()=>setReload(v=>v+1)} disabled={loading} className="os-action disabled:opacity-50"><RefreshCw size={15}/>刷新</button>
    </header>
    <section className="os-card p-5 md:p-6"><div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><p className="os-eyebrow mb-1">STAGE MAP</p><h2 className="os-section-heading">标准生产阶段</h2></div><span className="text-[11px] text-[var(--text-tertiary)]">共 7 个阶段 · 仅展示顺序</span></div><div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-7">
      {STAGE_ORDER.map((stage,i) => <div key={stage} className="relative flex min-h-[80px] flex-col justify-between rounded-[10px] border border-[var(--border-subtle)] bg-[var(--bg-app)] p-3"><span className="text-[11px] font-mono text-[var(--text-tertiary)]">{String(i + 1).padStart(2, '0')}</span><span className="flex items-center gap-2 text-[12px] font-semibold text-[var(--text-primary)]"><span className="flex h-5 w-5 items-center justify-center rounded-full border border-[var(--border-normal)] text-[var(--text-tertiary)]"><Check size={11}/></span>{stageLabel(stage)}</span></div>)}
    </div><p className="mt-4 text-[11px] text-[var(--text-tertiary)]">图示只解释阶段顺序；节点不是可点击的阶段推进操作。</p></section>
    <section className="os-card space-y-4 p-5 md:p-6">
      <div className="flex items-center justify-between gap-3"><div><p className="os-eyebrow mb-1">EPISODE STATUS</p><h2 className="os-section-heading">各作品所处阶段</h2></div><select aria-label="筛选阶段" value={filter} onChange={e=>setFilter(e.target.value)} className="h-9 rounded-[9px] border border-[var(--border-normal)] bg-[var(--bg-elevated)] px-3 text-[12px]"><option value="ALL">所有阶段</option>{STAGE_ORDER.map(x=><option key={x} value={x}>{stageLabel(x)}</option>)}</select></div>
      {error && <p role="alert" className="flex items-center gap-2 border border-[var(--border-normal)] rounded-[5px] p-3 text-[12px] text-[var(--warning)]"><AlertCircle size={16}/>{error}</p>}
      {loading ? <div role="status" className="p-8 text-center text-[var(--text-tertiary)] text-[13px]">正在读取权威阶段…</div>
      : filtered.length===0 ? <div className="rounded-[10px] border border-dashed border-[var(--border-normal)] p-10 text-center text-[13px] text-[var(--text-tertiary)]">暂无可展示的阶段记录。</div>
      : <div className="overflow-hidden rounded-[11px] border border-[var(--border-subtle)] divide-y divide-[var(--border-subtle)]">{filtered.map((x,i)=><div key={x.episode_id||i} className="os-data-row flex flex-wrap items-center gap-4 px-4 py-4 sm:flex-nowrap">
        <GitBranch size={16} className="shrink-0 text-[var(--info)]"/><div className="min-w-0 flex-1"><p className="text-[13px] font-medium truncate">{x.title || x.episode_ref || x.episode_id}</p><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">来源：{x.state_source || '未提供'} · {x.updated_at || x.observed_at || '更新时间未知'}</p></div>
        <span className="shrink-0 rounded-full border border-[var(--border-normal)] bg-[var(--bg-elevated)] px-3 py-1.5 text-[12px] font-medium text-[var(--text-secondary)]">{stageLabel(x.production_stage || 'NO_STATE')}</span><button type="button" onClick={() => setSelected(x)} aria-label={'查看阶段详情：' + (x.title || x.episode_ref || x.episode_id)} className="os-action shrink-0 !h-8">详情</button>
      </div>)}</div>}
    </section>
    {selected && <WorkflowDetailPanel selected={selected} onClose={() => setSelected(null)} />}
    <div className="os-card flex flex-wrap items-center justify-between gap-3 px-5 py-4"><span className="text-[12px] text-[var(--text-tertiary)]">已载入 {items.length}{total !== null ? ' / ' + total : ''} 条权威阶段摘要{hasMore ? ' · 尚有更多' : ''}</span>{hasMore && <button type="button" disabled={loadingMore} onClick={loadNext} className="h-9 px-3 border border-[var(--border-normal)] rounded-[5px] text-[12px] hover:bg-[var(--bg-hover)] disabled:opacity-50">{loadingMore ? '载入中…' : '加载更多'}</button>}</div>
    <p className="text-[11px] leading-5 text-[var(--text-tertiary)]">/runtime/statuses 仅提供阶段 summary；执行动作、Queue、Worker、质量门禁的实时值需按作品查询详细证据，不能根据阶段推断。</p>
  </div>;
};
