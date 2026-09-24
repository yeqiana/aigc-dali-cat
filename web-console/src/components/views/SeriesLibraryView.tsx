import React, { useState } from 'react';
import {
  Clapperboard,
  ArrowRight,
  Plus,
  Search,
  Sparkles
} from 'lucide-react';
import { Episode } from '../../types';

interface SeriesLibraryViewProps {
  episodes: Episode[];
  activeEpisode: Episode;
  onSelectEpisode: (episode: Episode) => void;
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
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStage, setFilterStage] = useState<string>('ALL');

  const filteredEpisodes = episodes.filter(ep => {
    const matchesFilter = filterStage === 'ALL' || ep.currentStage === filterStage;
    const matchesSearch = ep.title.includes(searchQuery) || ep.genre.includes(searchQuery) || ep.code.includes(searchQuery);
    return matchesFilter && matchesSearch;
  });

  return (
    <div id="series-library-view" className="space-y-4 text-[var(--text-secondary)] font-sans select-none">
      {/* 顶部标题区 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[var(--bg-surface)] p-3 rounded-[8px] border border-[var(--border-subtle)]">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center gap-2">
              <Clapperboard className="w-4 h-4 text-[#58A6FF]" />
              <span>剧集资产</span>
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-normal)] text-[var(--text-primary)] font-bold">
              {episodes.length} 部
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onNewStoryClick}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-[4px] bg-[var(--text-primary)] hover:opacity-90 text-[var(--bg-app)] text-xs font-semibold shadow-xs transition-opacity cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>新建项目</span>
          </button>
        </div>
      </div>

      {/* 过滤与搜索条 */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[var(--bg-surface)] p-2.5 rounded-[8px] border border-[var(--border-subtle)] text-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 text-[var(--text-tertiary)] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索剧集代号、标题..."
            className="w-full pl-8 pr-3 py-1.5 rounded-[4px] bg-[var(--bg-app)] border border-[var(--border-normal)] focus:outline-hidden focus:border-[#58A6FF] text-xs text-[var(--text-primary)] placeholder-[var(--text-tertiary)] font-mono"
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
              className={`px-2.5 py-1 rounded-[4px] font-mono text-[11px] font-medium transition-colors shrink-0 cursor-pointer border ${
                filterStage === item.id
                  ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-bold border-[#58A6FF]'
                  : 'bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border-[var(--border-subtle)]'
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
              className={`rounded-[8px] border bg-[var(--bg-surface)] overflow-hidden shadow-xs transition-all flex flex-col justify-between cursor-pointer ${
                isActive
                  ? 'border-[#58A6FF] ring-1 ring-[#58A6FF]/40 shadow-md'
                  : 'border-[var(--border-subtle)] hover:border-[var(--border-strong)]'
              }`}
              onClick={() => {
                onSelectEpisode(ep);
              }}
            >
              <div>
                {/* 封面预览 */}
                <div className="relative aspect-[16/9] bg-[var(--bg-workspace)] overflow-hidden">
                  <img
                    src={ep.coverImage}
                    alt={ep.title}
                    className="w-full h-full object-cover opacity-85 hover:opacity-100 transition-opacity"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />

                  <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-black/80 text-white border border-white/20 backdrop-blur-xs">
                      {ep.code}
                    </span>
                    {isActive && (
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white text-black shadow-xs">
                        当前工作台
                      </span>
                    )}
                  </div>

                  <div className="absolute top-2.5 right-2.5 flex items-center gap-1">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-black/80 text-zinc-200 border border-white/20 backdrop-blur-xs">
                      {ep.currentStage}
                    </span>
                  </div>

                  <div className="absolute bottom-2.5 left-2.5 right-2.5 text-white">
                    <h3 className="text-sm font-bold truncate text-white">{ep.title}</h3>
                    <p className="text-[10px] text-zinc-300 font-mono truncate">{ep.genre}</p>
                  </div>
                </div>

                {/* 进度 */}
                <div className="p-3.5 space-y-2.5">
                  <div>
                    <div className="flex justify-between text-[11px] font-mono text-[var(--text-tertiary)] mb-1 whitespace-nowrap">
                      <span>生产进度</span>
                      <span className="font-semibold text-[var(--text-primary)]">
                        {ep.completedFrames}/{ep.totalFrames} 帧 ({progressPercent}%)
                      </span>
                    </div>
                    <div className="w-full bg-[var(--bg-workspace)] h-1.5 rounded-full overflow-hidden border border-[var(--border-subtle)]">
                      <div
                        className="bg-[#58A6FF] h-full rounded-full transition-all"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* 底部操作条 */}
              <div className="p-3 bg-[var(--bg-elevated)] border-t border-[var(--border-subtle)] flex items-center justify-between whitespace-nowrap">
                <span className="text-[10px] font-mono text-[var(--text-tertiary)] truncate max-w-[140px]">
                  更新于 {ep.updatedAt}
                </span>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectEpisode(ep);
                    onGoToWorkbench();
                  }}
                  className="flex items-center gap-1 text-xs font-semibold text-[var(--text-primary)] hover:text-[#58A6FF] transition-colors px-2.5 py-1 rounded-[4px] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-normal)] cursor-pointer"
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
