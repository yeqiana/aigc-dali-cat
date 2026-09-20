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
    <div id="series-library-view" className="space-y-4 text-[var(--text-secondary)] font-sans select-none">
      {/* 顶部标题区 */}
      <div className="storyos-surface flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide flex items-center gap-2">
              <Clapperboard className="w-4 h-4 text-[var(--primary)]" />
              <span>剧集资产全景总览 (StoryOS Series & Episodes)</span>
            </h2>
            <span className="storyos-status storyos-status--neutral font-mono">
              {episodes.length} 剧目就绪
            </span>
          </div>
          <p className="text-xs text-[var(--text-tertiary)] mt-1">全系列图文故事生产资产库、7 大正式阶段流转状态与出图排期</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onNewStoryClick}
            className="h-9 flex items-center gap-1.5 px-3.5 rounded-[var(--radius-md)] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white text-xs font-semibold transition-colors cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-white stroke-[2.5]" />
            <span>新建故事项目</span>
          </button>
        </div>
      </div>

      {/* 过滤与搜索条 */}
      <div className="storyos-surface flex flex-col sm:flex-row items-center justify-between gap-3 p-3 text-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 text-[var(--text-tertiary)] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索剧目代号、标题或题材类型..."
            className="storyos-control w-full pl-8 pr-3 text-xs outline-none focus:border-[var(--focus)] placeholder:text-[var(--text-subtle)]"
          />
        </div>

        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto scrollbar-none">
          {[
            { id: 'ALL', label: '全部阶段' },
            { id: 'IDEA_LOCKED', label: '创意锁定' },
            { id: 'STORYBOARD_LOCKED', label: '分镜锁定' },
            { id: 'VISUAL_CALIBRATED', label: '视觉校准' },
            { id: 'PRODUCTION_PASSED', label: '生产通过' },
            { id: 'PUBLISH_READY', label: '待发布' },
            { id: 'PUBLISHED', label: '已发布' },
            { id: 'DATA_REVIEWED', label: '数据复盘' }
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setFilterStage(item.id)}
              className={`h-8 px-2.5 rounded-[var(--radius-sm)] font-mono text-[11px] font-medium transition-colors shrink-0 cursor-pointer border ${
                filterStage === item.id
                  ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] border-[var(--border-normal)] font-semibold'
                  : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)] border-[var(--border-normal)]'
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
              className={`rounded-[var(--radius-lg)] border bg-[var(--bg-surface)] overflow-hidden transition-colors flex flex-col justify-between cursor-pointer ${
                isActive
                  ? 'border-[var(--primary)] bg-[var(--bg-selected)]'
                  : 'border-[var(--border-normal)] hover:border-[var(--border-strong)]'
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
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-black/90 text-white border border-[var(--border-strong)]">
                      {ep.code}
                    </span>
                    {isActive && (
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[var(--primary)] text-white">
                        当前工作台
                      </span>
                    )}
                  </div>

                  <div className="absolute top-2.5 right-2.5 flex items-center gap-1">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-black/90 text-white border border-[var(--border-strong)]">
                      {ep.currentStage}
                    </span>
                  </div>

                  <div className="absolute bottom-2.5 left-2.5 right-2.5 text-white">
                    <h3 className="text-sm font-bold truncate text-white">{ep.title}</h3>
                    <p className="text-[10px] text-white/70 font-mono truncate">{ep.genre}</p>
                  </div>
                </div>

                {/* 介绍与指标 */}
                <div className="p-3.5 space-y-3">
                  <p className="text-xs text-[var(--text-secondary)] line-clamp-2 leading-relaxed">
                    {ep.synopsis}
                  </p>

                  {/* 进度条 */}
                  <div>
                    <div className="flex justify-between text-[11px] font-mono text-[var(--text-tertiary)] mb-1">
                      <span>已完成帧数</span>
                      <span className="font-semibold text-[var(--text-primary)] tabular-nums">
                        {ep.completedFrames} / {ep.totalFrames} 帧 ({progressPercent}%)
                      </span>
                    </div>
                    <div className="w-full bg-[var(--bg-muted)] h-1.5 rounded-full overflow-hidden border border-[var(--border-subtle)]">
                      <div
                        className="bg-[var(--primary)] h-full rounded-full transition-[width]"
                        style={{ width: `${progressPercent}%` }}
                      />
                    </div>
                  </div>

                  {/* 规格 */}
                  <div className="text-[11px] font-mono text-[var(--text-secondary)] bg-[var(--bg-subtle)] p-2 rounded-[var(--radius-md)] border border-[var(--border-subtle)] flex items-center justify-between">
                    <span className="truncate text-[var(--text-tertiary)]">
                      {ep.runtimeRequest.imageModel || 'gpt-image-2'}
                    </span>
                    <span className="text-[var(--text-primary)] font-semibold">{ep.runtimeRequest.aspectRatio || '4:5 1080×1350'}</span>
                  </div>
                </div>
              </div>

              {/* 底部操作条 */}
              <div className="p-3 bg-[var(--bg-subtle)] border-t border-[var(--border-subtle)] flex items-center justify-between">
                <span className="text-[10px] font-mono text-[var(--text-tertiary)]">
                  更新于 {ep.updatedAt}
                </span>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectEpisode(ep);
                    onGoToWorkbench();
                  }}
                  className="h-8 flex items-center gap-1 text-xs font-semibold text-[var(--primary)] hover:text-[var(--primary-hover)] transition-colors px-2 rounded-[var(--radius-sm)] bg-[var(--bg-surface)] hover:bg-[var(--primary-soft)] border border-[var(--border-normal)]"
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
