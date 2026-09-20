import React, { useState } from 'react';
import {
  ChevronDown,
  Share2,
  PanelRight,
  Check,
  Activity
} from 'lucide-react';
import { Episode } from '../types';

interface HeaderBarProps {
  activeEpisode: Episode;
  allEpisodes: Episode[];
  onSelectEpisode: (episode: Episode) => void;
  onToggleContextPanel?: () => void;
  contextPanelOpen?: boolean;
  onConnectWorkspace?: () => void;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({
  activeEpisode,
  allEpisodes,
  onSelectEpisode,
  onToggleContextPanel,
  contextPanelOpen = true,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [shared, setShared] = useState(false);

  const handleShare = () => {
    setShared(true);
    setTimeout(() => setShared(false), 1500);
  };

  const progressPercent = Math.round((activeEpisode.completedFrames / activeEpisode.totalFrames) * 100);

  return (
    <header className="h-[var(--header-height)] px-4 border-b border-[var(--border-normal)] bg-[var(--bg-workspace)] text-[var(--text-secondary)] flex items-center justify-between shrink-0 select-none z-20 text-xs">
      {/* 左侧：标题与下拉 */}
      <div className="flex items-center gap-2">
        <div className="relative">
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-1.5 font-medium text-[var(--text-primary)] transition-colors px-2 py-1 rounded-[var(--radius-sm)] hover:bg-[var(--bg-hover)] border border-transparent hover:border-[var(--border-subtle)] cursor-pointer"
          >
            <span className="font-mono text-[var(--text-tertiary)] font-semibold">{activeEpisode.code}</span>
            <span className="font-semibold text-[var(--text-primary)]">{activeEpisode.title}</span>
            <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-tertiary)] transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 top-full mt-1 w-64 storyos-elevated p-1 z-50 text-xs">
              <div className="px-2 py-1 text-[10px] font-mono text-[var(--text-tertiary)] uppercase border-b border-[var(--border-subtle)] mb-1">
                切换当前剧目
              </div>
              {allEpisodes.map((ep) => (
                <button
                  key={ep.id}
                  type="button"
                  onClick={() => {
                    onSelectEpisode(ep);
                    setDropdownOpen(false);
                  }}
                  className={`w-full text-left px-2 py-1.5 rounded-[var(--radius-sm)] transition-colors flex items-center justify-between cursor-pointer ${
                    ep.id === activeEpisode.id
                      ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] font-semibold border border-[var(--border-normal)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)]'
                  }`}
                >
                  <span className="truncate">{ep.code} {ep.title}</span>
                  <span className={`text-[10px] font-mono shrink-0 ml-2 ${ep.id === activeEpisode.id ? 'text-[var(--primary)]' : 'text-[var(--text-tertiary)]'}`}>
                    {ep.completedFrames}/{ep.totalFrames} 帧
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <span className="text-[11px] font-mono text-[var(--text-tertiary)] flex items-center gap-1.5 ml-2">
          <Activity className="w-3 h-3 text-[var(--info)]" />
          <span>{activeEpisode.currentStage}</span>
          <span className="text-[var(--text-disabled)]">·</span>
          <span>{activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧 ({progressPercent}%)</span>
        </span>
      </div>

      {/* 右侧：操作按钮（精密工控风格） */}
      <div className="flex items-center gap-2 text-[var(--text-secondary)]">
        <button
          type="button"
          onClick={handleShare}
          className="flex items-center gap-1.5 h-8 px-2.5 rounded-[var(--radius-sm)] bg-[var(--bg-surface)] border border-[var(--border-normal)] hover:bg-[var(--bg-subtle)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors text-xs cursor-pointer font-mono"
          title="分享剧目链接"
        >
          {shared ? <Check className="w-3.5 h-3.5 text-[var(--success)]" /> : <Share2 className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />}
          <span>{shared ? '已复制' : '分享剧目'}</span>
        </button>

        {onToggleContextPanel && (
          <button
            type="button"
            onClick={onToggleContextPanel}
            className={`h-8 px-2.5 rounded-[var(--radius-sm)] border transition-colors flex items-center gap-1.5 text-xs cursor-pointer font-mono ${
              contextPanelOpen
                ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] font-semibold border-[var(--border-normal)]'
                : 'bg-[var(--bg-surface)] text-[var(--text-tertiary)] border-[var(--border-normal)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)]'
            }`}
            title="展开/收起右侧面板"
          >
            <PanelRight className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">右侧面板</span>
          </button>
        )}
      </div>
    </header>
  );
};
