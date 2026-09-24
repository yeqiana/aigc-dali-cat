import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  Search,
  Bell,
  SquarePen,
  ShieldCheck,
  Settings,
  Film,
  Folder,
  Activity,
  GitBranch,
  Plus,
  MoreHorizontal,
  Edit3,
  Trash2,
  FileCode2,
  Pin,
  PinOff,
  FolderSync,
  Archive,
  X,
  Check,
  Share2,
  PanelRight,
  Sun,
  Moon,
  Sparkles,
  ChevronUp,
  ChevronRight,
  Clock,
  Clapperboard,
  FolderPlus,
  ArrowRight
} from 'lucide-react';
import { Episode, NavigationTab, ProjectItem } from '../types';

interface SidebarProps {
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  activeEpisode: Episode;
  allEpisodes: Episode[];
  onSelectEpisode: (episode: Episode) => void;
  projects: ProjectItem[];
  onCreateProject: (name: string) => void;
  onRenameProject: (projectId: string, newName: string) => void;
  onDeleteProject: (projectId: string) => void;
  // 新建故事归属体系
  onCreateStoryInProject?: (projectId: string, title?: string) => void;
  onCreateStoryFromHome?: (title?: string) => void;
  recentStoryIds?: string[];
  onRemoveRecentStory?: (storyId: string) => void;
  onAssignStoryToProject?: (storyId: string, projectId: string) => void;
  onNewConversation?: () => void;
  onOpenSearch?: () => void;
  onOpenNotifications?: () => void;
  unreadCount?: number;
  onToggleContextPanel?: () => void;
  contextPanelOpen?: boolean;
  currentTheme?: 'dark' | 'light' | 'light-gradient';
  onThemeChange?: (theme: 'dark' | 'light' | 'light-gradient') => void;
  onShowToast?: (msg: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  activeEpisode,
  allEpisodes,
  onSelectEpisode,
  projects,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
  onCreateStoryInProject,
  onCreateStoryFromHome,
  recentStoryIds = [],
  onRemoveRecentStory,
  onAssignStoryToProject,
  onNewConversation,
  onOpenSearch,
  onOpenNotifications,
  unreadCount = 0,
  onToggleContextPanel,
  contextPanelOpen = true,
  currentTheme = 'dark',
  onThemeChange,
  onShowToast,
}) => {
  // 当前选中的项目 ID
  const [activeProjectId, setActiveProjectId] = useState<string>(projects[0]?.id || 'proj-storyos');

  // 项目展开状态集合 (支持展开查看项目下的故事)
  const [expandedProjectIds, setExpandedProjectIds] = useState<string[]>(['proj-storyos', 'proj-urban']);

  // 置顶的项目 ID 集合
  const [pinnedProjectIds, setPinnedProjectIds] = useState<string[]>(['proj-storyos']);

  // 最近故事区域折叠状态 (默认展开)
  const [recentStoriesExpanded, setRecentStoriesExpanded] = useState(true);

  // 用户头像弹出菜单状态
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [copiedShare, setCopiedShare] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // 项目右键/操作菜单状态
  const [contextMenu, setContextMenu] = useState<{
    visible: boolean;
    x: number;
    y: number;
    project: ProjectItem | null;
  }>({
    visible: false,
    x: 0,
    y: 0,
    project: null,
  });

  // 弹窗状态：新建项目
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');

  // 弹窗状态：重命名项目
  const [renamingProject, setRenamingProject] = useState<ProjectItem | null>(null);
  const [renameValue, setRenameValue] = useState('');

  // 弹窗状态：新建故事模态框 (包含在项目内新建 vs 从主页自建)
  const [storyModal, setStoryModal] = useState<{
    isOpen: boolean;
    targetProjectId?: string; // 若有则是归入该项目；若无则是从主页自建归入“最近故事”
    targetProjectName?: string;
  }>({
    isOpen: false,
  });
  const [newStoryTitle, setNewStoryTitle] = useState('');

  const menuRef = useRef<HTMLDivElement>(null);

  // 计算“最近故事”列表：
  // 包含显式记录在 recentStoryIds 中的故事，以及没有属于任何具体项目的自由故事（从主页自建的故事）
  const recentStories = useMemo(() => {
    // 找出所有在 recentStoryIds 中的故事
    const matched = recentStoryIds
      .map(id => allEpisodes.find(ep => ep.id === id))
      .filter((ep): ep is Episode => Boolean(ep));

    // 找出所有没有分配给任何项目的孤立/主页自建故事
    const projectAssignedEpIds = new Set<string>();
    projects.forEach(p => p.episodeIds.forEach(id => projectAssignedEpIds.add(id)));

    const homeStories = allEpisodes.filter(ep => !projectAssignedEpIds.has(ep.id));

    // 合并并去重，以 recentStoryIds 的顺序为优先
    const combined: Episode[] = [...matched];
    homeStories.forEach(ep => {
      if (!combined.some(item => item.id === ep.id)) {
        combined.push(ep);
      }
    });

    return combined;
  }, [recentStoryIds, allEpisodes, projects]);

  // 点击外部关闭右键菜单与用户菜单
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setContextMenu({ visible: false, x: 0, y: 0, project: null });
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    if (contextMenu.visible || userMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [contextMenu.visible, userMenuOpen]);

  const handleOpenContextMenu = (e: React.MouseEvent, project: ProjectItem) => {
    e.preventDefault();
    e.stopPropagation();
    const x = Math.min(e.clientX, window.innerWidth - 200);
    const y = Math.min(e.clientY, window.innerHeight - 240);
    setContextMenu({
      visible: true,
      x,
      y,
      project,
    });
  };

  const handleTogglePin = (projectId: string) => {
    setPinnedProjectIds((prev) =>
      prev.includes(projectId)
        ? prev.filter(id => id !== projectId)
        : [...prev, projectId]
    );
    setContextMenu({ visible: false, x: 0, y: 0, project: null });
  };

  const handleToggleProjectExpand = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    setExpandedProjectIds(prev =>
      prev.includes(projectId)
        ? prev.filter(id => id !== projectId)
        : [...prev, projectId]
    );
  };

  const handleConfirmCreateProject = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    onCreateProject(newProjectName.trim());
    setNewProjectName('');
    setIsCreatingProject(false);
  };

  const handleConfirmRename = (e: React.FormEvent) => {
    e.preventDefault();
    if (!renamingProject || !renameValue.trim()) return;
    onRenameProject(renamingProject.id, renameValue.trim());
    setRenamingProject(null);
    setRenameValue('');
  };

  const handleSelectProject = (proj: ProjectItem) => {
    setActiveProjectId(proj.id);
    // 如果该项目有关联作品，切换到该作品并进入工作台
    const matchedEp = allEpisodes.find(ep => proj.episodeIds.includes(ep.id));
    if (matchedEp) {
      onSelectEpisode(matchedEp);
    }
  };

  // 打开在特定项目中新建故事的模态窗
  const handleOpenCreateStoryInProject = (e: React.MouseEvent, project: ProjectItem) => {
    e.stopPropagation();
    setStoryModal({
      isOpen: true,
      targetProjectId: project.id,
      targetProjectName: project.name,
    });
    setNewStoryTitle('');
  };

  // 打开从主页自己新建故事的模态窗（归入最近故事）
  const handleOpenCreateStoryFromHome = () => {
    setStoryModal({
      isOpen: true,
      targetProjectId: undefined,
      targetProjectName: undefined,
    });
    setNewStoryTitle('');
  };

  // 确认创建故事提交
  const handleConfirmCreateStory = (e: React.FormEvent) => {
    e.preventDefault();
    const title = newStoryTitle.trim() || undefined;

    if (storyModal.targetProjectId) {
      // 在项目上新建 -> 自动归入该项目
      if (onCreateStoryInProject) {
        onCreateStoryInProject(storyModal.targetProjectId, title);
      }
    } else {
      // 从主页自己建的故事 -> 自动归入项目同级的“最近故事”中
      if (onCreateStoryFromHome) {
        onCreateStoryFromHome(title);
      } else if (onNewConversation) {
        onNewConversation();
      }
    }

    setStoryModal({ isOpen: false });
    setNewStoryTitle('');
  };

  return (
    <aside className="w-[230px] shrink-0 bg-[var(--bg-app)] border-r border-[var(--border-subtle)] flex flex-col h-full select-none text-[13px] font-sans antialiased text-[var(--text-secondary)] relative">
      {/* 1. 顶部 Header */}
      <div className="h-[48px] px-3 flex items-center justify-between border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2 font-semibold text-[var(--text-primary)]">
          <span className="tracking-wider text-[var(--text-primary)] font-mono text-sm font-bold">StoryOS</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded-[3px] bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-subtle)] font-mono font-medium tracking-tight">
            OPS
          </span>
        </div>
        <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
          <button
            type="button"
            onClick={onOpenSearch}
            className="p-1 hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded-[4px] transition-colors cursor-pointer"
            title="搜索 (Ctrl+K)"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={onOpenNotifications}
            className="p-1 hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] rounded-[4px] transition-colors relative cursor-pointer"
            title="通知"
          >
            <Bell className="w-3.5 h-3.5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-[#58A6FF]" />
            )}
          </button>
        </div>
      </div>

      {/* 2. 主体滚动区 */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-4 scrollbar-thin scrollbar-thumb-[var(--border-normal)]">
        {/* 顶部主工作导航 */}
        <div className="space-y-0.5">
          {/* 从主页新建故事会话按钮（自动归入最近故事） */}
          <button
            type="button"
            onClick={handleOpenCreateStoryFromHome}
            className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-[5px] bg-[var(--bg-elevated)] border border-[var(--border-normal)] text-[var(--text-primary)] font-medium hover:bg-[var(--bg-hover)] transition-colors text-xs cursor-pointer mb-2 shadow-xs group"
            title="从主页自建故事，自动归入项目同级的「最近故事」"
          >
            <div className="flex items-center gap-2">
              <SquarePen className="w-3.5 h-3.5 text-[#58A6FF]" />
              <span className="font-medium">新建故事会话</span>
            </div>
            <span className="text-[10px] font-mono text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)]">
              主页自建
            </span>
          </button>

          {/* 生产监控台 */}
          <button
            type="button"
            onClick={() => onSelectTab('production_monitor')}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'production_monitor'
                ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] border border-[var(--border-normal)] font-medium'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
            }`}
          >
            <div className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-[#58A6FF]" />
              <span>生产监控</span>
            </div>
          </button>

          {/* 主要流程 */}
          <button
            type="button"
            onClick={() => onSelectTab('pipeline')}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'pipeline'
                ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] border border-[var(--border-normal)] font-medium'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
            }`}
          >
            <div className="flex items-center gap-2">
              <GitBranch className="w-3.5 h-3.5 text-emerald-400" />
              <span>主要流程</span>
            </div>
            <span className="text-[10px] px-1 rounded bg-emerald-500/15 text-emerald-400 font-mono">
              7阶段
            </span>
          </button>

          {/* 分镜与质检工作台 */}
          <button
            type="button"
            onClick={() => onSelectTab('workbench')}
            className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'workbench'
                ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] border border-[var(--border-normal)] font-medium'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <span>分镜与质检</span>
          </button>

          {/* 剧集作品资产 */}
          <button
            type="button"
            onClick={() => onSelectTab('episodes')}
            className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'episodes'
                ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] border border-[var(--border-normal)] font-medium'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
            }`}
          >
            <Film className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <span>作品资产</span>
          </button>

          {/* 审计日志 */}
          <button
            type="button"
            onClick={() => onSelectTab('logs')}
            className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-[5px] transition-colors text-xs cursor-pointer ${
              currentTab === 'logs'
                ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] border border-[var(--border-normal)] font-medium'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
            }`}
          >
            <FileCode2 className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
            <span>审计日志</span>
          </button>
        </div>

        {/* 3. 项目列表 (Project Items) */}
        <div className="pt-2 border-t border-[var(--border-subtle)]">
          <div className="flex items-center justify-between px-2 mb-1.5">
            <span className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)] font-semibold flex items-center gap-1.5">
              <span>项目</span>
              <span className="text-[10px] font-mono text-[var(--text-tertiary)] font-normal">
                ({projects.length})
              </span>
            </span>
            <button
              type="button"
              onClick={() => setIsCreatingProject(true)}
              className="p-1 rounded-[3px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
              title="新建项目"
            >
              <Plus className="w-3.5 h-3.5 text-[#58A6FF]" />
            </button>
          </div>

          <div className="space-y-1">
            {projects.map((proj) => {
              const isSelected = proj.id === activeProjectId;
              const isPinned = pinnedProjectIds.includes(proj.id);
              const isExpanded = expandedProjectIds.includes(proj.id);
              // 该项目下的故事列表
              const projectStories = allEpisodes.filter(ep => proj.episodeIds.includes(ep.id));

              return (
                <div key={proj.id} className="space-y-0.5">
                  <div
                    onContextMenu={(e) => handleOpenContextMenu(e, proj)}
                    onClick={() => handleSelectProject(proj)}
                    className={`group relative flex items-center justify-between px-2 py-1.5 rounded-[6px] transition-all cursor-pointer text-xs ${
                      isSelected
                        ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] font-medium border border-[var(--border-normal)] shadow-xs'
                        : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                    }`}
                    title={`项目: ${proj.name} (含 ${projectStories.length} 部故事)`}
                  >
                    {/* 左侧：折叠箭头 + 文件夹图标 + 项目名称 */}
                    <div className="flex items-center gap-1.5 min-w-0 pr-1">
                      {projectStories.length > 0 ? (
                        <button
                          type="button"
                          onClick={(e) => handleToggleProjectExpand(e, proj.id)}
                          className="p-0.5 rounded hover:bg-[var(--bg-hover)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-transform"
                          title={isExpanded ? '收起故事' : '展开故事'}
                        >
                          <ChevronRight className={`w-3 h-3 transition-transform ${isExpanded ? 'rotate-90 text-[var(--text-primary)]' : ''}`} />
                        </button>
                      ) : (
                        <span className="w-4" />
                      )}

                      <Folder className={`w-3.5 h-3.5 shrink-0 ${
                        isSelected ? 'text-[#58A6FF]' : 'text-[var(--text-tertiary)]'
                      }`} />
                      <span className="truncate text-[12px] tracking-tight">
                        {proj.name}
                      </span>
                    </div>

                    {/* 右侧：故事数量徽标 + 悬停操作 (在项目中新建故事 + 更多) */}
                    <div className="flex items-center gap-1 shrink-0">
                      {/* 数量标牌 (常态展示) */}
                      <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded ${
                        projectStories.length > 0
                          ? 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'
                          : 'text-[var(--text-tertiary)]'
                      } ${isSelected ? 'group-hover:hidden' : 'group-hover:hidden'}`}>
                        {projectStories.length}
                      </span>

                      {isPinned && !isSelected && (
                        <Pin className="w-2.5 h-2.5 text-[var(--text-tertiary)] group-hover:hidden" />
                      )}

                      {/* 悬停操作按钮组 */}
                      <div className="items-center gap-0.5 hidden group-hover:flex">
                        {/* 核心需求：在项目上新建故事，点击后自动归入该项目 */}
                        <button
                          type="button"
                          onClick={(e) => handleOpenCreateStoryInProject(e, proj)}
                          className="p-1 rounded-[3px] text-[#58A6FF] hover:bg-[var(--bg-surface)] transition-colors cursor-pointer"
                          title={`在此项目「${proj.name}」中新建故事（自动归入改项目）`}
                        >
                          <Plus className="w-3 h-3" />
                        </button>

                        {/* 更多菜单按钮 (···) */}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenContextMenu(e, proj);
                          }}
                          className="p-1 rounded-[3px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-colors cursor-pointer"
                          title="项目操作"
                        >
                          <MoreHorizontal className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* 展开该项目下的故事列表 */}
                  {isExpanded && projectStories.length > 0 && (
                    <div className="pl-6 pr-1 space-y-0.5 border-l border-[var(--border-subtle)] ml-3 my-0.5">
                      {projectStories.map(story => {
                        const isStoryActive = story.id === activeEpisode.id;
                        return (
                          <div
                            key={story.id}
                            onClick={() => {
                              onSelectEpisode(story);
                              onSelectTab('workbench');
                            }}
                            className={`flex items-center justify-between px-2 py-1 rounded-[4px] text-[11.5px] cursor-pointer transition-colors group/story ${
                              isStoryActive
                                ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-medium border border-[var(--border-normal)]'
                                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                            }`}
                            title={`《${story.title}》- 属于项目: ${proj.name}`}
                          >
                            <div className="flex items-center gap-1.5 min-w-0 pr-1">
                              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                isStoryActive ? 'bg-[#58A6FF]' : 'bg-[var(--border-normal)] group-hover/story:bg-[var(--text-tertiary)]'
                              }`} />
                              <span className="truncate">{story.title}</span>
                            </div>
                            <span className="text-[10px] font-mono text-[var(--text-tertiary)] shrink-0">
                              {story.code}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* 4. 项目同级的“最近故事” (Recent Stories) - 核心用户需求 */}
        <div className="pt-2 border-t border-[var(--border-subtle)]">
          <div className="flex items-center justify-between px-2 mb-1.5">
            <button
              type="button"
              onClick={() => setRecentStoriesExpanded(!recentStoriesExpanded)}
              className="flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)] font-semibold hover:text-[var(--text-primary)] transition-colors cursor-pointer text-left"
              title={recentStoriesExpanded ? '收起最近故事' : '展开最近故事'}
            >
              <ChevronRight className={`w-3 h-3 transition-transform ${recentStoriesExpanded ? 'rotate-90 text-[var(--text-primary)]' : ''}`} />
              <span>最近故事</span>
              <span className="text-[10px] font-mono text-[var(--text-tertiary)] font-normal">
                ({recentStories.length})
              </span>
            </button>

            {/* 从主页新建故事（自动归入最近故事） */}
            <button
              type="button"
              onClick={handleOpenCreateStoryFromHome}
              className="p-1 rounded-[3px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
              title="从主页自建故事（自动归入最近故事）"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
            </button>
          </div>

          {recentStoriesExpanded && (
            <div className="space-y-0.5">
              {recentStories.length === 0 ? (
                <div className="px-3 py-2 text-[11px] text-[var(--text-tertiary)] font-mono">
                  暂无自建故事，点击 + 快速从主页自建
                </div>
              ) : (
                recentStories.map((story) => {
                  const isStoryActive = story.id === activeEpisode.id;
                  // 是否属于某个项目
                  const assignedProj = projects.find(p => p.episodeIds.includes(story.id));

                  return (
                    <div
                      key={story.id}
                      onClick={() => {
                        onSelectEpisode(story);
                        onSelectTab('workbench');
                      }}
                      className={`group/recent flex items-center justify-between px-2 py-1.5 rounded-[5px] transition-all cursor-pointer text-xs ${
                        isStoryActive
                          ? 'bg-[var(--bg-elevated)] text-[var(--text-primary)] font-medium border border-[var(--border-normal)] shadow-xs'
                          : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                      }`}
                      title={`《${story.title}》· 代号 ${story.code}${assignedProj ? ` (归属于项目: ${assignedProj.name})` : ' (主页自建·最近故事)'}`}
                    >
                      <div className="flex items-center gap-2 min-w-0 pr-1">
                        <Clapperboard className={`w-3.5 h-3.5 shrink-0 ${
                          isStoryActive ? 'text-[#58A6FF]' : 'text-[var(--text-tertiary)]'
                        }`} />
                        <div className="min-w-0 flex flex-col">
                          <span className="truncate text-[12px] leading-tight font-medium">
                            {story.title}
                          </span>
                          <span className="text-[10px] text-[var(--text-tertiary)] font-mono leading-none mt-0.5">
                            {assignedProj ? assignedProj.name : '主页自建'}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1 shrink-0">
                        <span className="text-[10px] font-mono text-[var(--text-tertiary)] group-hover/recent:hidden">
                          {story.code}
                        </span>

                        {/* 悬停操作：如果需要移出最近列表 */}
                        {onRemoveRecentStory && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onRemoveRecentStory(story.id);
                              onShowToast?.(`已将《${story.title}》从最近故事中移出`);
                            }}
                            className="hidden group-hover/recent:flex p-1 rounded hover:bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"
                            title="从最近故事移除"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>

      {/* 5. 底部账户与全局控制 (点击头像弹出配置、分享、面板与主题切换) */}
      <div className="relative border-t border-[var(--border-subtle)] bg-[var(--bg-workspace)]">
        {/* 点击头像展开的悬浮菜单 */}
        {userMenuOpen && (
          <div
            ref={userMenuRef}
            className="absolute bottom-full left-2 right-2 mb-2 rounded-[8px] bg-[var(--bg-elevated)] border border-[var(--border-normal)] p-2 shadow-2xl z-50 text-xs font-sans animate-in fade-in zoom-in-95 duration-100 space-y-2 text-[var(--text-primary)]"
          >
            {/* 用户身份简报 */}
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-[4px] bg-[var(--bg-hover)] border border-[var(--border-normal)] text-[#58A6FF] flex items-center justify-center font-bold font-mono text-xs">
                  S
                </div>
                <div>
                  <div className="font-semibold text-xs leading-tight text-[var(--text-primary)]">StoryOS 运维</div>
                  <div className="text-[10px] text-[var(--text-tertiary)] font-mono">标定环境 4:5</div>
                </div>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">
                在线
              </span>
            </div>

            {/* 核心操作按钮组 */}
            <div className="space-y-1">
              {/* 配置 */}
              <button
                type="button"
                onClick={() => {
                  onSelectTab('settings');
                  setUserMenuOpen(false);
                }}
                className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-[4px] text-left transition-colors cursor-pointer ${
                  currentTab === 'settings'
                    ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-semibold border border-[var(--border-normal)]'
                    : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Settings className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                  <span>系统设置与配置</span>
                </div>
                <span className="text-[10px] font-mono text-[var(--text-tertiary)]">偏好设置</span>
              </button>

              {/* 分享 */}
              <button
                type="button"
                onClick={() => {
                  const url = window.location.href;
                  navigator.clipboard.writeText(url).then(() => {
                    setCopiedShare(true);
                    onShowToast?.('已复制工作台分享链接');
                    setTimeout(() => setCopiedShare(false), 2000);
                  }).catch(() => {
                    setCopiedShare(true);
                    onShowToast?.('已获取分享链接');
                    setTimeout(() => setCopiedShare(false), 2000);
                  });
                }}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-[4px] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-left transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-2">
                  {copiedShare ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Share2 className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                  )}
                  <span>{copiedShare ? '链接已复制' : '分享剧目链接'}</span>
                </div>
                <span className="text-[10px] font-mono text-[var(--text-tertiary)]">URL</span>
              </button>

              {/* 面板开关 */}
              {onToggleContextPanel && (
                <button
                  type="button"
                  onClick={() => {
                    onToggleContextPanel();
                  }}
                  className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-[4px] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-left transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <PanelRight className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
                    <span>右侧上下文面板</span>
                  </div>
                  <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                    contextPanelOpen
                      ? 'bg-blue-500/15 text-blue-400 border-blue-500/20'
                      : 'bg-[var(--bg-hover)] text-[var(--text-tertiary)] border-[var(--border-subtle)]'
                  }`}>
                    {contextPanelOpen ? '已展开' : '已收起'}
                  </span>
                </button>
              )}
            </div>

            {/* 主题快速切换 */}
            {onThemeChange && (
              <div className="pt-2 border-t border-[var(--border-subtle)]">
                <div className="text-[10px] font-mono text-[var(--text-tertiary)] px-1 mb-1.5 flex items-center justify-between">
                  <span>主题外观</span>
                  <span className="capitalize">{currentTheme}</span>
                </div>
                <div className="grid grid-cols-3 gap-1">
                  <button
                    type="button"
                    onClick={() => onThemeChange('dark')}
                    className={`flex items-center justify-center gap-1 py-1 rounded-[4px] text-[11px] font-mono transition-colors cursor-pointer border ${
                      currentTheme === 'dark'
                        ? 'bg-[var(--bg-selected)] border-[#58A6FF] text-[var(--text-primary)] font-bold'
                        : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                    }`}
                    title="深色模式"
                  >
                    <Moon className="w-3 h-3 text-indigo-400" />
                    <span>深色</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onThemeChange('light')}
                    className={`flex items-center justify-center gap-1 py-1 rounded-[4px] text-[11px] font-mono transition-colors cursor-pointer border ${
                      currentTheme === 'light'
                        ? 'bg-[var(--bg-selected)] border-[#58A6FF] text-[var(--text-primary)] font-bold'
                        : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                    }`}
                    title="浅色中性模式"
                  >
                    <Sun className="w-3 h-3 text-amber-500" />
                    <span>浅色</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => onThemeChange('light-gradient')}
                    className={`flex items-center justify-center gap-1 py-1 rounded-[4px] text-[11px] font-mono transition-colors cursor-pointer border ${
                      currentTheme === 'light-gradient'
                        ? 'bg-[var(--bg-selected)] border-[#58A6FF] text-[var(--text-primary)] font-bold'
                        : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                    }`}
                    title="浅色渐变模式"
                  >
                    <Sparkles className="w-3 h-3 text-blue-500" />
                    <span>渐变</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 触发条：点击头像/卡片弹出 */}
        <button
          type="button"
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className={`w-full h-[48px] px-3 flex items-center justify-between text-left transition-colors cursor-pointer ${
            userMenuOpen ? 'bg-[var(--bg-hover)]' : 'hover:bg-[var(--bg-hover)]'
          }`}
          title="点击展示设置、分享与面板控制"
        >
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-[4px] bg-[var(--bg-elevated)] border border-[var(--border-normal)] text-[#58A6FF] flex items-center justify-center text-xs font-bold font-mono">
              S
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-medium text-[var(--text-primary)] leading-tight">StoryOS 运维</span>
              <span className="text-[10px] text-[var(--text-tertiary)] font-mono leading-tight">4:5 标定环境</span>
            </div>
          </div>
          <div className="flex items-center gap-1 text-[var(--text-tertiary)]">
            <ChevronUp className={`w-3.5 h-3.5 transition-transform ${userMenuOpen ? 'rotate-180 text-[var(--text-primary)]' : ''}`} />
          </div>
        </button>
      </div>

      {/* 6. 项目操作弹出菜单 */}
      {contextMenu.visible && contextMenu.project && (
        <div
          ref={menuRef}
          style={{ top: contextMenu.y, left: contextMenu.x }}
          className="fixed z-50 w-48 rounded-[8px] theme-popover-menu py-1 text-xs font-sans animate-in fade-in zoom-in-95 duration-75 shadow-2xl"
        >
          {/* 在当前项目新建故事 */}
          <button
            type="button"
            onClick={(e) => {
              if (contextMenu.project) {
                handleOpenCreateStoryInProject(e, contextMenu.project);
              }
              setContextMenu({ visible: false, x: 0, y: 0, project: null });
            }}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[var(--bg-hover)] text-left transition-colors cursor-pointer text-[#58A6FF] font-medium"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>在项目中新建故事</span>
          </button>

          <div className="my-1 border-t border-[var(--border-subtle)]" />

          {/* 取消置顶 / 置顶 */}
          <button
            type="button"
            onClick={() => contextMenu.project && handleTogglePin(contextMenu.project.id)}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[var(--bg-hover)] text-left transition-colors cursor-pointer"
          >
            {pinnedProjectIds.includes(contextMenu.project.id) ? (
              <>
                <PinOff className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
                <span>取消置顶</span>
              </>
            ) : (
              <>
                <Pin className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
                <span>置顶项目</span>
              </>
            )}
          </button>

          {/* 编辑 */}
          <button
            type="button"
            onClick={() => {
              setRenamingProject(contextMenu.project);
              setRenameValue(contextMenu.project?.name || '');
              setContextMenu({ visible: false, x: 0, y: 0, project: null });
            }}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[var(--bg-hover)] text-left transition-colors cursor-pointer"
          >
            <Edit3 className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
            <span>重命名项目</span>
          </button>

          <div className="my-1 border-t border-[var(--border-subtle)]" />

          {/* 归档项目 */}
          <button
            type="button"
            onClick={() => {
              if (contextMenu.project) {
                onRenameProject(contextMenu.project.id, `${contextMenu.project.name} (已归档)`);
              }
              setContextMenu({ visible: false, x: 0, y: 0, project: null });
            }}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-[var(--bg-hover)] text-left transition-colors cursor-pointer"
          >
            <Archive className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
            <span>归档项目</span>
          </button>

          {/* 移除项目 */}
          <button
            type="button"
            onClick={() => {
              if (contextMenu.project) {
                onDeleteProject(contextMenu.project.id);
              }
              setContextMenu({ visible: false, x: 0, y: 0, project: null });
            }}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 hover:bg-red-500/15 text-red-400 text-left transition-colors cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>移除项目</span>
          </button>
        </div>
      )}

      {/* 7. 新建故事弹窗 (支持在指定项目新建 vs 从主页自建) */}
      {storyModal.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-[8px] bg-[var(--bg-elevated)] border border-[var(--border-normal)] p-4 text-[var(--text-primary)] shadow-2xl animate-in fade-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)] mb-3">
              <div className="flex items-center gap-2">
                <Clapperboard className="w-4 h-4 text-[#58A6FF]" />
                <span className="font-semibold text-sm">
                  {storyModal.targetProjectName
                    ? `在项目《${storyModal.targetProjectName}》新建故事`
                    : '新建故事（主页自建）'
                  }
                </span>
              </div>
              <button
                type="button"
                onClick={() => setStoryModal({ isOpen: false })}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* 明确的归属规则提示 */}
            <div className="mb-3 p-2.5 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs font-mono">
              {storyModal.targetProjectName ? (
                <div className="text-[#58A6FF] flex items-center gap-1.5">
                  <Check className="w-3.5 h-3.5 shrink-0" />
                  <span>故事创建后将<strong>自动归入项目「{storyModal.targetProjectName}」</strong>中</span>
                </div>
              ) : (
                <div className="text-emerald-400 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 shrink-0" />
                  <span>故事从主页自建，将<strong>自动归入项目同级的「最近故事」</strong>中</span>
                </div>
              )}
            </div>

            <form onSubmit={handleConfirmCreateStory} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-[var(--text-secondary)] mb-1">
                  故事名称 / 剧目代号 (如《雨夜回响》或《镜中规则》)
                </label>
                <input
                  type="text"
                  autoFocus
                  value={newStoryTitle}
                  onChange={(e) => setNewStoryTitle(e.target.value)}
                  placeholder={storyModal.targetProjectName ? `输入属于 ${storyModal.targetProjectName} 的故事名称...` : "输入自建故事名称..."}
                  className="w-full px-2.5 py-1.5 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-normal)] text-[var(--text-primary)] text-xs focus:outline-hidden focus:border-[#58A6FF]"
                />
              </div>

              {/* 快速灵感词 */}
              <div>
                <div className="text-[10px] font-mono text-[var(--text-tertiary)] mb-1">快速选题灵感：</div>
                <div className="flex flex-wrap gap-1.5">
                  {['雨夜回响', '4:5 镜中倒影', '车库十三层', '迷雾当铺', '最后一次婚礼'].map(tag => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => setNewStoryTitle(`《${tag}》`)}
                      className="px-2 py-0.5 rounded-[3px] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer"
                    >
                      +{tag}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-[var(--border-subtle)]">
                <button
                  type="button"
                  onClick={() => setStoryModal({ isOpen: false })}
                  className="px-3 py-1 rounded-[4px] bg-[var(--bg-hover)] border border-[var(--border-normal)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-mono cursor-pointer"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] hover:opacity-90 text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>
                    {storyModal.targetProjectName ? '归入项目并创建' : '创建并加入最近故事'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 8. 新建项目弹窗 */}
      {isCreatingProject && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-[8px] bg-[var(--bg-elevated)] border border-[var(--border-normal)] p-4 text-[var(--text-primary)] shadow-2xl animate-in fade-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)] mb-3">
              <span className="font-semibold text-sm">新建项目</span>
              <button
                type="button"
                onClick={() => setIsCreatingProject(false)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleConfirmCreateProject} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-[var(--text-secondary)] mb-1">
                  项目名称 (如 story OS 或 aigc-dali-cat)
                </label>
                <input
                  type="text"
                  autoFocus
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="输入项目名称..."
                  className="w-full px-2.5 py-1.5 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-normal)] text-[var(--text-primary)] text-xs focus:outline-hidden focus:border-[#58A6FF]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCreatingProject(false)}
                  className="px-3 py-1 rounded-[4px] bg-[var(--bg-hover)] border border-[var(--border-normal)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-mono cursor-pointer"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={!newProjectName.trim()}
                  className="px-3 py-1 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] hover:opacity-90 disabled:opacity-50 text-xs font-semibold flex items-center gap-1 cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>创建项目</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 9. 修改项目名称弹窗 */}
      {renamingProject && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="w-full max-w-sm rounded-[8px] bg-[var(--bg-elevated)] border border-[var(--border-normal)] p-4 text-[var(--text-primary)] shadow-2xl animate-in fade-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)] mb-3">
              <span className="font-semibold text-sm">编辑项目</span>
              <button
                type="button"
                onClick={() => setRenamingProject(null)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleConfirmRename} className="space-y-3">
              <div>
                <label className="block text-[11px] font-mono text-[var(--text-secondary)] mb-1">
                  项目名称
                </label>
                <input
                  type="text"
                  autoFocus
                  value={renameValue}
                  onChange={(e) => setRenameValue(e.target.value)}
                  className="w-full px-2.5 py-1.5 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-normal)] text-[var(--text-primary)] text-xs focus:outline-hidden focus:border-[#58A6FF]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setRenamingProject(null)}
                  className="px-3 py-1 rounded-[4px] bg-[var(--bg-hover)] border border-[var(--border-normal)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs font-mono cursor-pointer"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={!renameValue.trim()}
                  className="px-3 py-1 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] hover:opacity-90 disabled:opacity-50 text-xs font-semibold flex items-center gap-1 cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>保存修改</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </aside>
  );
};
