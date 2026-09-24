import React, { useState } from 'react';
import { Check, ChevronDown } from 'lucide-react';
import { ProductionStage } from '../types';

interface StatusFlowBannerProps {
  currentStage: ProductionStage;
  onStageChange?: (stage: ProductionStage) => void;
  completedFrames?: number;
  totalFrames?: number;
  onOpenPipelineView?: () => void;
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
  onOpenPipelineView,
}) => {
  const [showPrePanel, setShowPrePanel] = useState(false);

  const currentIndex = FORMAL_STAGES.findIndex((s) => s.id === currentStage);
  const activeStageInfo = FORMAL_STAGES[currentIndex] || FORMAL_STAGES[3];

  return (
    <div className="mb-4 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[8px] p-2.5 text-xs text-[var(--text-secondary)] shadow-xs select-none">
      {/* 极简单行 7 大正式流水线 */}
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
                  className={`flex items-center gap-1.5 px-2 py-1 rounded-[4px] transition-all cursor-pointer ${
                    isCurrent
                      ? 'bg-[var(--text-primary)] text-[var(--bg-app)] font-bold shadow-xs'
                      : isCompleted
                      ? 'bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)]'
                      : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-3 h-3 text-emerald-400 stroke-[2.5]" />
                  ) : isCurrent ? (
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--bg-app)] shrink-0 animate-pulse" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--border-strong)] shrink-0" />
                  )}
                  <span className="tracking-tight">{s.label}</span>
                  {s.id === 'PROD_APPROVED' && (
                    <span className={`text-[10px] ml-0.5 font-mono ${isCurrent ? 'text-[var(--bg-app)] opacity-80' : 'text-[var(--text-tertiary)]'}`}>
                      ({completedFrames}/{totalFrames})
                    </span>
                  )}
                </button>

                {idx < FORMAL_STAGES.length - 1 && (
                  <span className="text-[var(--border-strong)] text-[11px] px-0.5">/</span>
                )}
              </React.Fragment>
            );
          })}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {onOpenPipelineView && (
            <button
              type="button"
              onClick={onOpenPipelineView}
              className="text-[11px] font-mono text-[#58A6FF] hover:text-[#79B8FF] px-2 py-0.5 rounded-[4px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
              title="查看 7 大阶段门禁规范与时序导图"
            >
              主要流程图 →
            </button>
          )}
          <button
            type="button"
            onClick={() => setShowPrePanel(!showPrePanel)}
            className="text-[11px] font-mono text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-2 py-0.5 rounded-[4px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center gap-1 transition-colors cursor-pointer"
          >
            <span>阶段详情</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${showPrePanel ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* 阶段运行与指标面板 */}
      {showPrePanel && (
        <div className="mt-2 pt-2 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] font-mono flex items-center justify-between gap-2 bg-[var(--bg-elevated)] p-2 rounded-[6px]">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-[var(--text-primary)] font-medium">阶段: {activeStageInfo.label}</span>
            <span className="text-[var(--text-tertiary)]">· 进度: {completedFrames}/{totalFrames} 帧 ({Math.round((completedFrames/totalFrames)*100)}%)</span>
          </div>
          <span className="text-[var(--text-tertiary)] font-mono text-[10px]">{activeStageInfo.desc}</span>
        </div>
      )}
    </div>
  );
};
