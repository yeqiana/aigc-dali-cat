import React, { useState } from 'react';
import {
  ChevronDown,
  Share2,
  PanelRight,
  Check,
  Settings
} from 'lucide-react';
import { Episode } from '../types';

interface HeaderBarProps {
  activeEpisode: Episode;
  allEpisodes: Episode[];
  onSelectEpisode: (episode: Episode) => void;
  onToggleContextPanel?: () => void;
  contextPanelOpen?: boolean;
  onConnectWorkspace?: () => void;
  onOpenSettings?: () => void;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({
  activeEpisode,
  allEpisodes,
  onSelectEpisode,
  onToggleContextPanel,
  contextPanelOpen = true,
  onOpenSettings,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [shared, setShared] = useState(false);

  const handleShare = () => {
    setShared(true);
    setTimeout(() => setShared(false), 1500);
  };

  const progressPercent = Math.round((activeEpisode.completedFrames / activeEpisode.totalFrames) * 100);

  return (
    <header className="h-[48px] px-4 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-secondary)] flex items-center justify-between shrink-0 select-none z-20 text-xs transition-colors">
      {/* 左侧：标题与下拉 */}
      <div className="flex items-center gap-2">
        <div className="relative">
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-1.5 font-medium text-[var(--text-primary)] transition-colors px-2 py-1 rounded-[4px] hover:bg-[var(--bg-hover)] border border-transparent hover:border-[var(--border-subtle)] cursor-pointer"
          >
            <span className="font-mono text-[var(--text-tertiary)] font-semibold">{activeEpisode.code}</span>
            <span className="font-semibold text-[var(--text-primary)]">{activeEpisode.title}</span>
            <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-tertiary)] transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 top-full mt-1 w-64 theme-popover-menu rounded-[6px] p-1 z-50 text-xs shadow-2xl">
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
                  className={`w-full text-left px-2 py-1.5 rounded-[4px] transition-colors flex items-center justify-between cursor-pointer ${
                    ep.id === activeEpisode.id
                      ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-semibold border border-[var(--border-normal)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                  }`}
                >
                  <span className="truncate">{ep.code} {ep.title}</span>
                  <span className={`text-[10px] font-mono shrink-0 ml-2 ${ep.id === activeEpisode.id ? 'text-[#58A6FF]' : 'text-[var(--text-tertiary)]'}`}>
                    {ep.completedFrames}/{ep.totalFrames} 帧
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <span className="text-[11px] font-mono text-[#737D8A] flex items-center gap-1.5 ml-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#58A6FF]" />
          <span>{activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧 ({progressPercent}%)</span>
        </span>
      </div>

      {/* 右侧：纯净运行状态指标 (原 [配置][分享][面板] 三个按钮已收纳至左下角头像菜单) */}
      <div className="flex items-center gap-3 text-xs font-mono text-[var(--text-tertiary)]">
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-[4px] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3FB950] animate-pulse" />
          <span className="text-[var(--text-secondary)]">调度引擎就绪</span>
        </div>
      </div>
    </header>
  );
};
