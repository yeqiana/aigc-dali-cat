import React from 'react';
import {
  BookOpen,
  Tag,
  Users,
  Compass,
  Flame,
  FileText,
  Clock,
  Sparkles
} from 'lucide-react';
import { Episode } from '../types';

interface StorySynopsisCardProps {
  episode: Episode;
}

export const StorySynopsisCard: React.FC<StorySynopsisCardProps> = ({ episode }) => {
  return (
    <div id="story-synopsis-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide">
                故事梗概与戏剧命题
              </h3>
              <span className="storyos-status storyos-status--neutral font-mono">
                模拟演示数据
              </span>
              <span className="storyos-status storyos-status--info font-mono">
                {episode.code}
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">世界观设定、戏剧核心假定与受众定位</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="storyos-status storyos-status--neutral">
            {episode.genre}
          </span>
        </div>
      </div>

      {/* Logline Box */}
      <div className="p-3 bg-[var(--primary-soft)] border border-[var(--border-normal)] rounded-[var(--radius-md)] mb-3">
        <div className="text-[10px] font-mono uppercase tracking-wider text-[var(--primary-hover)] font-semibold mb-1 flex items-center gap-1">
          <Flame className="w-3 h-3 text-[var(--primary)]" />
          <span>核心商业钩子 (Logline)</span>
        </div>
        <p className="text-xs font-semibold text-[var(--text-primary)] leading-relaxed">
          “{episode.logline}”
        </p>
      </div>

      {/* Synopsis Body */}
      <div className="mb-3.5">
        <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)] mb-1">
          完整剧情梗概 (Narrative Synopsis)
        </div>
        <p className="text-xs text-[var(--text-secondary)] leading-relaxed text-justify">
          {episode.synopsis}
        </p>
      </div>

      {/* Footer Tags: Target Audience & Three-Act Tension */}
      <div className="pt-2.5 border-t border-[var(--border-subtle)] grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-1.5 text-[var(--text-secondary)]">
          <Users className="w-3.5 h-3.5 text-[var(--text-subtle)] shrink-0" />
          <span className="text-[var(--text-tertiary)] text-[11px] font-mono shrink-0">核心受众:</span>
          <span className="text-[var(--text-primary)] font-medium truncate">{episode.targetAudience}</span>
        </div>

        <div className="flex items-center gap-1.5 text-[var(--text-secondary)]">
          <Compass className="w-3.5 h-3.5 text-[var(--text-subtle)] shrink-0" />
          <span className="text-[var(--text-tertiary)] text-[11px] font-mono shrink-0">戏剧节拍:</span>
          <span className="text-[var(--text-primary)] font-medium truncate">4 幕 32 镜 • 强反转终局</span>
        </div>
      </div>
    </div>
  );
};
