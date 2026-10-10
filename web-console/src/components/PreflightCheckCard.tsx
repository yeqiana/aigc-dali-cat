import React from 'react';
import {AlertTriangle, Ban, CheckCircle2, Clock, ShieldCheck} from 'lucide-react';
import type {PreflightCheckItem} from '../types';
interface PreflightCheckCardProps { checks: PreflightCheckItem[]; onTriggerCheck?: () => void; }
const labels: Record<string,string>={passed:'通过',warning:'警告',blocking:'阻塞',pending:'待检查'};
export const PreflightCheckCard:React.FC<PreflightCheckCardProps>=({checks})=>{
  const passed=checks.filter(c=>c.status==='passed').length;
  const blocked=checks.filter(c=>c.status==='blocking').length;
  const warn=checks.filter(c=>c.status==='warning').length;
  return <section id="preflight-check-card" className="space-y-3 border-y border-[var(--border-subtle)] py-4 text-[var(--text-primary)]">
    <header className="flex flex-wrap items-center justify-between gap-3"><div><h3 className="flex items-center gap-2 text-[14px] font-semibold"><ShieldCheck size={16}/> 发布前检查</h3><p className="mt-1 text-[12px] text-[var(--text-tertiary)]">工作区中已记录的预检状态，不代表最终发布授权。</p></div><span className="text-[12px] tabular-nums text-[var(--text-secondary)]">{passed}/{checks.length} 项记录为通过</span></header>
    {(blocked>0||warn>0)&&<p role="status" className="flex items-center gap-2 border-l-2 border-[var(--warning)] pl-3 text-[12px] text-[var(--text-secondary)]"><AlertTriangle size={15} className="text-[var(--warning)]"/>已记录阻塞 {blocked} 项、警告 {warn} 项，需以正式审核证据确认。</p>}
    <div className="divide-y divide-[var(--border-subtle)] border-y border-[var(--border-subtle)]">{!checks.length?<p className="py-8 text-center text-[12px] text-[var(--text-tertiary)]">暂无预检记录，不能据此推断已通过发布门禁。</p>:checks.map(chk=><div key={chk.id} className="flex min-w-0 items-start gap-3 py-3">{chk.status==='passed'?<CheckCircle2 size={17} className="shrink-0 text-[var(--success)]"/>:chk.status==='blocking'?<Ban size={17} className="shrink-0 text-[var(--danger)]"/>:chk.status==='warning'?<AlertTriangle size={17} className="shrink-0 text-[var(--warning)]"/>:<Clock size={17} className="shrink-0 text-[var(--text-tertiary)]"/>}<div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><strong className="text-[13px] font-medium">{chk.title}</strong><span className="text-[11px] text-[var(--text-secondary)]">{labels[chk.status]||chk.status}</span></div><p className="mt-1 text-[12px] leading-5 text-[var(--text-secondary)]">{chk.detail}</p></div></div>)}</div>
    <p className="text-[11px] text-[var(--text-tertiary)]">此视图不提供发布、越级放行或门禁写入操作。</p>
  </section>;
};
