import React from 'react';
import {
  Activity,
  Bell,
  Film,
  FolderOpen,
  LayoutDashboard,
  Search,
  Settings,
  ShieldCheck,
  SquarePen,
} from 'lucide-react';
import type { Episode, NavigationTab } from '../types';

interface SidebarProps {
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  activeEpisode: Episode;
  allEpisodes: Episode[];
  onSelectEpisode: (episode: Episode) => void;
  onNewConversation?: () => void;
  onOpenSearch?: () => void;
  onOpenNotifications?: () => void;
}

function navClass(active: boolean) {
  return `w-full h-9 flex items-center gap-2 px-3 rounded-[var(--radius-md)] text-xs transition-colors ${active
    ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-medium'
    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  activeEpisode,
  allEpisodes,
  onSelectEpisode,
  onNewConversation,
  onOpenSearch,
  onOpenNotifications,
}) => {
  const isWorkbench = currentTab === 'workbench';

  return (
    <aside className="w-[var(--sidebar-width)] shrink-0 bg-[var(--bg-sidebar)] border-r border-[var(--border-subtle)] flex flex-col h-full select-none text-[13px] text-[var(--text-secondary)]">
      <div className="h-[var(--header-height)] px-3 flex items-center justify-between border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
          <span className="tracking-wide font-mono text-sm font-bold">StoryOS</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-[var(--radius-xs)] bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-normal)] font-mono">OPS</span>
        </div>
        {isWorkbench && (
          <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
            <button type="button" onClick={onOpenSearch} aria-label="搜索本地 Workbench 示例" className="p-1 hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)]" title="搜索本地 Workbench 示例 (Ctrl+K)">
              <Search className="w-3.5 h-3.5" />
            </button>
            <button type="button" onClick={onOpenNotifications} aria-label="查看本地示例通知" className="p-1 hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded-[var(--radius-sm)]" title="本地示例通知">
              <Bell className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4 scrollbar-none">
        <nav className="space-y-1" aria-label="StoryOS Console">
          <button type="button" onClick={() => onSelectTab('production_monitor')} className={navClass(currentTab === 'production_monitor')}>
            <Activity className="w-3.5 h-3.5 text-[var(--info)]" />
            <span>生产监控</span>
            <span className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--success)]" title="MySQL Authority" />
          </button>
          <button type="button" onClick={() => onSelectTab('episodes')} className={navClass(currentTab === 'episodes')}>
            <Film className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <span>Episode Index</span>
          </button>
          <button type="button" onClick={() => onSelectTab('logs')} className={navClass(currentTab === 'logs')}>
            <FolderOpen className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <span>Runtime Logs</span>
          </button>
          <div className="pt-2 mt-2 border-t border-[var(--border-subtle)]">
            <button type="button" onClick={() => onSelectTab('workbench')} className={navClass(isWorkbench)}>
              <ShieldCheck className="w-3.5 h-3.5 text-[var(--warning)]" />
              <span>Workbench Demo</span>
            </button>
          </div>
        </nav>

        {isWorkbench && (
          <section>
            <div className="px-2 mb-1 flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-[var(--warning)]">
              <span>Local Demo Episodes</span>
              <span>{allEpisodes.length}</span>
            </div>
            <div className="space-y-0.5">
              {allEpisodes.map((episode) => {
                const active = episode.id === activeEpisode.id;
                return (
                  <button
                    key={episode.id}
                    type="button"
                    onClick={() => onSelectEpisode(episode)}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-[var(--radius-sm)] text-left text-xs ${active ? 'bg-[var(--bg-selected)] text-[var(--text-primary)]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'}`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${active ? 'bg-[var(--warning)]' : 'bg-[var(--text-disabled)]'}`} />
                    <span className="truncate">{episode.code} · {episode.title}</span>
                  </button>
                );
              })}
            </div>
            <button type="button" onClick={onNewConversation} className="storyos-control mt-2 w-full h-8 px-2 flex items-center justify-center gap-1.5 text-[11px] font-mono">
              <SquarePen className="w-3.5 h-3.5" />
              NEW LOCAL DEMO
            </button>
          </section>
        )}
      </div>

      <div className="h-[var(--header-height)] px-3 border-t border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-sidebar)]">
        <div>
          <div className="text-xs font-medium text-[var(--text-primary)]">StoryOS 运维</div>
          <div className="text-[10px] text-[var(--text-tertiary)] font-mono">{isWorkbench ? 'WORKBENCH DEMO' : 'PRODUCTION READ ONLY'}</div>
        </div>
        <div className="flex items-center gap-1">
          <a href="/platform" aria-label="打开 Platform Console" className="p-1.5 rounded-[4px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]" title="Platform Console">
            <LayoutDashboard className="w-4 h-4" />
          </a>
          <button type="button" onClick={() => onSelectTab('settings')} aria-label="打开设置" className={`p-1.5 rounded-[4px] ${currentTab === 'settings' ? 'text-[var(--text-primary)] bg-[var(--bg-selected)]' : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
