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
    <div id="story-synopsis-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-100">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-amber-500/10 text-amber-600">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide">
                故事梗概与戏剧命题
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700 font-semibold border border-zinc-300">
                模拟演示数据
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">
                {episode.code}
              </span>
            </div>
            <p className="text-[11px] text-zinc-600 mt-0.5">世界观设定、戏剧核心假定与受众定位</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-[11px] px-2 py-0.5 rounded bg-zinc-100 text-zinc-700 font-medium border border-zinc-200">
            {episode.genre}
          </span>
        </div>
      </div>

      {/* Logline Box */}
      <div className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-lg mb-3">
        <div className="text-[10px] font-mono uppercase tracking-wider text-amber-900 font-bold mb-1 flex items-center gap-1">
          <Flame className="w-3 h-3 text-amber-600" />
          <span>核心商业钩子 (Logline)</span>
        </div>
        <p className="text-xs font-semibold text-zinc-900 leading-relaxed">
          “{episode.logline}”
        </p>
      </div>

      {/* Synopsis Body */}
      <div className="mb-3.5">
        <div className="text-[11px] font-mono uppercase tracking-wider text-zinc-500 mb-1">
          完整剧情梗概 (Narrative Synopsis)
        </div>
        <p className="text-xs text-zinc-700 leading-relaxed text-justify">
          {episode.synopsis}
        </p>
      </div>

      {/* Footer Tags: Target Audience & Three-Act Tension */}
      <div className="pt-2.5 border-t border-zinc-100 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        <div className="flex items-center gap-1.5 text-zinc-600">
          <Users className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          <span className="text-zinc-500 text-[11px] font-mono shrink-0">核心受众:</span>
          <span className="text-zinc-800 font-medium truncate">{episode.targetAudience}</span>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-600">
          <Compass className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
          <span className="text-zinc-500 text-[11px] font-mono shrink-0">戏剧节拍:</span>
          <span className="text-zinc-800 font-medium truncate">4 幕 32 镜 • 强反转终局</span>
        </div>
      </div>
    </div>
  );
};
