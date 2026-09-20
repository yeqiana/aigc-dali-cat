import React, { useState } from 'react';
import {
  ChevronDown,
  Search,
  Bell,
  SquarePen,
  ShieldCheck,
  ChevronRight,
  Settings,
  Film,
  FolderOpen,
  LayoutDashboard,
  Activity,
  Layers
} from 'lucide-react';
import { Episode, NavigationTab } from '../types';

interface SidebarProps {
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  activeEpisode: Episode;
  allEpisodes: Episode[];
  onSelectEpisode: (episode: Episode) => void;
  onNewConversation?: () => void;
  onOpenSearch?: () => void;
  onOpenNotifications?: () => void;
  unreadCount?: number;
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
  const [pinnedOpen, setPinnedOpen] = useState(true);
  const [seriesOpen, setSeriesOpen] = useState(true);

  // Group episodes into pinned and series
  const pinnedEpisodes = allEpisodes.slice(0, 3);
  const seriesEpisodes = allEpisodes.slice(3);

  return (
    <aside className="w-[224px] shrink-0 bg-[#0B0D10] border-r border-[#232830] flex flex-col h-full select-none text-[13px] font-sans antialiased text-[#A7AFBA]">
      {/* 1. 顶部 Header (StoryOS PRO 与 交互搜索/通知) */}
      <div className="h-[48px] px-3 flex items-center justify-between border-b border-[#232830]">
        <div className="flex items-center gap-2 font-semibold text-[#F1F3F5]">
          <span className="tracking-wider text-[#F1F3F5] font-mono text-sm font-bold">StoryOS</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded-[3px] bg-[#171B21] text-[#A7AFBA] border border-[#2D333D] font-mono font-medium tracking-tight">
            OPS
          </span>
        </div>
        <div className="flex items-center gap-1 text-[#737D8A]">
          <button
            type="button"
            onClick={onOpenSearch}
            className="p-1 hover:text-[#F1F3F5] hover:bg-[#171B21] rounded-[4px] transition-colors cursor-pointer"
            title="搜索剧集、分镜或台词 (Ctrl+K)"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={onOpenNotifications}
            className="p-1 hover:text-[#F1F3F5] hover:bg-[#171B21] rounded-[4px] transition-colors relative cursor-pointer"
            title="查看出图与质检通知"
          >
            <Bell className="w-3.5 h-3.5" />
            <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-[#58A6FF]" />
          </button>
        </div>
      </div>

      {/* 2. 核心功能菜单 */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4 scrollbar-none">
        {/* 顶部主工作操作项 */}
        <div className="space-y-1">
          <button
            type="button"
            onClick={() => {
              onSelectTab('workbench');
              if (onNewConversation) onNewConversation();
            }}
            className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] bg-[#171B21] border border-[#2D333D] text-[#F1F3F5] font-medium hover:bg-[#20262E] transition-colors text-xs cursor-pointer"
          >
            <SquarePen className="w-3.5 h-3.5 text-[#58A6FF]" />
            <span>新建故事剧本会话</span>
          </button>

          {/* 生产监控台：作为多任务总控主页 */}
          <button
            type="button"
            onClick={() => onSelectTab('production_monitor')}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'production_monitor'
                ? 'bg-[#171B21] text-[#F1F3F5] border border-[#2D333D] font-semibold'
                : 'text-[#A7AFBA] hover:text-[#F1F3F5] hover:bg-[#13161B]'
            }`}
          >
            <div className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-[#58A6FF]" />
              <span>生产监控 (主控台)</span>
            </div>
            <span className="w-1.5 h-1.5 rounded-full bg-[#58A6FF]" />
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('workbench')}
            className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'workbench'
                ? 'bg-[#171B21] text-[#F1F3F5] border border-[#2D333D] font-medium'
                : 'text-[#A7AFBA] hover:text-[#F1F3F5] hover:bg-[#13161B]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-[#737D8A]" />
            <span>分镜质检与调度台</span>
          </button>

          <button
            type="button"
            onClick={() => onSelectTab('episodes')}
            className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'episodes'
                ? 'bg-[#171B21] text-[#F1F3F5] border border-[#2D333D] font-medium'
                : 'text-[#A7AFBA] hover:text-[#F1F3F5] hover:bg-[#13161B]'
            }`}
          >
            <Film className="w-3.5 h-3.5 text-[#737D8A]" />
            <span>剧集资产全景总览</span>
          </button>
        </div>

        {/* 置顶剧目：真实可点击切换 */}
        <div>
          <button
            type="button"
            onClick={() => setPinnedOpen(!pinnedOpen)}
            className="w-full flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-[#737D8A] hover:text-[#F1F3F5] px-2 mb-1 cursor-pointer"
          >
            <span className="flex items-center gap-1">
              <ChevronRight className={`w-3 h-3 transition-transform ${pinnedOpen ? 'rotate-90' : ''}`} />
              <span>当前置顶剧目</span>
            </span>
            <span className="text-[10px] text-[#737D8A]">{pinnedEpisodes.length}</span>
          </button>

          {pinnedOpen && (
            <div className="space-y-0.5">
              {pinnedEpisodes.map((ep) => {
                const isActive = ep.id === activeEpisode.id && currentTab === 'workbench';
                return (
                  <button
                    key={ep.id}
                    type="button"
                    onClick={() => {
                      onSelectEpisode(ep);
                      onSelectTab('workbench');
                    }}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-[4px] transition-all text-left text-xs cursor-pointer ${
                      isActive
                        ? 'bg-[#171B21] text-[#F1F3F5] border border-[#2D333D] font-medium'
                        : 'text-[#A7AFBA] hover:text-[#F1F3F5] hover:bg-[#13161B]'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      isActive ? 'bg-[#58A6FF]' : 'bg-[#505864]'
                    }`} />
                    <span className="truncate">{ep.title}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* 剧目系列库：真实可点击切换 */}
        <div>
          <button
            type="button"
            onClick={() => setSeriesOpen(!seriesOpen)}
            className="w-full flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-[#737D8A] hover:text-[#F1F3F5] px-2 mb-1 cursor-pointer"
          >
            <span className="flex items-center gap-1">
              <ChevronRight className={`w-3 h-3 transition-transform ${seriesOpen ? 'rotate-90' : ''}`} />
              <span>更多系列作品</span>
            </span>
            <span className="text-[10px] text-[#737D8A]">{seriesEpisodes.length}</span>
          </button>

          {seriesOpen && (
            <div className="space-y-0.5">
              {seriesEpisodes.map((ep) => {
                const isActive = ep.id === activeEpisode.id && currentTab === 'workbench';
                return (
                  <button
                    key={ep.id}
                    type="button"
                    onClick={() => {
                      onSelectEpisode(ep);
                      onSelectTab('workbench');
                    }}
                    className={`w-full flex items-center gap-2 px-2 py-1 rounded-[4px] transition-colors text-left text-xs cursor-pointer ${
                      isActive
                        ? 'bg-[#171B21] text-[#F1F3F5] border border-[#2D333D] font-medium'
                        : 'text-[#A7AFBA] hover:text-[#F1F3F5] hover:bg-[#13161B]'
                    }`}
                  >
                    <FolderOpen className="w-3 h-3 text-[#505864] shrink-0" />
                    <span className="truncate">{ep.title}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 3. 底部用户信息与系统设置 */}
      <div className="h-[48px] px-3 border-t border-[#232830] flex items-center justify-between bg-[#0F1115]">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-[4px] bg-[#171B21] border border-[#2D333D] text-[#58A6FF] flex items-center justify-center text-xs font-bold font-mono">
            S
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-medium text-[#F1F3F5] leading-tight">StoryOS 运维</span>
            <span className="text-[10px] text-[#737D8A] font-mono leading-tight">4:5 1080×1350 标定</span>
          </div>
        </div>
        <button
          type="button"
          onClick={() => onSelectTab('settings')}
          className={`p-1.5 rounded-[4px] transition-colors cursor-pointer ${
            currentTab === 'settings'
              ? 'text-[#F1F3F5] bg-[#171B21] border border-[#2D333D]'
              : 'text-[#737D8A] hover:text-[#F1F3F5] hover:bg-[#171B21]'
          }`}
          title="外观与系统设置"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
