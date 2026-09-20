import React, { useState } from 'react';
import {
  CheckSquare,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Sliders,
  Sparkles,
  Wand2,
  MessageSquare,
  ShieldCheck,
  User,
  Bot
} from 'lucide-react';
import { FrameReviewResult } from '../types';

interface FrameReviewCardProps {
  reviews: FrameReviewResult[];
  onReviewAction?: (frameId: string, action: 'pass' | 'inpaint' | 'reject') => void;
}

export const FrameReviewCard: React.FC<FrameReviewCardProps> = ({
  reviews,
  onReviewAction,
}) => {
  const [reviewList, setReviewList] = useState<FrameReviewResult[]>(reviews);
  const [fixingId, setFixingId] = useState<string | null>(null);

  const handleAction = (frameId: string, action: 'pass' | 'inpaint' | 'reject') => {
    if (action === 'inpaint') {
      setFixingId(frameId);
      setTimeout(() => {
        setFixingId(null);
        setReviewList(prev => prev.map(r => {
          if (r.frameId === frameId) {
            return {
              ...r,
              verdict: 'PASS',
              anatomyScore: 98.2,
              issueTags: ['Inpaint 修复完毕', '倒影合规'],
              comment: '已通过局部重绘擦除反光多余伪影，重新核验通过。',
            };
          }
          return r;
        }));
      }, 1500);
    } else if (action === 'pass') {
      setReviewList(prev => prev.map(r => r.frameId === frameId ? { ...r, verdict: 'PASS' } : r));
    }

    if (onReviewAction) onReviewAction(frameId, action);
  };

  return (
    <div id="frame-review-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)] gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <CheckSquare className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide flex items-center gap-2">
              <span>逐帧审核与质检报告 (Frame-by-Frame QA & Inspection)</span>
              <span className="storyos-status storyos-status--neutral font-mono">
                示例数据 · 待连接工作区
              </span>
            </h3>
            <p className="text-[11px] text-[var(--text-tertiary)]">
              4:5 (1080×1350) 正式画幅质检：人脸连戏、解剖结构与光影连续性抽样分析（当前尚有 1 项待修复告警，阻断越级通过）
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="storyos-status storyos-status--success font-mono">
            {reviewList.filter(r => r.verdict === 'PASS').length} 通过
          </span>
          <span className="storyos-status storyos-status--warning font-mono">
            {reviewList.filter(r => r.verdict === 'WARN').length} 警示待修
          </span>
        </div>
      </div>

      {/* Frame Reviews Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {reviewList.map((review) => {
          const isPass = review.verdict === 'PASS';
          const isWarn = review.verdict === 'WARN';
          const isFixing = fixingId === review.frameId;

          return (
            <div
              key={review.frameId}
              className={`rounded-[var(--radius-md)] border p-3 flex flex-col justify-between transition-colors ${
                isWarn
                  ? 'bg-[var(--warning-soft)] border-[var(--warning)] ring-1 ring-[var(--warning-soft)]'
                  : 'bg-[var(--bg-subtle)] border-[var(--border-normal)]'
              }`}
            >
              <div>
                {/* Header info */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono font-semibold text-xs text-[var(--text-primary)]">
                      Frame #{review.frameIndex}
                    </span>
                    <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
                      ({review.frameId})
                    </span>
                  </div>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded flex items-center gap-1 ${
                    isPass
                      ? 'bg-[var(--success-soft)] text-[var(--success)] border border-[var(--success)]'
                      : 'bg-[var(--warning-soft)] text-[var(--warning)] border border-[var(--warning)]'
                  }`}>
                    {isPass ? <CheckCircle2 className="w-3 h-3" /> : <AlertTriangle className="w-3 h-3 text-[var(--warning)]" />}
                    <span>{review.verdict}</span>
                  </span>
                </div>

                {/* Preview Aspect (4:5 vertical proportion) */}
                <div className="relative aspect-[4/5] max-h-64 mx-auto w-full rounded-md overflow-hidden bg-black mb-2.5">
                  <img
                    src={review.imageUrl}
                    alt={`Frame ${review.frameIndex}`}
                    className="w-full h-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute bottom-1 right-1.5 text-[9px] font-mono bg-black/75 text-slate-200 px-1 py-0.5 rounded">
                    {review.shotType}
                  </div>
                  <div className="absolute top-1.5 left-1.5 text-[9px] font-mono bg-black/75 text-slate-200 px-1 py-0.5 rounded border border-white/10">
                    4:5 1080×1350
                  </div>
                </div>

                {/* Metric Scores Bar */}
                <div className="grid grid-cols-3 gap-1.5 text-center text-[10px] font-mono mb-2">
                  <div className="p-1 rounded-[var(--radius-xs)] bg-[var(--bg-muted)] border border-[var(--border-subtle)]">
                    <div className="text-[var(--text-tertiary)] text-[9px]">人脸相似</div>
                    <div className="font-semibold text-[var(--text-primary)]">{review.facialScore}%</div>
                  </div>
                  <div className="p-1 rounded-[var(--radius-xs)] bg-[var(--bg-muted)] border border-[var(--border-subtle)]">
                    <div className="text-[var(--text-tertiary)] text-[9px]">光影吻合</div>
                    <div className="font-semibold text-[var(--text-primary)]">{review.lightConsistency}%</div>
                  </div>
                  <div className={`p-1 rounded border ${
                    review.anatomyScore < 92 ? 'bg-[var(--warning-soft)] border-[var(--warning)] text-[var(--warning)] font-semibold' : 'bg-[var(--bg-muted)] border-[var(--border-subtle)] text-[var(--text-primary)]'
                  }`}>
                    <div className="text-[var(--text-tertiary)] text-[9px]">肢体解剖</div>
                    <div>{review.anatomyScore}%</div>
                  </div>
                </div>

                {/* Issue Tags */}
                <div className="flex flex-wrap gap-1 mb-2">
                  {review.issueTags.map((tag, i) => (
                    <span
                      key={i}
                      className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${
                        isWarn
                          ? 'bg-[var(--warning-soft)] text-[var(--warning)] border border-[var(--warning)]'
                          : 'bg-[var(--bg-muted)] text-[var(--text-secondary)]'
                      }`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Reviewer Note */}
                <div className="text-[11px] text-[var(--text-secondary)] bg-[var(--bg-surface)] p-2 rounded-[var(--radius-sm)] border border-[var(--border-subtle)] mb-2 leading-tight">
                  <div className="flex items-center gap-1 font-mono text-[10px] text-[var(--text-tertiary)] mb-0.5 font-semibold">
                    <Bot className="w-3 h-3 text-[var(--primary)]" />
                    <span>{review.reviewer}:</span>
                  </div>
                  <p>{review.comment}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between gap-1.5">
                {isWarn ? (
                  <>
                    <button
                      onClick={() => handleAction(review.frameId, 'inpaint')}
                      disabled={isFixing}
                      className="flex-1 h-8 rounded-[var(--radius-sm)] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white font-semibold text-xs flex items-center justify-center gap-1 transition-colors disabled:opacity-50"
                    >
                      <Wand2 className="w-3 h-3" />
                      <span>{isFixing ? 'Inpaint 修补中...' : '自动局部修补'}</span>
                    </button>
                    <button
                      onClick={() => handleAction(review.frameId, 'pass')}
                      className="h-8 px-2.5 rounded-[var(--radius-sm)] bg-[var(--bg-surface)] hover:bg-[var(--bg-muted)] border border-[var(--border-normal)] text-[var(--text-secondary)] text-xs font-semibold"
                      title="忽略告警强制标记通过"
                    >
                      放行
                    </button>
                  </>
                ) : (
                  <div className="w-full flex items-center justify-between text-[11px] text-[var(--success)] font-mono">
                    <span className="flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>已录入分镜生产资产库</span>
                    </span>
                    <span className="text-[var(--text-subtle)]">PASSED</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
