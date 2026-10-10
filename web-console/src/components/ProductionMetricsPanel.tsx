import React from 'react';
import { AlertTriangle, CheckCircle2, ShieldCheck } from 'lucide-react';
import { Episode } from '../types';

interface ProductionMetricsPanelProps { activeEpisode: Episode; onShowToast?: (msg: string) => void; }
export const ProductionMetricsPanel: React.FC<ProductionMetricsPanelProps> = ({ activeEpisode }) => {
  const frames = activeEpisode.frameReviews ?? [];
  const passed = frames.filter(frame => frame.verdict === 'PASS').length;
  const warnings = frames.filter(frame => frame.verdict === 'WARN').length;
  const failed = frames.filter(frame => frame.verdict === 'FAIL').length;
  const checks = activeEpisode.preflightChecks ?? [];
  const blocking = checks.filter(item => item.status === 'blocking').length;
  const progress = activeEpisode.totalFrames ? Math.round(activeEpisode.completedFrames / activeEpisode.totalFrames * 100) : 0;
  return <section aria-label="作品制作证据" className="border-y border-[var(--border-subtle)] py-4 text-[var(--text-primary)]">
    <div className="mb-3 flex items-center justify-between gap-3"><h2 className="text-[14px] font-semibold">制作进展</h2><span className="text-[11px] text-[var(--text-tertiary)]">工作区证据快照</span></div>
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div><p className="text-[12px] text-[var(--text-tertiary)]">已完成帧</p><p className="mt-1 text-[22px] font-semibold tabular-nums">{activeEpisode.completedFrames}<span className="text-[12px] font-normal text-[var(--text-tertiary)]"> / {activeEpisode.totalFrames}</span></p><div className="mt-2 h-1 rounded bg-[var(--border-normal)]"><div className="h-full rounded bg-[#58A6FF]" style={{width:`${Math.max(0,Math.min(progress,100))}%`}}/></div></div>
      <div><p className="text-[12px] text-[var(--text-tertiary)]">已审核记录</p><p className="mt-1 text-[22px] font-semibold tabular-nums">{frames.length}</p><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">通过 {passed} · 待查 {warnings}</p></div>
      <div><p className="text-[12px] text-[var(--text-tertiary)]">审核失败</p><p className={`mt-1 text-[22px] font-semibold tabular-nums ${failed?'text-[var(--danger)]':''}`}>{failed}</p><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">按真实记录计数</p></div>
      <div><p className="text-[12px] text-[var(--text-tertiary)]">门禁阻塞</p><p className={`mt-1 text-[22px] font-semibold tabular-nums ${blocking?'text-[var(--danger)]':''}`}>{blocking}</p><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">{checks.length} 项检查已记录</p></div>
    </div>
    <div className="mt-4 flex items-center gap-2 text-[12px] text-[var(--text-secondary)]">{blocking || failed ? <AlertTriangle size={15} className="text-[var(--danger)]"/> : frames.length ? <CheckCircle2 size={15} className="text-[var(--success)]"/> : <ShieldCheck size={15}/>} {blocking || failed ? '存在需要处理的证据，请检查明细。' : frames.length ? '暂无失败审核记录；此信息不替代最终门禁。' : '暂无逐帧审核记录，不能推断质量评分。'}</div>
  </section>;
};
