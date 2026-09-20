import React from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Image as ImageIcon,
  Layers3,
  LoaderCircle,
} from 'lucide-react';
import type { BatchItem, Episode } from '../types';

interface ProductionStagePanelProps {
  activeEpisode: Episode;
  isGeneratingBatch?: boolean;
  onSelectFrame?: (frame: BatchItem) => void;
}

const statusMeta: Record<BatchItem['status'], { label: string; tone: string; dot: string }> = {
  rendering: {
    label: 'RUNNING',
    tone: 'text-[var(--info)]',
    dot: 'bg-[var(--info)]',
  },
  ready: {
    label: 'READY',
    tone: 'text-[var(--text-secondary)]',
    dot: 'bg-[var(--text-tertiary)]',
  },
  qa_passed: {
    label: 'PASSED',
    tone: 'text-[var(--success)]',
    dot: 'bg-[var(--success)]',
  },
  qa_warning: {
    label: 'WARNING',
    tone: 'text-[var(--warning)]',
    dot: 'bg-[var(--warning)]',
  },
  needs_reroll: {
    label: 'RETRY',
    tone: 'text-[var(--retry)]',
    dot: 'bg-[var(--retry)]',
  },
};

export const ProductionStagePanel: React.FC<ProductionStagePanelProps> = ({
  activeEpisode,
  isGeneratingBatch = false,
  onSelectFrame,
}) => {
  const completion = Math.round(
    (activeEpisode.completedFrames / Math.max(activeEpisode.totalFrames, 1)) * 100,
  );
  const batch = activeEpisode.currentBatch;
  const passed = batch.items.filter((item) => item.status === 'qa_passed').length;
  const attention = batch.items.filter(
    (item) => item.status === 'qa_warning' || item.status === 'needs_reroll',
  ).length;

  return (
    <section
      aria-label="Production Stage"
      className="storyos-surface min-w-0 overflow-hidden self-start xl:sticky xl:top-0"
    >
      <header className="h-11 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between gap-3">
        <div className="min-w-0 flex items-center gap-2">
          <Layers3 className="w-3.5 h-3.5 text-[var(--info)] shrink-0" />
          <div className="min-w-0">
            <div className="text-[13px] font-semibold text-[var(--text-primary)] truncate">
              Production Stage
            </div>
            <div className="text-[11px] font-mono text-[var(--text-tertiary)] truncate">
              {activeEpisode.code} · {batch.batchName}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono shrink-0">
          <span className="text-[var(--text-tertiary)]">{completion}%</span>
          <span className="inline-flex items-center gap-1.5 text-[var(--text-secondary)]">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isGeneratingBatch ? 'bg-[var(--info)] animate-pulse' : 'bg-[var(--success)]'
              }`}
            />
            {isGeneratingBatch ? 'GENERATING' : batch.status.toUpperCase()}
          </span>
        </div>
      </header>

      <div className="px-3 py-2 border-b border-[var(--border-subtle)] flex flex-wrap items-center gap-x-5 gap-y-1 text-[11px] font-mono">
        <span className="text-[var(--text-tertiary)]">
          STAGE <strong className="text-[var(--text-secondary)] font-medium">{activeEpisode.currentStage}</strong>
        </span>
        <span className="text-[var(--text-tertiary)]">
          FRAMES <strong className="text-[var(--text-primary)] font-medium">{activeEpisode.completedFrames}/{activeEpisode.totalFrames}</strong>
        </span>
        <span className="text-[var(--text-tertiary)]">
          PASS <strong className="text-[var(--success)] font-medium">{passed}</strong>
        </span>
        <span className="text-[var(--text-tertiary)]">
          ATTENTION <strong className={attention > 0 ? 'text-[var(--warning)] font-medium' : 'text-[var(--text-secondary)] font-medium'}>{attention}</strong>
        </span>
      </div>

      <div className="p-3">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-[12px] font-medium text-[var(--text-secondary)]">
            <ImageIcon className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            当前批次 Artifact
          </div>
          <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
            4:5 · {activeEpisode.runtimeRequest.imageModel}
          </span>
        </div>

        {batch.items.length === 0 ? (
          <div className="h-48 border border-dashed border-[var(--border-normal)] rounded-[var(--radius-md)] flex flex-col items-center justify-center gap-2 text-center">
            <ImageIcon className="w-5 h-5 text-[var(--text-disabled)]" />
            <div className="text-[12px] text-[var(--text-secondary)]">当前批次暂无 Artifact</div>
            <div className="text-[11px] text-[var(--text-tertiary)]">从左侧 Operator Console 调度生产任务。</div>
          </div>
        ) : (
          <div className="grid grid-cols-2 2xl:grid-cols-5 gap-2">
            {batch.items.map((item) => {
              const meta = statusMeta[item.status];
              return (
                <button
                  type="button"
                  key={item.id}
                  onClick={() => onSelectFrame?.(item)}
                  className="group text-left min-w-0 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--bg-workspace)] overflow-hidden hover:border-[var(--border-strong)] transition-colors"
                  aria-label={`查看 Frame #${item.frameIndex}，状态 ${meta.label}`}
                >
                  <div className="relative aspect-[4/5] bg-[var(--bg-app)] overflow-hidden">
                    <img
                      src={item.imageUrl}
                      alt={`Frame #${item.frameIndex}`}
                      className="w-full h-full object-cover"
                      referrerPolicy="no-referrer"
                    />
                    <span className="absolute left-1.5 top-1.5 px-1.5 py-0.5 rounded-[var(--radius-xs)] bg-[rgba(11,13,16,.82)] border border-white/10 text-[10px] font-mono text-white">
                      #{item.frameIndex}
                    </span>
                  </div>
                  <div className="px-2 py-1.5 border-t border-[var(--border-subtle)]">
                    <div className={`flex items-center gap-1.5 text-[10px] font-mono font-medium ${meta.tone}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${meta.dot}`} />
                      {meta.label}
                    </div>
                    <div className="mt-1 flex items-center justify-between gap-2 text-[10px] font-mono text-[var(--text-tertiary)]">
                      <span>{item.renderTime}</span>
                      <span>{Math.round(item.consistencyScore * 100)}%</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <footer className="min-h-10 px-3 py-2 border-t border-[var(--border-subtle)] flex items-center justify-between gap-3 text-[11px]">
        <div className="flex items-center gap-1.5 text-[var(--text-tertiary)]">
          {isGeneratingBatch ? (
            <LoaderCircle className="w-3.5 h-3.5 text-[var(--info)] animate-spin" />
          ) : attention > 0 ? (
            <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" />
          ) : (
            <CheckCircle2 className="w-3.5 h-3.5 text-[var(--success)]" />
          )}
          <span>
            {isGeneratingBatch
              ? '批次正在执行，结果完成后逐帧进入 Review。'
              : attention > 0
                ? `${attention} 帧需要 Review / Retry。`
                : '当前批次无阻断项。'}
          </span>
        </div>
        <span className="font-mono text-[var(--text-disabled)] shrink-0">{batch.batchId}</span>
      </footer>
    </section>
  );
};
