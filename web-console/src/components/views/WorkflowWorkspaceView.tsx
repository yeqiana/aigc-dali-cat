import React, { useEffect, useState } from 'react';
import { AlertCircle, ArrowRight, GitBranch, RefreshCw } from 'lucide-react';
import { platformApi, RuntimeStatusSummary, stageLabel } from '../../api/platformApi';

const STAGE_ORDER = ['IDEA_LOCKED','STORYBOARD_LOCKED','VISUAL_CALIBRATED','PRODUCTION_PASSED','PUBLISH_READY','PUBLISHED','DATA_REVIEWED'];
export const WorkflowWorkspaceView: React.FC = () => {
  const [items,setItems] = useState<RuntimeStatusSummary[]>([]);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState<string | null>(null);
  const [reload,setReload] = useState(0);
  const [filter,setFilter] = useState('ALL');
  useEffect(() => {
    let active=true;
    setLoading(true);
    platformApi.runtimeStatuses(100,0).then(data => {
      if(!active)return;
      setItems(data.items ?? []);
      setError(data.errors?.length ? '部分状态数据读取失败，以下仅展示成功返回的阶段投影。' : null);
    }).catch(() => {
      if(!active)return;
      setItems([]);
      setError('无法连接 Platform API，暂不能读取生产阶段。');
    }).finally(() => {if(active)setLoading(false)});
    return () => {active=false};
  },[reload]);
  const filtered=items.filter(x => filter==='ALL' || x.production_stage===filter);
  return <div className="mx-auto max-w-[1200px] space-y-7 pb-16 text-[var(--text-primary)]">
    <header className="flex items-start justify-between gap-3 border-b border-[var(--border-subtle)] pb-5">
      <div><p className="mb-2 text-[12px] text-[var(--text-tertiary)]">StoryOS / Workflow</p><h1 className="text-[20px] font-semibold">生产流程</h1><p className="mt-2 text-[13px] text-[var(--text-secondary)]">查看 canonical 生产阶段，不在前端点击跳过门禁。</p></div>
      <button type="button" onClick={()=>setReload(v=>v+1)} disabled={loading} className="flex items-center gap-2 h-9 px-3 border border-[var(--border-normal)] rounded-[5px] text-[12px] disabled:opacity-50"><RefreshCw size={15}/>刷新</button>
    </header>
    <section><h2 className="mb-4 text-[14px] font-semibold">标准生产阶段</h2><div className="flex flex-wrap items-center gap-2">
      {STAGE_ORDER.map((stage,i) => <React.Fragment key={stage}>{i>0 && <ArrowRight size={14} className="text-[var(--text-tertiary)]"/>}<span className="border border-[var(--border-normal)] px-3 py-2 rounded-[5px] text-[12px] bg-[var(--bg-surface)]">{stageLabel(stage)}</span></React.Fragment>)}
    </div><p className="mt-3 text-[11px] text-[var(--text-tertiary)]">此处仅解释执行顺序；节点不是可点击的阶段推进操作。</p></section>
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3"><h2 className="text-[14px] font-semibold">各作品所处阶段</h2><select aria-label="筛选阶段" value={filter} onChange={e=>setFilter(e.target.value)} className="h-9 border border-[var(--border-normal)] rounded-[5px] px-3 bg-[var(--bg-surface)] text-[12px]"><option value="ALL">所有阶段</option>{STAGE_ORDER.map(x=><option key={x} value={x}>{stageLabel(x)}</option>)}</select></div>
      {error && <p role="alert" className="flex items-center gap-2 border border-[var(--border-normal)] rounded-[5px] p-3 text-[12px] text-[var(--warning)]"><AlertCircle size={16}/>{error}</p>}
      {loading ? <div role="status" className="p-8 text-center text-[var(--text-tertiary)] text-[13px]">正在读取权威阶段…</div>
      : filtered.length===0 ? <div className="p-8 border-y border-[var(--border-subtle)] text-center text-[13px] text-[var(--text-tertiary)]">暂无可展示的阶段记录。</div>
      : <div className="divide-y divide-[var(--border-subtle)] border-y border-[var(--border-subtle)]">{filtered.map((x,i)=><div key={x.episode_id||i} className="flex items-start gap-4 py-3">
        <GitBranch size={16} className="mt-0.5 shrink-0 text-[var(--text-tertiary)]"/><div className="min-w-0 flex-1"><p className="text-[13px] font-medium truncate">{x.title || x.episode_ref || x.episode_id}</p><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">来源：{x.state_source || '未提供'} · {x.updated_at || x.observed_at || '更新时间未知'}</p></div>
        <span className="shrink-0 text-[12px] text-[var(--text-secondary)]">{stageLabel(x.production_stage || 'NO_STATE')}</span>
      </div>)}</div>}
    </section>
    <p className="text-[11px] leading-5 text-[var(--text-tertiary)]">/runtime/statuses 仅提供阶段 summary；执行动作、Queue、Worker、质量门禁的实时值需按作品查询详细证据，不能根据阶段推断。</p>
  </div>;
};
