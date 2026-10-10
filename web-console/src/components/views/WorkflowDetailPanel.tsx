import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { platformApi, RuntimeStatusDetail, RuntimeStatusSummary, stageLabel } from '../../api/platformApi';

interface Props { selected: RuntimeStatusSummary; onClose: () => void; }
export const WorkflowDetailPanel: React.FC<Props> = ({selected, onClose}) => {
  const [detail, setDetail] = useState<RuntimeStatusDetail | null>(null);
  const [status, setStatus] = useState<'loading'|'ready'|'failed'>('loading');
  const episode = selected.episode_ref || selected.episode || selected.business_episode_id || selected.episode_id;
  useEffect(() => {
    let active = true; setDetail(null); setStatus('loading');
    if (!episode) { setStatus('failed'); return; }
    platformApi.runtimeStatus(episode).then(data => {
      if(!active)return;
      setDetail(data);
      setStatus(data?'ready':'failed');
    }).catch(() => {if(active)setStatus('failed')});
    return () => {active=false};
  },[episode]);
  const value = (data: string | number | boolean | null | undefined) => data == null || data === '' ? '未提供' : String(data);
  return <section aria-label="工作流阶段详情" className="border border-[var(--border-normal)] rounded-[6px] p-4 space-y-3 bg-[var(--bg-surface)]">
    <div className="flex gap-3 items-start justify-between">
      <div className="min-w-0"><h3 className="text-[14px] font-semibold truncate">{selected.title || episode}</h3><p className="text-[11px] text-[var(--text-tertiary)] mt-1">权威 Runtime 详情查询（只读）</p></div>
      <button type="button" onClick={onClose} aria-label="关闭工作流详情" className="p-1.5 rounded hover:bg-[var(--bg-hover)]"><X size={16}/></button>
    </div>
    {status === 'loading' ? <p role="status" className="text-[12px] text-[var(--text-secondary)]">正在获取阶段详情…</p> : status === 'failed' ? <p role="alert" className="text-[12px] text-[var(--warning)]">详情接口不可用；只保留摘要，不推测运行状态。</p> :
      <dl className="grid gap-3 sm:grid-cols-2">
        {[
          ['正式阶段',stageLabel(detail?.production_stage || selected.production_stage || 'NO_STATE')],
          ['执行状态',value(detail?.execution_status)],
          ['当前动作',value(detail?.current_action)],
          ['下一步',value(detail?.next_step)],
          ['阻塞原因',value(detail?.blocking_reason)],
          ['需要人工',value(detail?.needs_user)],
          ['可自动恢复',value(detail?.auto_recoverable)],
          ['心跳状态',value(detail?.heartbeat?.health)],
          ['通过帧',value(detail?.image_progress?.accepted_frames)],
          ['目标帧',value(detail?.image_progress?.expected_frames)]
        ].map(([k,v]) => <div key={k}><dt className="text-[11px] text-[var(--text-tertiary)]">{k}</dt><dd className="mt-1 text-[12px] break-words">{v}</dd></div>)}
      </dl>
    }
  </section>;
};
