import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, ChevronDown, ChevronRight, Clock3, Image as ImageIcon, ShieldAlert } from 'lucide-react';
import { Episode } from '../types';

interface ActivityStreamProps {
  activeEpisode: Episode;
  onGenerateBatch: () => void;
  isGeneratingBatch: boolean;
  onReviewAction: (frameId: string, action: 'pass' | 'inpaint' | 'reject') => void;
  onShowToast: (msg: string) => void;
}

const verdictColor: Record<string,string> = { PASS: 'text-[var(--success)]', WARN: 'text-[var(--warning)]', FAIL: 'text-[var(--danger)]' };
export const ActivityStream: React.FC<ActivityStreamProps> = ({ activeEpisode }) => {
  const [expanded, setExpanded] = useState(false);
  const reviews = activeEpisode.frameReviews ?? [];
  const batch = activeEpisode.currentBatch;
  const warnings = reviews.filter(x => x.verdict !== 'PASS');
  return <section className="space-y-4 pb-6 text-[var(--text-primary)]">
    <header className="flex flex-wrap items-center justify-between gap-3">
      <div><h2 className="text-[14px] font-semibold">制作与审核记录</h2><p className="mt-1 text-[12px] text-[var(--text-tertiary)]">来自当前作品的工作区证据，不代表实时执行日志。</p></div>
      <span className="text-[11px] text-[var(--text-tertiary)]">只读视图 · 写入接口未接入</span>
    </header>
    <div className="border border-[var(--border-subtle)] rounded-[6px] bg-[var(--bg-surface)]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border-subtle)]">
        <div><p className="text-[13px] font-medium">当前批次</p><p className="mt-1 text-[12px] text-[var(--text-tertiary)]">{batch?.batchName || '暂无批次证据'}</p></div>
        <span className="text-[12px] text-[var(--text-secondary)]">{batch ? `${batch.items.length} 帧 · ${batch.status}` : '尚无数据'}</span>
      </div>
      <div className="p-4">
        {!batch?.items.length ? <div className="flex items-center gap-2 py-5 text-[13px] text-[var(--text-tertiary)]"><ImageIcon size={18}/> 暂无可预览的批次帧，生成操作需使用已授权的 Runtime。</div>
        : <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6">{batch.items.map(frame => <div key={frame.id} className="min-w-0">
          <div className="aspect-[4/5] rounded-[4px] border border-[var(--border-subtle)] bg-[var(--bg-app)] overflow-hidden">{frame.imageUrl && <img loading="lazy" alt={`第 ${frame.frameIndex} 帧`} src={frame.imageUrl} className="w-full h-full object-cover"/>}</div>
          <div className="flex items-center justify-between gap-1 mt-2 text-[11px]"><span className="text-[var(--text-secondary)]">Frame {frame.frameIndex}</span><span className="truncate text-[var(--text-tertiary)]">{frame.status}</span></div>
        </div>)}</div>}
      </div>
    </div>
    <div className="border-t border-[var(--border-subtle)] pt-4">
      <div className="flex items-center justify-between"><div><h3 className="text-[14px] font-semibold">逐帧审核</h3><p className="mt-1 text-[12px] text-[var(--text-tertiary)]">已记录 {reviews.length} 项 · 需检查 {warnings.length} 项</p></div>
        <button type="button" onClick={() => setExpanded(!expanded)} aria-expanded={expanded} className="flex items-center gap-1 text-[12px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]">{expanded ? <ChevronDown size={15}/> : <ChevronRight size={15}/>} {expanded ? '收起' : '查看全部'}</button></div>
      {reviews.length === 0 ? <p className="mt-4 border border-dashed border-[var(--border-normal)] rounded-[6px] p-6 text-[13px] text-[var(--text-tertiary)]">暂无审核记录。这里不会把未审核的帧标成通过。</p>
        : <div className="mt-3 divide-y divide-[var(--border-subtle)] border-y border-[var(--border-subtle)]">{(expanded ? reviews : reviews.slice(0,5)).map(review => <div key={review.frameId} className="flex min-w-0 flex-wrap items-start gap-3 py-3 sm:flex-nowrap">
          {review.verdict === 'PASS' ? <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-[var(--success)]"/> : review.verdict === 'FAIL' ? <ShieldAlert size={17} className="mt-0.5 shrink-0 text-[var(--danger)]"/> : <AlertCircle size={17} className="mt-0.5 shrink-0 text-[var(--warning)]"/>}
          <div className="flex-1 min-w-0"><div className="flex items-center gap-2 text-[13px]"><span className="font-medium">Frame {review.frameIndex}</span><span className={`text-[11px] font-mono ${verdictColor[review.verdict]}`}>{review.verdict}</span></div><p className="mt-1 text-[12px] text-[var(--text-secondary)] break-words">{review.comment || review.issueTags?.join('、') || '暂无审核备注'}</p></div>
          <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1 shrink-0"><Clock3 size={12}/>{review.timestamp}</span>
        </div>)}</div>}
    </div>
  </section>;
};
