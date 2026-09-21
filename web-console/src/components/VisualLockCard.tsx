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
    <div id="visual-lock-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide">
                4 张 Visual Lock 核心视觉锁定母版
              </h3>
              <span className="storyos-status storyos-status--neutral font-mono">
                模拟演示数据 · 视觉基准
              </span>
              <span className="storyos-status storyos-status--success font-mono">
                4/4 LOCKED
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
              全剧画风、人物特征、光影质感与空间调性的最高基线，出图差异超标即阻断
            </p>
          </div>
        </div>

        <span className="text-[11px] font-mono text-[var(--text-tertiary)] hidden sm:inline">
          标准画幅: 4:5 (1080×1350) ｜ 模型: gpt-image-2 (high)
        </span>
      </div>

      {/* 4 Cards Grid in 4:5 Aspect Ratio Style */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {visualLocks.map((vl) => (
          <div
            key={vl.id}
            className="group rounded-[var(--radius-md)] border border-[var(--border-normal)] bg-[var(--bg-surface)] overflow-hidden hover:border-[var(--border-strong)] transition-colors flex flex-col justify-between"
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
                <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-black/70 text-amber-300 border border-amber-500/30">
                  {vl.category}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/80 text-[var(--success)] border border-[var(--success)] flex items-center gap-1">
                  <Lock className="w-2.5 h-2.5" />
                  <span>{vl.version}</span>
                </span>
              </div>

              {/* Format tag */}
              <div className="absolute bottom-1.5 left-2 right-2 flex items-center justify-between text-[10px] text-white/75 font-mono">
                <span>4:5 1080×1350</span>
                <span className="text-[var(--warning)] font-bold">{vl.consistencyDelta}</span>
              </div>

              {/* Fullscreen Inspect Icon */}
              <button
                onClick={() => setActiveModalAsset(vl)}
                aria-label={`查看 Visual Lock ${vl.title} 详情`}
                className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 bg-black/40 transition-opacity text-white"
                title="查看高分辨率锁定参数"
              >
                <div className="p-1.5 rounded-[var(--radius-sm)] bg-black/70 border border-white/30">
                  <Maximize2 className="w-4 h-4 text-white" />
                </div>
              </button>
            </div>

            {/* Card Meta Content */}
            <div className="p-2.5 flex-1 flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-semibold text-[var(--text-primary)] truncate mb-1" title={vl.title}>
                  {vl.title}
                </h4>
                <p className="text-[11px] text-[var(--text-tertiary)] line-clamp-1 font-mono flex items-center gap-1">
                  <Palette className="w-3 h-3 text-[var(--text-subtle)] shrink-0" />
                  <span className="truncate">{vl.colorGrade}</span>
                </p>
              </div>

              <div className="mt-2 pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[10px] font-mono text-[var(--text-tertiary)]">
                <span className="truncate max-w-[130px]" title={vl.promptSnippet}>
                  {vl.promptSnippet}
                </span>
                <button
                  onClick={() => setActiveModalAsset(vl)}
                  className="text-[var(--primary)] hover:text-[var(--primary-hover)] font-semibold shrink-0"
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
        <div className="storyos-overlay fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="storyos-elevated rounded-[var(--radius-lg)] max-w-3xl w-full text-[var(--text-primary)] overflow-hidden animate-in fade-in"
            role="dialog"
            aria-modal="true"
            aria-label={`${activeModalAsset.title} Visual Lock 详情`}
          >
            <div className="p-4 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-[var(--primary)]" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Visual Lock 视觉基准母版详情</h3>
                <span className="storyos-status storyos-status--neutral font-mono">
                  {activeModalAsset.id}
                </span>
              </div>
              <button
                onClick={() => setActiveModalAsset(null)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                aria-label="关闭 Visual Lock 详情"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-3">
              <div className="aspect-[21/9] rounded-[var(--radius-md)] overflow-hidden bg-black border border-[var(--border-normal)] relative">
                <img
                  src={activeModalAsset.imageUrl}
                  alt={activeModalAsset.title}
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs font-mono">
                <div className="p-2 bg-[var(--bg-subtle)] rounded-[var(--radius-sm)] border border-[var(--border-subtle)]">
                  <div className="text-[10px] text-[var(--text-tertiary)]">分类</div>
                  <div className="font-semibold text-[var(--text-primary)]">{activeModalAsset.category}</div>
                </div>
                <div className="p-2 bg-[var(--bg-subtle)] rounded-[var(--radius-sm)] border border-[var(--border-subtle)]">
                  <div className="text-[10px] text-[var(--text-tertiary)]">画幅比</div>
                  <div className="font-semibold text-[var(--text-primary)]">{activeModalAsset.aspectRatio}</div>
                </div>
                <div className="p-2 bg-[var(--bg-subtle)] rounded-[var(--radius-sm)] border border-[var(--border-subtle)]">
                  <div className="text-[10px] text-[var(--text-tertiary)]">机位焦距</div>
                  <div className="font-semibold text-[var(--text-primary)]">{activeModalAsset.focalLength}</div>
                </div>
                <div className="p-2 bg-[var(--bg-subtle)] rounded-[var(--radius-sm)] border border-[var(--border-subtle)]">
                  <div className="text-[10px] text-[var(--text-tertiary)]">色差漂移容限</div>
                  <div className="font-semibold text-[var(--success)]">{activeModalAsset.consistencyDelta}</div>
                </div>
              </div>

              <div className="p-3 bg-[var(--bg-subtle)] rounded-[var(--radius-md)] border border-[var(--border-subtle)] text-xs">
                <div className="text-[11px] font-mono text-[var(--primary)] font-semibold mb-1">
                  生成 Prompt 锚点提示词：
                </div>
                <p className="font-mono text-[var(--text-secondary)] leading-relaxed text-[11px]">
                  {activeModalAsset.promptSnippet}
                </p>
              </div>
            </div>

            <div className="p-3 bg-[var(--bg-subtle)] border-t border-[var(--border-subtle)] flex justify-end">
              <button
                onClick={() => setActiveModalAsset(null)}
                className="h-9 px-4 rounded-[var(--radius-md)] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-xs font-medium text-white"
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
