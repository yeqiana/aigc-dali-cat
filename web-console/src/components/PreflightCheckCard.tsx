import React from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Ban,
  ArrowRight,
  Sparkles,
  Lock,
  Send
} from 'lucide-react';
import { PreflightCheckItem } from '../types';

interface PreflightCheckCardProps {
  checks: PreflightCheckItem[];
  onTriggerCheck?: () => void;
}

export const PreflightCheckCard: React.FC<PreflightCheckCardProps> = ({ checks }) => {
  const passedCount = checks.filter(c => c.status === 'passed').length;
  const isAllPassed = passedCount === checks.length;

  return (
    <div id="preflight-check-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)] gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide flex items-center gap-2">
              <span>发布前门禁检查 (Preflight Gate & Quality Audit)</span>
              <span className="storyos-status storyos-status--neutral font-mono">
                示例数据 · 待连接工作区
              </span>
              <span className="storyos-status storyos-status--info font-mono">
                {passedCount} / {checks.length} 项通过
              </span>
            </h3>
            <p className="text-[11px] text-[var(--text-tertiary)]">工业化严苛门禁：杜绝违规穿帮与面部崩溃，禁止非达标剧集流向公域</p>
          </div>
        </div>

        {/* Real Status Gatekeeper Pill */}
        <div className="flex items-center gap-2">
          <div className="storyos-status storyos-status--danger">
            <Lock className="w-3.5 h-3.5 text-[var(--danger)]" />
            <span>发布通道锁定 (阶段互斥阻断)</span>
          </div>
        </div>
      </div>

      {/* Honest Warning Notice */}
      <div className="p-3 rounded-[var(--radius-md)] bg-[var(--warning-soft)] border border-[var(--warning)] mb-3 text-xs flex items-start gap-2.5">
        <AlertTriangle className="w-4 h-4 text-[var(--warning)] shrink-0 mt-0.5" />
        <div className="text-[var(--text-secondary)] leading-relaxed">
          <strong className="text-[var(--warning)] font-semibold">阶段互斥与门禁守则：</strong>
          当前剧集正处于<strong>「生产推进中」</strong>（已渲染 24/32 帧），依照阶段互斥守则，不可标记为「生产通过」；待全部 32 帧渲染且终审放行后方可达成正式「生产通过」，之后才进入「待发布」。当前均为<strong>示例数据</strong>；后续接入真实 Episode 投影后只读映射 release-manifest 等门禁证据，前端不直接修改状态。
        </div>
      </div>

      {/* 8-Check Items List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        {checks.map((chk) => {
          const isPassed = chk.status === 'passed';
          const isWarning = chk.status === 'warning';
          const isPending = chk.status === 'pending';
          const isBlocking = chk.status === 'blocking';

          return (
            <div
              key={chk.id}
              className={`p-2.5 rounded-[var(--radius-md)] border text-xs flex items-start gap-2.5 transition-colors ${
                isPassed
                  ? 'bg-[var(--bg-subtle)] border-[var(--border-normal)]'
                  : isWarning
                  ? 'bg-[var(--warning-soft)] border-[var(--warning)]'
                  : isBlocking
                  ? 'bg-[var(--danger-soft)] border-[var(--danger)]'
                  : 'bg-[var(--bg-subtle)] border-[var(--border-subtle)]'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isPassed && <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />}
                {isWarning && <AlertTriangle className="w-4 h-4 text-[var(--warning)]" />}
                {isPending && <Clock className="w-4 h-4 text-[var(--text-subtle)]" />}
                {isBlocking && <Ban className="w-4 h-4 text-[var(--danger)]" />}
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1 mb-0.5">
                  <h4 className={`font-bold text-xs truncate ${
                    isPassed ? 'text-[var(--text-primary)]' : isWarning ? 'text-[var(--warning)]' : 'text-[var(--text-secondary)]'
                  }`}>
                    {chk.title}
                  </h4>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded shrink-0 font-bold ${
                    isPassed
                      ? 'bg-[var(--success-soft)] text-[var(--success)]'
                      : isWarning
                      ? 'bg-[var(--warning-soft)] text-[var(--warning)]'
                      : isBlocking
                      ? 'bg-[var(--danger-soft)] text-[var(--danger)]'
                      : 'bg-[var(--bg-muted)] text-[var(--text-secondary)]'
                  }`}>
                    {isPassed ? '通过' : isWarning ? '告警' : isBlocking ? '阻断' : '待处理'}
                  </span>
                </div>
                <p className="text-[11px] text-[var(--text-tertiary)] leading-tight">{chk.detail}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Release Button State (Honest Disabled Gate) */}
      <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
        <span className="text-[var(--text-tertiary)] font-mono text-[11px]">
          前置阻断项：Frame #18 质检告警待修、第 28-32 帧待批次渲染、导演组签字待签署
        </span>
        <button
          disabled={!isAllPassed}
          className="h-9 px-4 rounded-[var(--radius-md)] bg-[var(--bg-muted)] text-[var(--text-disabled)] font-semibold text-xs flex items-center gap-1.5 cursor-not-allowed border border-[var(--border-normal)]"
          title="必须先完成全量帧审核与签字放行"
        >
          <Send className="w-3.5 h-3.5" />
          <span>确认全剧并下发分发网络 (锁定)</span>
        </button>
      </div>
    </div>
  );
};
