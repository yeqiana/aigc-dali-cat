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
    <div id="preflight-check-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-zinc-100 gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-zinc-900 text-amber-400">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide flex items-center gap-2">
              <span>发布前门禁检查 (Preflight Gate & Quality Audit)</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 font-bold border border-amber-300">
                示例数据 · 待连接工作区
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-bold border border-amber-200">
                {passedCount} / {checks.length} 项通过
              </span>
            </h3>
            <p className="text-[11px] text-zinc-600">工业化严苛门禁：杜绝违规穿帮与面部崩溃，禁止非达标剧集流向公域</p>
          </div>
        </div>

        {/* Real Status Gatekeeper Pill */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-rose-50 border border-rose-200 text-xs font-semibold text-rose-800">
            <Lock className="w-3.5 h-3.5 text-rose-600" />
            <span>发布通道锁定 (阶段互斥阻断)</span>
          </div>
        </div>
      </div>

      {/* Honest Warning Notice */}
      <div className="p-3 rounded-lg bg-amber-50/80 border border-amber-300 mb-3 text-xs flex items-start gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div className="text-zinc-800 leading-relaxed">
          <strong className="text-amber-950 font-bold">阶段互斥与门禁守则：</strong>
          当前剧集正处于<strong>「生产推进中」</strong>（已渲染 24/32 帧），依照阶段互斥守则，不可标记为「生产通过」；待全部 32 帧渲染且终审放行后方可达成正式「生产通过」，之后才进入「待发布」。当前均为<strong>示例数据</strong>，后续连接 GitHub 时只读并映射 release-manifest 等门禁文件，前端不直接修改状态。
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
              className={`p-2.5 rounded-lg border text-xs flex items-start gap-2.5 transition-colors ${
                isPassed
                  ? 'bg-zinc-50/70 border-zinc-200'
                  : isWarning
                  ? 'bg-amber-50/40 border-amber-300'
                  : isBlocking
                  ? 'bg-rose-50/30 border-rose-200'
                  : 'bg-zinc-50/30 border-zinc-200/80'
              }`}
            >
              <div className="mt-0.5 shrink-0">
                {isPassed && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                {isWarning && <AlertTriangle className="w-4 h-4 text-amber-600" />}
                {isPending && <Clock className="w-4 h-4 text-zinc-400" />}
                {isBlocking && <Ban className="w-4 h-4 text-rose-600" />}
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1 mb-0.5">
                  <h4 className={`font-bold text-xs truncate ${
                    isPassed ? 'text-zinc-900' : isWarning ? 'text-amber-950' : 'text-zinc-700'
                  }`}>
                    {chk.title}
                  </h4>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded shrink-0 font-bold ${
                    isPassed
                      ? 'bg-emerald-100 text-emerald-800'
                      : isWarning
                      ? 'bg-amber-100 text-amber-900'
                      : isBlocking
                      ? 'bg-rose-100 text-rose-800'
                      : 'bg-zinc-200 text-zinc-700'
                  }`}>
                    {isPassed ? '通过' : isWarning ? '告警' : isBlocking ? '阻断' : '待处理'}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-600 leading-tight">{chk.detail}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Release Button State (Honest Disabled Gate) */}
      <div className="mt-3 pt-3 border-t border-zinc-100 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
        <span className="text-zinc-500 font-mono text-[11px]">
          前置阻断项：Frame #18 质检告警待修、第 28-32 帧待批次渲染、导演组签字待签署
        </span>
        <button
          disabled={!isAllPassed}
          className="px-4 py-1.5 rounded-md bg-zinc-200 text-zinc-400 font-bold text-xs flex items-center gap-1.5 cursor-not-allowed border border-zinc-300"
          title="必须先完成全量帧审核与签字放行"
        >
          <Send className="w-3.5 h-3.5" />
          <span>确认全剧并下发分发网络 (锁定)</span>
        </button>
      </div>
    </div>
  );
};
