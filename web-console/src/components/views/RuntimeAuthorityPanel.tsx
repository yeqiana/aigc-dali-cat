import React, { useEffect, useState } from 'react';
import { ChevronRight, X } from 'lucide-react';
import { platformApi, RuntimeStatusDetail, RuntimeStatusSummary, stageLabel } from '../../api/platformApi';

interface Props { items: RuntimeStatusSummary[]; dataState: 'loading' | 'ok' | 'partial' | 'offline'; lastSync: string | null; }
export const RuntimeAuthorityPanel: React.FC<Props> = ({ items, dataState, lastSync }) => {
  const [selected, setSelected] = useState<RuntimeStatusSummary | null>(null);
  const [detail, setDetail] = useState<RuntimeStatusDetail | null>(null);
  const [detailState, setDetailState] = useState<'loading' | 'available' | 'unavailable'>('loading');
  const ref = selected?.episode_ref || selected?.episode || selected?.business_episode_id || selected?.episode_id;
  useEffect(() => {
    if (!ref) { setDetail(null); return; }
    let active = true;
    setDetailState('loading');
    setDetail(null);
    platformApi.runtimeStatus(ref).then(response => {
      if (!active) return;
      setDetail(response);
      setDetailState(response ? 'available' : 'unavailable');
    }).catch(() => { if (active) setDetailState('unavailable'); });
    return () => { active = false; };
  }, [ref]);
  const text = (value?: string | number | boolean | null) => value === null || value === undefined || value === '' ? '未提供' : String(value);
  return <section aria-label="平台权威阶段摘要" className="rounded-[6px] border border-[var(--border-normal)] bg-[var(--bg-surface)] text-[12px] text-[var(--text-primary)]">
    <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-[var(--border-subtle)]">
      <div><h2 className="text-[14px] font-semibold">平台阶段证据</h2><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">来自 Runtime API，区别于下方历史工作区运行快照。只读。</p></div>
      <span className="shrink-0 text-[11px] text-[var(--text-tertiary)]">{lastSync ? '读取于 ' + lastSync : '未获取成功'}</span>
    </div>
    {dataState === 'loading' ? <p role="status" className="px-4 py-5 text-[var(--text-secondary)]">正在读取平台阶段…</p>
    : dataState === 'offline' ? <p role="alert" className="px-4 py-5 text-[var(--warning)]">无法连接 Platform API；本区不展示历史数据冒充在线状态。</p>
    : <>
      {dataState === 'partial' && <p role="alert" className="px-4 pt-3 text-[var(--warning)]">接口报告部分失败，阶段列表可能不完整。</p>}
      {items.length === 0 && <p className="px-4 py-5 text-[var(--text-tertiary)]">接口已响应，但没有可显示的阶段摘要。</p>}
      <div className="divide-y divide-[var(--border-subtle)]">{items.slice(0, 8).map((item, i) =>
        <button type="button" aria-label={'查看权威阶段：' + (item.title || item.episode_ref || item.episode_id)} key={(item.episode_id || item.episode_ref || String(i)) + ':' + i}
          onClick={() => setSelected(item)} className="flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left hover:bg-[var(--bg-hover)] focus-visible:outline-2 focus-visible:outline-[#58A6FF]">
          <span className="min-w-0 truncate font-medium" title={item.title || item.episode_ref || item.episode_id}>{item.title || item.episode_ref || item.episode_id || '未知作品'}</span>
          <span className="ml-auto shrink-0 text-[var(--text-secondary)]">{stageLabel(item.production_stage || 'NO_STATE')}</span><ChevronRight size={14} className="shrink-0 text-[var(--text-tertiary)]"/>
        </button>)}</div>
      {items.length > 8 && <p className="px-4 py-2 text-[11px] text-[var(--text-tertiary)]">仅预览前 8 条；完整列表请到工作流查看分页。</p>}
    </>}
    {selected && <div className="border-t border-[var(--border-strong)] bg-[var(--bg-elevated)] px-4 py-4 space-y-3">
      <div className="flex items-start justify-between gap-3"><div className="min-w-0"><h3 className="text-[13px] font-semibold truncate">{selected.title || selected.episode_ref || selected.episode_id}</h3><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">阶段详情（权威 Runtime 只读查询）</p></div><button onClick={() => setSelected(null)} aria-label="关闭阶段详情" type="button" className="p-1.5 rounded hover:bg-[var(--bg-hover)]"><X size={16}/></button></div>
      {detailState === 'loading' ? <p role="status" className="text-[var(--text-secondary)]">读取阶段详情中…</p> : detailState === 'unavailable' ? <p role="alert" className="text-[var(--warning)]">详情接口不可用；不推断执行状态。</p> : <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-3">
        {[
          ['生产阶段', stageLabel(detail?.production_stage || selected.production_stage || 'NO_STATE')],
          ['执行状态', text(detail?.execution_status)],
          ['当前动作', text(detail?.current_action || detail?.next_step)],
          ['阻塞原因', text(detail?.blocking_reason)],
          ['需要人工', text(detail?.needs_user)],
          ['心跳健康', text(detail?.heartbeat?.health)],
          ['已接受帧', text(detail?.image_progress?.accepted_frames)],
          ['总目标帧', text(detail?.image_progress?.expected_frames)]
        ].map(([key, value]) => <div key={key}><dt className="text-[11px] text-[var(--text-tertiary)]">{key}</dt><dd className="mt-1 break-words text-[12px]">{value}</dd></div>)}
      </dl>}
    </div>}
  </section>;
};
