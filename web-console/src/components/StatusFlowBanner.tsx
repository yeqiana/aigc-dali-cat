import React, { useState } from 'react';
import { Check, ChevronDown, Sparkles } from 'lucide-react';
import { ProductionStage } from '../types';

interface StatusFlowBannerProps {
  currentStage: ProductionStage;
  onStageChange?: (stage: ProductionStage) => void;
  completedFrames?: number;
  totalFrames?: number;
}

const FORMAL_STAGES: { id: ProductionStage; label: string; desc: string }[] = [
  { id: 'IDEA_LOCK', label: '创意锁定', desc: '剧本核心冲突与高概念锚定' },
  { id: 'STORYBOARD_LOCK', label: '分镜锁定', desc: '景别轴线与情绪节拍冻结' },
  { id: 'VISUAL_CALIBRATE', label: '视觉校准', desc: '主角面容与光影基准锁定' },
  { id: 'PROD_APPROVED', label: '生产通过', desc: '逐帧批次出图与严格质检' },
  { id: 'READY_TO_PUBLISH', label: '待发布', desc: '4:5 1080×1350 规格终审放行' },
  { id: 'PUBLISHED', label: '已发布', desc: '全渠道矩阵打包上线' },
  { id: 'POST_MORTEM', label: '数据复盘', desc: '完播率与留存归因分析' },
];

export const StatusFlowBanner: React.FC<StatusFlowBannerProps> = ({
  currentStage,
  onStageChange,
  completedFrames = 24,
  totalFrames = 32,
}) => {
  const [showPrePanel, setShowPrePanel] = useState(false);

  const currentIndex = FORMAL_STAGES.findIndex((s) => s.id === currentStage);
  const activeStageInfo = FORMAL_STAGES[currentIndex] || FORMAL_STAGES[3];

  return (
    <div className="mb-4 bg-[#0a0a0c] border border-[#222226] rounded-xl p-2.5 text-xs text-zinc-300 shadow-sm select-none">
      {/* 极简单行 7 大正式流水线 - 黑底白字高对比 */}
      <div className="flex items-center justify-between gap-3 overflow-x-auto pb-1 scrollbar-none">
        <div className="flex items-center gap-1 shrink-0 text-[11px] font-mono">
          {FORMAL_STAGES.map((s, idx) => {
            const isCompleted = idx < currentIndex;
            const isCurrent = s.id === currentStage;

            return (
              <React.Fragment key={s.id}>
                <button
                  type="button"
                  onClick={() => onStageChange && onStageChange(s.id)}
                  title={`${s.label}: ${s.desc} (点击切换阶段)`}
                  className={`flex items-center gap-1.5 px-2 py-1 rounded-md transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-white text-black font-semibold shadow-xs'
                      : isCompleted
                      ? 'bg-[#141416] text-zinc-300 hover:text-white hover:bg-[#1a1a1e] border border-[#27272a]'
                      : 'text-zinc-500 hover:text-zinc-200 hover:bg-[#141416]'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-3 h-3 text-zinc-300 stroke-[2.5]" />
                  ) : isCurrent ? (
                    <span className="w-1.5 h-1.5 rounded-full bg-black shrink-0 animate-pulse" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-700 shrink-0" />
                  )}
                  <span className="tracking-tight">{s.label}</span>
                  {s.id === 'PROD_APPROVED' && (
                    <span className={`text-[10px] ml-0.5 font-mono ${isCurrent ? 'text-zinc-700' : 'text-zinc-500'}`}>
                      ({completedFrames}/{totalFrames})
                    </span>
                  )}
                </button>

                {idx < FORMAL_STAGES.length - 1 && (
                  <span className="text-zinc-700 text-[11px] px-0.5">/</span>
                )}
              </React.Fragment>
            );
          })}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setShowPrePanel(!showPrePanel)}
            className="text-[11px] font-mono text-zinc-400 hover:text-white px-2 py-0.5 rounded bg-[#141416] border border-[#27272a] flex items-center gap-1 transition-colors"
          >
            <span>流水线详情</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${showPrePanel ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* 阶段运行与指标面板（纯黑底白字折叠） */}
      {showPrePanel && (
        <div className="mt-2 pt-2 border-t border-[#1f1f23] text-[11px] text-zinc-300 font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-[#0e0e11] p-2 rounded-lg">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-white font-medium flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-white" />
              当前阶段: {activeStageInfo.label}
            </span>
            <span className="text-zinc-400">• 目标: {activeStageInfo.desc}</span>
            <span className="text-zinc-300">• 生产进度: {completedFrames}/{totalFrames} 帧 ({Math.round((completedFrames/totalFrames)*100)}%)</span>
          </div>
          <span className="text-zinc-400 shrink-0">点击上方各阶段药丸可直接推进或回溯</span>
        </div>
      )}
    </div>
  );
};
