import React, { useState } from 'react';
import {
  Layers,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sliders,
  RotateCcw,
  Sparkles,
  Maximize2,
  X,
  Camera,
  Terminal,
  Cpu
} from 'lucide-react';
import { BatchQueue, BatchItem } from '../types';

interface BatchQueueCardProps {
  batchQueue: BatchQueue;
  onRerollItem?: (itemId: string) => void;
  onRerunBatch?: () => void;
}

export const BatchQueueCard: React.FC<BatchQueueCardProps> = ({
  batchQueue,
  onRerollItem,
  onRerunBatch,
}) => {
  const [activeItemModal, setActiveItemModal] = useState<BatchItem | null>(null);
  const [rerollingId, setRerollingId] = useState<string | null>(null);

  const handleReroll = (id: string) => {
    setRerollingId(id);
    setTimeout(() => {
      setRerollingId(null);
      if (onRerollItem) onRerollItem(id);
    }, 1200);
  };

  return (
    <div id="batch-queue-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)] gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide flex items-center gap-1.5">
                <span>5 帧逻辑批次出图队列 (5-Frame Logical Batch Pipeline)</span>
                <span className="storyos-status storyos-status--info font-mono">
                  BATCH #{batchQueue.batchNumber < 10 ? `0${batchQueue.batchNumber}` : batchQueue.batchNumber}
                </span>
              </h3>
              {/* Clear Source Badge */}
              <span className="storyos-status storyos-status--neutral font-mono">
                示例数据 · 待连接工作区
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
              {batchQueue.batchName} • 调度引擎：StoryOS Engine ｜ 图像模型：gpt-image-2 (high) ｜ 画幅：4:5 (1080×1350) ｜ 最大同时出图：3 张
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-[var(--text-tertiary)] hidden md:inline">
            生产规则: 5 帧逻辑批次 / 并发 3
          </span>
          <button
            onClick={onRerunBatch}
            className="h-9 flex items-center gap-1.5 px-3 rounded-[var(--radius-md)] bg-[var(--bg-surface)] hover:bg-[var(--bg-muted)] text-xs font-semibold text-[var(--text-secondary)] border border-[var(--border-normal)] transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <span>重新调度当前批次</span>
          </button>
        </div>
      </div>

      {/* 5 Frames Grid in 4:5 vertical proportion */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {batchQueue.items.map((item) => {
          const isRendering = item.status === 'rendering' || rerollingId === item.id;
          const isWarning = item.status === 'qa_warning';
          const isPassed = item.status === 'qa_passed';

          return (
            <div
              key={item.id}
              className={`rounded-[var(--radius-md)] border bg-[var(--bg-surface)] overflow-hidden flex flex-col justify-between transition-all ${
                isWarning
                  ? 'border-[var(--warning)] bg-[var(--warning-soft)] ring-1 ring-[var(--warning-soft)]'
                  : isRendering
                  ? 'border-[var(--primary)] bg-[var(--primary-soft)]'
                  : 'border-[var(--border-normal)] hover:border-[var(--border-strong)] shadow-[var(--shadow-xs)]'
              }`}
            >
              {/* Frame Image Aspect Preview (4:5 vertical aspect) */}
              <div className="relative aspect-[4/5] bg-slate-950 overflow-hidden group">
                <img
                  src={item.imageUrl}
                  alt={`Frame ${item.frameIndex}`}
                  className={`w-full h-full object-cover transition-opacity ${isRendering ? 'opacity-40 blur-xs' : 'opacity-100'}`}
                  referrerPolicy="no-referrer"
                />

                {/* Rendering overlay */}
                {isRendering && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70 text-white p-2 text-center">
                    <RefreshCw className="w-5 h-5 animate-spin mb-1" />
                    <span className="text-[10px] font-mono font-bold">StoryOS 批次渲染中 {item.progress}%</span>
                    <span className="text-[9px] text-slate-300 mt-0.5">gpt-image-2 (high)</span>
                  </div>
                )}

                {/* Top Badge */}
                <div className="absolute top-1.5 left-1.5 right-1.5 flex items-center justify-between pointer-events-none">
                  <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-black/75 text-white border border-white/20 backdrop-blur-xs">
                    #{item.frameIndex}
                  </span>
                  <span className={`text-[9px] font-mono px-1 py-0.2 rounded font-bold ${
                    isPassed
                      ? 'bg-emerald-600 text-white'
                      : isWarning
                      ? 'bg-amber-500 text-slate-950'
                      : 'bg-slate-800 text-slate-100'
                  }`}>
                    {isPassed ? 'QA PASS' : isWarning ? 'QA WARN' : 'RENDERING'}
                  </span>
                </div>

                {/* Format pill in image */}
                <div className="absolute bottom-1.5 left-1.5 pointer-events-none">
                  <span className="text-[9px] font-mono bg-black/70 text-slate-200 px-1 py-0.5 rounded border border-white/10">
                    4:5 1080×1350
                  </span>
                </div>

                {/* Inspect Button on hover */}
                {!isRendering && (
                  <button
                    onClick={() => setActiveItemModal(item)}
                    className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white"
                    aria-label={`查看 Frame ${item.frameIndex} 详情`}
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Meta & Stats */}
              <div className="p-2.5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-tertiary)] mb-1">
                    <span className="text-[var(--text-secondary)] font-semibold">StoryOS 槽位 #{item.frameIndex % 3 + 1}</span>
                    <span className="text-[var(--primary)] font-medium">high 档位</span>
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] line-clamp-2 leading-tight font-sans" title={item.prompt}>
                    {item.prompt}
                  </p>
                  {item.driftWarning && (
                    <div className="mt-1.5 p-1 rounded-[var(--radius-xs)] bg-[var(--warning-soft)] border border-[var(--warning)] text-[10px] text-[var(--warning)] leading-tight font-sans">
                      ⚠️ {item.driftWarning}
                    </div>
                  )}
                </div>

                {/* Bottom Actions */}
                <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] flex items-center justify-between">
                  <span className="text-[10px] font-mono font-semibold text-[var(--success)]">
                    一致性 {item.consistencyScore}%
                  </span>
                  <button
                    onClick={() => handleReroll(item.id)}
                    disabled={isRendering}
                    className="text-[10px] font-mono font-semibold text-[var(--primary)] hover:text-[var(--primary-hover)] hover:bg-[var(--primary-soft)] px-1.5 py-0.5 rounded-[var(--radius-xs)] transition-colors disabled:opacity-40"
                  >
                    重抽此帧
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Frame Detail Modal */}
      {activeItemModal && (
        <div className="storyos-overlay fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="storyos-elevated rounded-[var(--radius-lg)] max-w-lg w-full text-[var(--text-primary)] overflow-hidden animate-in fade-in">
            <div className="p-3 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-[var(--primary)] font-semibold">
                  Frame #{activeItemModal.frameIndex} 渲染详情
                </span>
                <span className="storyos-status storyos-status--neutral font-mono">
                  4:5 1080×1350 · StoryOS Engine
                </span>
              </div>
              <button
                onClick={() => setActiveItemModal(null)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                aria-label="关闭 Frame 渲染详情"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-4 space-y-3">
              <div className="aspect-[4/5] max-h-[380px] bg-black rounded-lg overflow-hidden mx-auto">
                <img
                  src={activeItemModal.imageUrl}
                  alt=""
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              </div>
              <div className="p-3 bg-[var(--bg-subtle)] rounded-[var(--radius-md)] border border-[var(--border-subtle)] text-xs font-mono space-y-1">
                <div className="text-[var(--primary)] font-semibold">PROMPT:</div>
                <div className="text-[var(--text-secondary)] leading-relaxed text-[11px]">{activeItemModal.prompt}</div>
                <div className="text-[var(--text-tertiary)] text-[10px] pt-1 border-t border-[var(--border-subtle)] flex justify-between">
                  <span>模型: gpt-image-2 (high)</span>
                  <span>来源: 模拟演示数据</span>
                </div>
              </div>
            </div>
            <div className="p-3 bg-[var(--bg-subtle)] border-t border-[var(--border-subtle)] flex justify-end">
              <button
                onClick={() => setActiveItemModal(null)}
                className="h-9 px-3 rounded-[var(--radius-md)] bg-[var(--primary)] text-xs text-white hover:bg-[var(--primary-hover)]"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
