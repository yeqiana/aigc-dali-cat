import React, { useState } from 'react';
import { Check, ChevronDown, Sparkles } from 'lucide-react';
import { ProductionStage } from '../types';

interface StatusFlowBannerProps {
  currentStage: ProductionStage;
  completedFrames?: number;
  totalFrames?: number;
}

const FORMAL_STAGES: { id: ProductionStage; label: string; desc: string }[] = [
  { id: 'IDEA_LOCKED', label: '创意锁定', desc: '剧本核心冲突与高概念锚定' },
  { id: 'STORYBOARD_LOCKED', label: '分镜锁定', desc: '景别轴线与情绪节拍冻结' },
  { id: 'VISUAL_CALIBRATED', label: '视觉校准', desc: '主角面容与光影基准锁定' },
  { id: 'PRODUCTION_PASSED', label: '生产通过', desc: '逐帧批次出图与严格质检' },
  { id: 'PUBLISH_READY', label: '待发布', desc: '4:5 1080×1350 规格终审放行' },
  { id: 'PUBLISHED', label: '已发布', desc: '全渠道矩阵打包上线' },
  { id: 'DATA_REVIEWED', label: '数据复盘', desc: '完播率与留存归因分析' },
];

export const StatusFlowBanner: React.FC<StatusFlowBannerProps> = ({
  currentStage,
  completedFrames = 24,
  totalFrames = 32,
}) => {
  const [showPrePanel, setShowPrePanel] = useState(false);

  const currentIndex = FORMAL_STAGES.findIndex((s) => s.id === currentStage);
  const activeStageInfo = FORMAL_STAGES[currentIndex] || FORMAL_STAGES[3];

  return (
    <div className="mb-3 storyos-surface p-2 text-xs text-[var(--text-secondary)] select-none">
      {/* 单行正式流水线：状态清晰，但不靠大面积状态色抢占 Stage。 */}
      <div className="flex items-center justify-between gap-3 overflow-x-auto pb-1 scrollbar-none">
        <div className="flex items-center gap-1 shrink-0 text-[11px] font-mono">
          {FORMAL_STAGES.map((s, idx) => {
            const isCompleted = idx < currentIndex;
            const isCurrent = s.id === currentStage;

            return (
              <React.Fragment key={s.id}>
                <button
                  type="button"
                  disabled
                  title={`${s.label}: ${s.desc} · 阶段只读`}
                  className={`flex items-center gap-1.5 px-2 py-1 rounded-[var(--radius-sm)] ${
                    isCurrent
                      ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] border border-[var(--border-normal)] font-semibold'
                      : isCompleted
                      ? 'bg-[var(--bg-subtle)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'
                      : 'text-[var(--text-tertiary)]'
                  }`}
                >
                  {isCompleted ? (
                    <Check className="w-3 h-3 text-[var(--success)] stroke-[2.5]" />
                  ) : isCurrent ? (
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] shrink-0" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-subtle)] shrink-0" />
                  )}
                  <span className="tracking-tight">{s.label}</span>
                  {s.id === 'PRODUCTION_PASSED' && (
                    <span className={`text-[10px] ml-0.5 font-mono ${isCurrent ? 'text-[var(--primary)]' : 'text-[var(--text-tertiary)]'}`}>
                      ({completedFrames}/{totalFrames})
                    </span>
                  )}
                </button>

                {idx < FORMAL_STAGES.length - 1 && (
                  <span className="text-[var(--text-subtle)] text-[11px] px-0.5">/</span>
                )}
              </React.Fragment>
            );
          })}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setShowPrePanel(!showPrePanel)}
            className="text-[11px] font-mono text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-2 py-0.5 rounded-[var(--radius-sm)] bg-[var(--bg-surface)] border border-[var(--border-normal)] flex items-center gap-1 transition-colors"
          >
            <span>流水线详情</span>
            <ChevronDown className={`w-3 h-3 transition-transform ${showPrePanel ? 'rotate-180' : ''}`} />
          </button>
        </div>
      </div>

      {/* 阶段运行与指标面板 */}
      {showPrePanel && (
        <div className="mt-2 pt-2 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-[var(--bg-workspace)] p-2 rounded-[var(--radius-sm)]">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-[var(--text-primary)] font-medium flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-[var(--primary)]" />
              当前阶段: {activeStageInfo.label}
            </span>
            <span className="text-[var(--text-tertiary)]">• 目标: {activeStageInfo.desc}</span>
            <span className="text-[var(--text-secondary)]">• 生产进度: {completedFrames}/{totalFrames} 帧 ({Math.round((completedFrames/totalFrames)*100)}%)</span>
          </div>
          <span className="text-[var(--text-tertiary)] shrink-0">阶段只读映射，推进由 StoryOS canonical state transition 执行</span>
        </div>
      )}
    </div>
  );
};
