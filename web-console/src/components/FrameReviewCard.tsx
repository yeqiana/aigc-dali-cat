import React from 'react';
import {AlertTriangle, CheckCircle2, ShieldCheck} from 'lucide-react';
import type {FrameReviewResult} from '../types';
interface FrameReviewCardProps { reviews:FrameReviewResult[]; onReviewAction?:(frameId:string,action:'pass'|'inpaint'|'reject')=>void; }
export const FrameReviewCard:React.FC<FrameReviewCardProps>=({reviews})=>{
  const passed=reviews.filter(r=>r.verdict==='PASS').length;
  const flagged=reviews.filter(r=>r.verdict!=='PASS').length;
  return <section id="frame-review-card" className="space-y-3 border-y border-[var(--border-subtle)] py-4 text-[var(--text-primary)]">
    <header className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="flex items-center gap-2 text-[14px] font-semibold"><ShieldCheck size={16}/> 逐帧审核记录</h3><p className="mt-1 text-[12px] text-[var(--text-tertiary)]">只读检视现有审核证据；不在浏览器内模拟修补或强制放行。</p></div><div className="flex gap-3 text-[12px] tabular-nums"><span>{passed} 通过</span><span className={flagged?'text-[var(--warning)]':'text-[var(--text-tertiary)]'}>{flagged} 需复查</span></div></header>
    <div className="divide-y divide-[var(--border-subtle)] border-y border-[var(--border-subtle)]">{!reviews.length?<p className="py-8 text-center text-[12px] text-[var(--text-tertiary)]">暂无审核记录，不能认为已通过。</p>:reviews.map(r=><div key={r.frameId} className="flex min-w-0 flex-wrap items-start gap-3 py-3 sm:flex-nowrap">
      <div className="h-24 w-[77px] shrink-0 overflow-hidden rounded-[4px] bg-[var(--bg-elevated)]">{r.imageUrl&&<img src={r.imageUrl} alt={'Frame '+r.frameIndex} loading="lazy" className="h-full w-full object-cover" referrerPolicy="no-referrer"/>}</div>
      <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="font-mono text-[12px] font-semibold">Frame {r.frameIndex}</span><span className="text-[11px] text-[var(--text-tertiary)]">{r.shotType}</span>{r.verdict==='PASS'?<CheckCircle2 size={15} className="text-[var(--success)]"/>:<AlertTriangle size={15} className="text-[var(--warning)]"/>}<span className="text-[12px] font-medium">{r.verdict}</span></div><p className="mt-2 text-[12px] leading-5 text-[var(--text-secondary)]">{r.comment||'暂无审核说明'}</p><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">{r.issueTags.join('、')||'无问题标签'} · 审核来源：{r.reviewer}</p></div>
      <dl className="grid shrink-0 grid-cols-3 gap-3 text-right text-[11px] tabular-nums text-[var(--text-secondary)]"><div><dt>人脸</dt><dd className="mt-1 text-[13px] font-medium text-[var(--text-primary)]">{r.facialScore}%</dd></div><div><dt>光影</dt><dd className="mt-1 text-[13px] font-medium text-[var(--text-primary)]">{r.lightConsistency}%</dd></div><div><dt>结构</dt><dd className="mt-1 text-[13px] font-medium text-[var(--text-primary)]">{r.anatomyScore}%</dd></div></dl>
    </div>)}</div>
    <p className="text-[11px] text-[var(--text-tertiary)]">修补、标记通过、驳回等操作必须经过正式 Runtime / Review Authority 记录。</p>
  </section>;
};
