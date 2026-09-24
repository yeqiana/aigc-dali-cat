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
    <div id="batch-queue-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-zinc-100 gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-zinc-900 text-amber-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide flex items-center gap-1.5">
                <span>5 帧逻辑批次出图队列 (5-Frame Logical Batch Pipeline)</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 font-bold border border-amber-200">
                  BATCH #{batchQueue.batchNumber < 10 ? `0${batchQueue.batchNumber}` : batchQueue.batchNumber}
                </span>
              </h3>
              {/* Clear Source Badge */}
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-300 font-bold">
                示例数据 · 待连接工作区
              </span>
            </div>
            <p className="text-[11px] text-zinc-600 mt-0.5">
              {batchQueue.batchName} • 调度引擎：StoryOS Engine ｜ 图像模型：gpt-image-2 (high) ｜ 画幅：4:5 (1080×1350) ｜ 最大同时出图：3 张
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-zinc-500 hidden md:inline">
            生产规则: 5 帧逻辑批次 / 并发 3
          </span>
          <button
            onClick={onRerunBatch}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-zinc-100 hover:bg-zinc-200 text-xs font-semibold text-zinc-800 border border-zinc-300 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 text-zinc-600" />
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
              className={`rounded-lg border bg-zinc-50 overflow-hidden flex flex-col justify-between transition-all ${
                isWarning
                  ? 'border-amber-300 bg-amber-50/20 ring-1 ring-amber-300/40'
                  : isRendering
                  ? 'border-amber-400 bg-amber-50/40'
                  : 'border-zinc-200 hover:border-zinc-300 shadow-2xs'
              }`}
            >
              {/* Frame Image Aspect Preview (4:5 vertical aspect) */}
              <div className="relative aspect-[4/5] bg-zinc-950 overflow-hidden group">
                <img
                  src={item.imageUrl}
                  alt={`Frame ${item.frameIndex}`}
                  className={`w-full h-full object-cover transition-opacity ${isRendering ? 'opacity-40 blur-xs' : 'opacity-100'}`}
                  referrerPolicy="no-referrer"
                />

                {/* Rendering overlay */}
                {isRendering && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/70 text-amber-300 p-2 text-center">
                    <RefreshCw className="w-5 h-5 animate-spin mb-1" />
                    <span className="text-[10px] font-mono font-bold">StoryOS 批次渲染中 {item.progress}%</span>
                    <span className="text-[9px] text-zinc-400 mt-0.5">gpt-image-2 (high)</span>
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
                      ? 'bg-amber-500 text-zinc-950'
                      : 'bg-zinc-800 text-amber-300'
                  }`}>
                    {isPassed ? 'QA PASS' : isWarning ? 'QA WARN' : 'RENDERING'}
                  </span>
                </div>

                {/* Format pill in image */}
                <div className="absolute bottom-1.5 left-1.5 pointer-events-none">
                  <span className="text-[9px] font-mono bg-black/70 text-zinc-300 px-1 py-0.2 rounded border border-white/10">
                    4:5 1080×1350
                  </span>
                </div>

                {/* Inspect Button on hover */}
                {!isRendering && (
                  <button
                    onClick={() => setActiveItemModal(item)}
                    className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white"
                  >
                    <Maximize2 className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Meta & Stats */}
              <div className="p-2.5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 mb-1">
                    <span className="text-zinc-600 font-semibold">StoryOS 槽位 #{item.frameIndex % 3 + 1}</span>
                    <span className="text-amber-700 font-medium">high 档位</span>
                  </div>
                  <p className="text-[11px] text-zinc-700 line-clamp-2 leading-tight font-sans" title={item.prompt}>
                    {item.prompt}
                  </p>
                  {item.driftWarning && (
                    <div className="mt-1.5 p-1 rounded bg-amber-100/80 border border-amber-300 text-[10px] text-amber-900 leading-tight font-sans">
                      ⚠️ {item.driftWarning}
                    </div>
                  )}
                </div>

                {/* Bottom Actions */}
                <div className="mt-2 pt-1.5 border-t border-zinc-200/80 flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-emerald-700">
                    一致性 {item.consistencyScore}%
                  </span>
                  <button
                    onClick={() => handleReroll(item.id)}
                    disabled={isRendering}
                    className="text-[10px] font-mono font-semibold text-amber-800 hover:text-amber-950 hover:bg-amber-100 px-1.5 py-0.5 rounded transition-colors disabled:opacity-40"
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
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-lg w-full text-zinc-100 shadow-2xl overflow-hidden animate-in fade-in">
            <div className="p-3 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-amber-400 font-bold">
                  Frame #{activeItemModal.frameIndex} 渲染详情
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                  4:5 1080×1350 · StoryOS Engine
                </span>
              </div>
              <button onClick={() => setActiveItemModal(null)} className="text-zinc-400 hover:text-white">
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
              <div className="p-3 bg-zinc-950 rounded border border-zinc-800 text-xs font-mono space-y-1">
                <div className="text-amber-400 font-bold">PROMPT:</div>
                <div className="text-zinc-300 leading-relaxed text-[11px]">{activeItemModal.prompt}</div>
                <div className="text-zinc-500 text-[10px] pt-1 border-t border-zinc-800 flex justify-between">
                  <span>模型: gpt-image-2 (high)</span>
                  <span>来源: 模拟演示数据</span>
                </div>
              </div>
            </div>
            <div className="p-3 bg-zinc-950 border-t border-zinc-800 flex justify-end">
              <button
                onClick={() => setActiveItemModal(null)}
                className="px-3 py-1 rounded bg-zinc-800 text-xs text-white hover:bg-zinc-700"
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
