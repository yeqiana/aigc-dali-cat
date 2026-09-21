import React, { useState } from 'react';
import { Activity, Check, ChevronDown, PanelRight, Share2 } from 'lucide-react';
import type { Episode, NavigationTab } from '../types';

interface HeaderBarProps {
  currentTab: NavigationTab;
  activeEpisode: Episode;
  allEpisodes: Episode[];
  onSelectEpisode: (episode: Episode) => void;
  onToggleContextPanel?: () => void;
  contextPanelOpen?: boolean;
}

const SECTION_META: Record<NavigationTab, { title: string; badge?: string; tone?: 'success' | 'warning' | 'neutral' }> = {
  production_monitor: { title: 'Production Monitor', badge: 'MYSQL AUTHORITY · READ ONLY', tone: 'success' },
  episodes: { title: 'Episode Index', badge: 'MYSQL AUTHORITY · READ ONLY', tone: 'success' },
  logs: { title: 'Runtime Logs', badge: 'CAPABILITY NOT CONNECTED', tone: 'warning' },
  settings: { title: 'Settings', badge: 'LOCAL CONFIG VIEW', tone: 'neutral' },
  workbench: { title: 'Workbench' },
};

export const HeaderBar: React.FC<HeaderBarProps> = ({
  currentTab,
  activeEpisode,
  allEpisodes,
  onSelectEpisode,
  onToggleContextPanel,
  contextPanelOpen = true,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [shared, setShared] = useState(false);
  const isWorkbench = currentTab === 'workbench';
  const meta = SECTION_META[currentTab];

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setShared(true);
      setTimeout(() => setShared(false), 1500);
    } catch {
      setShared(false);
    }
  };

  const progressPercent = Math.round((activeEpisode.completedFrames / activeEpisode.totalFrames) * 100);

  return (
    <header className="h-[var(--header-height)] px-4 border-b border-[var(--border-normal)] bg-[var(--bg-workspace)] text-[var(--text-secondary)] flex items-center justify-between shrink-0 select-none z-20 text-xs">
      <div className="flex items-center gap-2 min-w-0">
        {isWorkbench ? (
          <>
            <div className="relative">
              <button type="button" onClick={() => setDropdownOpen(!dropdownOpen)} aria-expanded={dropdownOpen} aria-haspopup="listbox" className="flex items-center gap-1.5 font-medium text-[var(--text-primary)] px-2 py-1 rounded-[var(--radius-sm)] hover:bg-[var(--bg-hover)] border border-transparent hover:border-[var(--border-subtle)]">
                <span className="font-mono text-[var(--text-tertiary)] font-semibold">{activeEpisode.code}</span>
                <span className="font-semibold text-[var(--text-primary)]">{activeEpisode.title}</span>
                <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-tertiary)] transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
              </button>
              {dropdownOpen && (
                <div className="absolute left-0 top-full mt-1 w-64 storyos-elevated p-1 z-50 text-xs">
                  <div className="px-2 py-1 text-[10px] font-mono text-[var(--text-tertiary)] uppercase border-b border-[var(--border-subtle)] mb-1">LOCAL WORKBENCH DEMO</div>
                  {allEpisodes.map((ep) => (
                    <button key={ep.id} type="button" onClick={() => { onSelectEpisode(ep); setDropdownOpen(false); }} className={`w-full text-left px-2 py-1.5 rounded-[var(--radius-sm)] flex items-center justify-between ${ep.id === activeEpisode.id ? 'bg-[var(--bg-selected)] text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'}`}>
                      <span className="truncate">{ep.code} {ep.title}</span>
                      <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{ep.completedFrames}/{ep.totalFrames}</span>
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
            <span className="storyos-status storyos-status--warning font-mono ml-1" title="Workbench 使用本地示例数据，不代表生产 Authority">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
              LOCAL DEMO · NOT AUTHORITY
            </span>
          </>
        ) : (
          <>
            <span className="font-semibold text-[var(--text-primary)]">{meta.title}</span>
            {meta.badge && (
              <span className={`storyos-status storyos-status--${meta.tone || 'neutral'} font-mono`}>
                <span className={`w-1.5 h-1.5 rounded-full ${meta.tone === 'success' ? 'bg-[var(--success)]' : meta.tone === 'warning' ? 'bg-[var(--warning)]' : 'bg-[var(--text-tertiary)]'}`} />
                {meta.badge}
              </span>
            )}
          </>
        )}
      </div>

      <div className="flex items-center gap-2 text-[var(--text-secondary)]">
        <button type="button" onClick={handleShare} aria-label="复制当前页面链接" className="storyos-control h-8 px-2.5 flex items-center gap-1.5 text-xs font-mono">
          {shared ? <Check className="w-3.5 h-3.5 text-[var(--success)]" /> : <Share2 className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />}
          <span>{shared ? '已复制' : '分享'}</span>
        </button>
        {isWorkbench && onToggleContextPanel && (
          <button type="button" onClick={onToggleContextPanel} aria-expanded={contextPanelOpen} className={`h-8 px-2.5 rounded-[var(--radius-sm)] border flex items-center gap-1.5 text-xs font-mono ${contextPanelOpen ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] border-[var(--border-normal)]' : 'bg-[var(--bg-surface)] text-[var(--text-tertiary)] border-[var(--border-normal)] hover:text-[var(--text-primary)]'}`}>
            <PanelRight className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">右侧面板</span>
          </button>
        )}
      </div>
    </header>
  );
};
