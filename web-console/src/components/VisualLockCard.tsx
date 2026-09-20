import React, { useState } from 'react';
import {
  Lock,
  Camera,
  Layers,
  Sparkles,
  Maximize2,
  Sliders,
  CheckCircle2,
  X,
  Palette
} from 'lucide-react';
import { VisualLockAsset } from '../types';

interface VisualLockCardProps {
  visualLocks: VisualLockAsset[];
}

export const VisualLockCard: React.FC<VisualLockCardProps> = ({ visualLocks }) => {
  const [activeModalAsset, setActiveModalAsset] = useState<VisualLockAsset | null>(null);

  return (
    <div id="visual-lock-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-zinc-900 text-amber-400">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide">
                4 张 Visual Lock 核心视觉锁定母版
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700 font-semibold border border-zinc-300">
                模拟演示数据 · 视觉基准
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">
                4/4 LOCKED
              </span>
            </div>
            <p className="text-[11px] text-zinc-600 mt-0.5">
              全剧画风、人物特征、光影质感与空间调性的最高基线，出图差异超标即阻断
            </p>
          </div>
        </div>

        <span className="text-[11px] font-mono text-zinc-600 hidden sm:inline">
          标准画幅: 4:5 (1080×1350) ｜ 模型: gpt-image-2 (high)
        </span>
      </div>

      {/* 4 Cards Grid in 4:5 Aspect Ratio Style */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {visualLocks.map((vl) => (
          <div
            key={vl.id}
            className="group rounded-lg border border-zinc-200 bg-zinc-50 overflow-hidden hover:border-zinc-400 transition-all flex flex-col justify-between"
          >
            {/* Image Preview Container (4:5 vertical aspect) */}
            <div className="relative aspect-[4/5] bg-zinc-900 overflow-hidden">
              <img
                src={vl.imageUrl}
                alt={vl.title}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                referrerPolicy="no-referrer"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none" />

              {/* Badges on top */}
              <div className="absolute top-2 left-2 right-2 flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-black/70 text-amber-300 border border-amber-500/30 backdrop-blur-xs">
                  {vl.category}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 flex items-center gap-1 backdrop-blur-xs">
                  <Lock className="w-2.5 h-2.5" />
                  <span>{vl.version}</span>
                </span>
              </div>

              {/* Format tag */}
              <div className="absolute bottom-1.5 left-2 right-2 flex items-center justify-between text-[10px] text-zinc-300 font-mono">
                <span>4:5 1080×1350</span>
                <span className="text-amber-300 font-bold">{vl.consistencyDelta}</span>
              </div>

              {/* Fullscreen Inspect Icon */}
              <button
                onClick={() => setActiveModalAsset(vl)}
                className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/40 transition-opacity text-white"
                title="查看高分辨率锁定参数"
              >
                <div className="p-1.5 rounded-full bg-black/70 border border-white/30">
                  <Maximize2 className="w-4 h-4 text-white" />
                </div>
              </button>
            </div>

            {/* Card Meta Content */}
            <div className="p-2.5 flex-1 flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-bold text-zinc-900 truncate mb-1" title={vl.title}>
                  {vl.title}
                </h4>
                <p className="text-[11px] text-zinc-500 line-clamp-1 font-mono flex items-center gap-1">
                  <Palette className="w-3 h-3 text-zinc-400 shrink-0" />
                  <span className="truncate">{vl.colorGrade}</span>
                </p>
              </div>

              <div className="mt-2 pt-2 border-t border-zinc-200/70 flex items-center justify-between text-[10px] font-mono text-zinc-600">
                <span className="truncate max-w-[130px]" title={vl.promptSnippet}>
                  {vl.promptSnippet}
                </span>
                <button
                  onClick={() => setActiveModalAsset(vl)}
                  className="text-amber-700 hover:text-amber-900 font-semibold underline shrink-0"
                >
                  详情
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal for Visual Lock Details */}
      {activeModalAsset && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-3xl w-full text-zinc-100 shadow-2xl overflow-hidden animate-in fade-in">
            <div className="p-4 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-white">Visual Lock 视觉基准母版详情</h3>
                <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-amber-300 font-mono">
                  {activeModalAsset.id}
                </span>
              </div>
              <button
                onClick={() => setActiveModalAsset(null)}
                className="text-zinc-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-3">
              <div className="aspect-[21/9] rounded-lg overflow-hidden bg-black border border-zinc-800 relative">
                <img
                  src={activeModalAsset.imageUrl}
                  alt={activeModalAsset.title}
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
                <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                  <div className="text-[10px] text-zinc-500">分类</div>
                  <div className="font-bold text-white">{activeModalAsset.category}</div>
                </div>
                <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                  <div className="text-[10px] text-zinc-500">画幅比</div>
                  <div className="font-bold text-white">{activeModalAsset.aspectRatio}</div>
                </div>
                <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                  <div className="text-[10px] text-zinc-500">机位焦距</div>
                  <div className="font-bold text-white">{activeModalAsset.focalLength}</div>
                </div>
                <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                  <div className="text-[10px] text-zinc-500">色差漂移容限</div>
                  <div className="font-bold text-emerald-400">{activeModalAsset.consistencyDelta}</div>
                </div>
              </div>

              <div className="p-3 bg-zinc-950 rounded border border-zinc-800 text-xs">
                <div className="text-[11px] font-mono text-amber-400 font-semibold mb-1">
                  生成 Prompt 锚点提示词：
                </div>
                <p className="font-mono text-zinc-300 leading-relaxed text-[11px]">
                  {activeModalAsset.promptSnippet}
                </p>
              </div>
            </div>

            <div className="p-3 bg-zinc-950 border-t border-zinc-800 flex justify-end">
              <button
                onClick={() => setActiveModalAsset(null)}
                className="px-4 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-medium text-white"
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
