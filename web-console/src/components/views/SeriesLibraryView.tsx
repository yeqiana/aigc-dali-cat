import React, { useState } from 'react';
import {
  Clapperboard,
  Search,
  Plus,
  ArrowRight,
  Check,
  FolderOpen
} from 'lucide-react';
import { Episode } from '../../types';

interface SeriesLibraryViewProps {
  episodes: Episode[];
  activeEpisode: Episode;
  onSelectEpisode: (ep: Episode) => void;
  onGoToWorkbench: () => void;
  onNewStoryClick: () => void;
}

export const SeriesLibraryView: React.FC<SeriesLibraryViewProps> = ({
  episodes,
  activeEpisode,
  onSelectEpisode,
  onGoToWorkbench,
  onNewStoryClick,
}) => {
  const [filterStage, setFilterStage] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredEpisodes = episodes.filter(ep => {
    const matchesFilter = filterStage === 'ALL' || ep.currentStage === filterStage;
    const matchesSearch = ep.title.includes(searchQuery) || ep.genre.includes(searchQuery) || ep.code.includes(searchQuery);
    return matchesFilter && matchesSearch;
  });

  return (
    <div id="series-library-view" className="space-y-4 text-zinc-300 font-sans select-none">
      {/* 顶部标题区 - 纯黑底白字 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#0a0a0c] p-4 rounded-xl border border-[#222226]">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clapperboard className="w-4 h-4 text-white" />
              <span>剧集资产全景总览 (StoryOS Series & Episodes)</span>
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-black font-bold">
              {episodes.length} 剧目就绪
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">全系列图文故事生产资产库、7 大正式阶段流转状态与出图排期</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onNewStoryClick}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-white hover:bg-zinc-200 text-black text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-black stroke-[2.5]" />
            <span>新建故事项目</span>
          </button>
        </div>
      </div>

      {/* 过滤与搜索条 */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#0a0a0c] p-3 rounded-xl border border-[#222226] text-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索剧目代号、标题或题材类型..."
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-[#000000] border border-[#27272a] focus:outline-hidden focus:border-white text-xs text-white placeholder-zinc-500"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto scrollbar-none">
          {[
            { id: 'ALL', label: '全部阶段' },
            { id: 'IDEA_LOCK', label: '创意锁定' },
            { id: 'STORYBOARD_LOCK', label: '分镜锁定' },
            { id: 'VISUAL_CALIBRATE', label: '视觉校准' },
            { id: 'PROD_APPROVED', label: '生产通过' },
            { id: 'READY_TO_PUBLISH', label: '待发布' },
            { id: 'PUBLISHED', label: '已发布' }
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setFilterStage(item.id)}
              className={`px-2.5 py-1 rounded-md font-mono text-[11px] font-medium transition-colors shrink-0 cursor-pointer ${
                filterStage === item.id
                  ? 'bg-white text-black font-semibold shadow-xs'
                  : 'bg-[#141416] text-zinc-400 hover:text-white hover:bg-[#1a1a1e] border border-[#27272a]'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* 剧集网格卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEpisodes.map((ep) => {
          const isActive = ep.id === activeEpisode.id;
          const progressPercent = Math.round((ep.completedFrames / ep.totalFrames) * 100);

          return (
            <div
              key={ep.id}
              className={`rounded-xl border bg-[#0a0a0c] overflow-hidden shadow-xs transition-all flex flex-col justify-between cursor-pointer ${
                isActive
                  ? 'border-white ring-1 ring-white/60 shadow-lg'
                  : 'border-[#222226] hover:border-[#38383e]'
              }`}
              onClick={() => {
                onSelectEpisode(ep);
              }}
            >
              <div>
                {/* 封面预览 */}
                <div className="relative aspect-[16/9] bg-black overflow-hidden">
                  <img
                    src={ep.coverImage}
                    alt={ep.title}
                    className="w-full h-full object-cover opacity-80 hover:opacity-100 transition-opacity"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />

                  <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-black/90 text-white border border-[#333338] backdrop-blur-xs">
                      {ep.code}
                    </span>
                    {isActive && (
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white text-black">
                        当前工作台
                      </span>
                    )}
                  </div>

                  <div className="absolute top-2.5 right-2.5 flex items-center gap-1">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-black/90 text-zinc-200 border border-[#333338] backdrop-blur-xs">
                      {ep.currentStage}
                    </span>
                  </div>

                  <div className="absolute bottom-2.5 left-2.5 right-2.5 text-white">
                    <h3 className="text-sm font-bold truncate text-white">{ep.title}</h3>
                    <p className="text-[10px] text-zinc-400 font-mono truncate">{ep.genre}</p>
                  </div>
                </div>

                {/* 介绍与指标 */}
                <div className="p-3.5 space-y-3">
                  <p className="text-xs text-zinc-400 line-clamp-2 leading-relaxed">
                    {ep.synopsis}
                  </p>

                  {/* 进度条 - 纯黑白 */}
                  <div>
                    <div className="flex justify-between text-[11px] font-mono text-zinc-400 mb-1">
                      <span>已完成帧数</span>
                      <span className="font-bold text-white">
                        {ep.completedFrames} / {ep.totalFrames} 帧 ({progressPercent}%)
                      </span>
                    </div>
                    <div className="w-full bg-[#18181b] h-1.5 rounded-full overflow-hidden border border-[#27272a]">
                      <div
                        className="bg-white h-full rounded-full transition-all"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>

                  {/* 规格 */}
                  <div className="text-[11px] font-mono text-zinc-300 bg-[#000000] p-2 rounded-lg border border-[#222226] flex items-center justify-between">
                    <span className="truncate text-zinc-400">
                      {ep.runtimeRequest.imageModel || 'gpt-image-2'}
                    </span>
                    <span className="text-white font-bold">{ep.runtimeRequest.aspectRatio || '4:5 1080×1350'}</span>
                  </div>
                </div>
              </div>

              {/* 底部操作条 */}
              <div className="p-3 bg-[#050507] border-t border-[#1f1f23] flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-500">
                  更新于 {ep.updatedAt}
                </span>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectEpisode(ep);
                    onGoToWorkbench();
                  }}
                  className="flex items-center gap-1 text-xs font-bold text-white hover:text-zinc-300 transition-colors px-2 py-1 rounded bg-[#18181b] hover:bg-[#222226] border border-[#2e2e33]"
                >
                  <span>进入工作台</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
