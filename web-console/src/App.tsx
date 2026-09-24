import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { HeaderBar } from './components/HeaderBar';
import { StatusFlowBanner } from './components/StatusFlowBanner';
import { ProductionMetricsPanel } from './components/ProductionMetricsPanel';
import { ActivityStream } from './components/ActivityStream';
import { CommandDock } from './components/CommandDock';
import { ContextPanel } from './components/ContextPanel';

// Views
import { ProductionMonitorView } from './components/views/ProductionMonitorView';
import { ProductionPipelineView } from './components/views/ProductionPipelineView';
import { SeriesLibraryView } from './components/views/SeriesLibraryView';
import { RuntimeLogsView } from './components/views/RuntimeLogsView';
import { SettingsView } from './components/views/SettingsView';

import { REAL_EPISODES } from './data/storyosRealData';
import { platformApi } from './api/platformApi';
import { Episode, NavigationTab, ProductionStage, BatchItem, ThemeMode, ProjectItem } from './types';

const STORY_PLACEHOLDER_IMAGE = 'data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E';
import { Search, X, CheckCircle2, AlertCircle, Bell, Clock } from 'lucide-react';

const DEFAULT_PROJECTS: ProjectItem[] = [
  {
    id: 'proj-aigc-dali',
    name: 'aigc-dali-cat',
    description: 'AIGC 视觉模型与工作流项目',
    createdAt: '2026-09-01',
    episodeIds: ['ep-10-01', 'ep-10-02'],
  },
  {
    id: 'proj-storyos',
    name: 'story OS',
    description: 'StoryOS 短剧核心生产与调度中枢',
    createdAt: '2026-09-07',
    episodeIds: ['ep-10-B01', 'ep-09-04', 'ep-09-05'],
  },
  {
    id: 'proj-urban',
    name: '《都市怪谈》系列',
    description: '都市情感与心理悬疑短剧矩阵',
    createdAt: '2026-08-20',
    episodeIds: ['ep-10-01', 'ep-10-02', 'ep-10-B01'],
  },
  {
    id: 'proj-relic',
    name: '《旧物惊魂》系列',
    description: '三十年旧物回响与微缩空间怪谈',
    createdAt: '2026-08-25',
    episodeIds: ['ep-09-04', 'ep-09-05', 'ep-11-01', 'ep-11-01-RE'],
  },
];

export default function App() {
  const [episodes, setEpisodes] = useState<Episode[]>(REAL_EPISODES);
  const [activeEpisode, setActiveEpisode] = useState<Episode>(REAL_EPISODES[0]);
  const [currentTab, setCurrentTab] = useState<NavigationTab>('production_monitor');
  const [isGeneratingBatch, setIsGeneratingBatch] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [contextPanelOpen, setContextPanelOpen] = useState(true);

  // 项目管理状态 (系列即项目，项目下包含具体作品)
  const [projects, setProjects] = useState<ProjectItem[]>(() => {
    try {
      const saved = localStorage.getItem('storyos_projects');
      if (saved) return JSON.parse(saved);
    } catch {}
    return DEFAULT_PROJECTS;
  });

  const saveProjects = (newProjects: ProjectItem[]) => {
    setProjects(newProjects);
    try {
      localStorage.setItem('storyos_projects', JSON.stringify(newProjects));
    } catch {}
  };

  // 项目同级的“最近故事”状态管理 (主页自建故事与最近活跃故事)
  const [recentStoryIds, setRecentStoryIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('storyos_recent_story_ids');
      if (saved) return JSON.parse(saved);
    } catch {}
    return ['ep-10-01', 'ep-10-02', 'ep-10-B01'];
  });

  const saveRecentStories = (newIds: string[]) => {
    setRecentStoryIds(newIds);
    try {
      localStorage.setItem('storyos_recent_story_ids', JSON.stringify(newIds));
    } catch {}
  };

  const handleCreateProject = (name: string) => {
    const newProj: ProjectItem = {
      id: `proj-${Date.now()}`,
      name,
      createdAt: new Date().toISOString().split('T')[0],
      episodeIds: [],
    };
    saveProjects([newProj, ...projects]);
    showToast(`已成功创建项目: ${name}`);
  };

  const handleRenameProject = (projectId: string, newName: string) => {
    const updated = projects.map(p => p.id === projectId ? { ...p, name: newName } : p);
    saveProjects(updated);
    showToast(`项目名称已修改为: ${newName}`);
  };

  const handleDeleteProject = (projectId: string) => {
    const target = projects.find(p => p.id === projectId);
    if (!target) return;
    if (projects.length <= 1) {
      showToast('至少保留一个项目');
      return;
    }
    const updated = projects.filter(p => p.id !== projectId);
    saveProjects(updated);
    showToast(`已删除项目: ${target.name}`);
  };

  // 基础故事结构构建器
  const buildNewEpisode = (id: string, title: string, projectId?: string, initialSynopsis?: string): Episode => {
    return {
      id,
      code: `C-${Math.floor(Math.random() * 90 + 10)}`,
      title,
      projectId,
      synopsis: initialSynopsis || `${title} - StoryOS 4:5 竖屏短剧创作，等待编剧与分镜配置。`,
      logline: '日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。',
      genre: '短剧创作',
      targetAudience: '悬疑短剧高完播人群',
      totalFrames: 24,
      completedFrames: 0,
      currentStage: 'IDEA_LOCK',
      stageProgressPercent: 5,
      coverImage: STORY_PLACEHOLDER_IMAGE,
      updatedAt: '刚刚',
      runtimeRequest: {
        imageModel: 'gpt-image-2',
        quality: 'high',
        aspectRatio: '4:5 1080×1350',
        batchMode: '5 帧逻辑批次',
        maxConcurrentImages: 3,
        executionLayer: 'StoryOS Engine',
        sourceBadge: '已连接生产内核',
      },
      characters: activeEpisode?.characters || [],
      visualLocks: activeEpisode?.visualLocks || [],
      storyboardBeats: [
        {
          id: 'beat-01',
          beatIndex: 1,
          sceneName: '开场序幕',
          act: '第一幕：建立日常',
          shotType: '中景 4:5',
          lighting: '自然柔光',
          narration: '故事的开始总是在看似平常的黄昏...',
          status: 'queued',
        }
      ],
      currentBatch: {
        batchId: 'batch-01',
        batchNumber: 1,
        batchName: '开场序幕 01-05 帧初始批次',
        targetFrames: '01-05',
        totalImages: 5,
        createdAt: '刚刚',
        status: 'ready_for_review',
        items: [],
      },
      frameReviews: [],
      preflightChecks: [],
      performance: activeEpisode?.performance || REAL_EPISODES[0].performance,
    };
  };

  // 1. 在项目上新建的故事，自动归入该项目
  const handleCreateStoryInProject = (projectId: string, title?: string) => {
    const targetProject = projects.find(p => p.id === projectId);
    const storyTitle = title || `新剧目 · ${targetProject?.name || '项目'} #${(targetProject?.episodeIds.length || 0) + 1}`;
    const newEpId = `ep-proj-${Date.now()}`;
    const newEpisode = buildNewEpisode(newEpId, storyTitle, projectId);

    setEpisodes(prev => [newEpisode, ...prev]);
    const updatedProjects = projects.map(p =>
      p.id === projectId
        ? { ...p, episodeIds: [newEpId, ...p.episodeIds] }
        : p
    );
    saveProjects(updatedProjects);
    setActiveEpisode(newEpisode);
    setCurrentTab('workbench');
    showToast(`已在项目《${targetProject?.name || '项目'}》中创建《${storyTitle}》，已自动归入该项目`);
  };

  // 2. 如果是从主页自己建的故事，自动归入项目同级的“最近故事”中
  const handleCreateStoryFromHome = (title?: string) => {
    const count = recentStoryIds.length + 1;
    const storyTitle = title || `主页独立故事 #${count}`;
    const newEpId = `ep-home-${Date.now()}`;
    // 从主页自建，不归入任何特定项目
    const newEpisode = buildNewEpisode(newEpId, storyTitle, undefined);

    setEpisodes(prev => [newEpisode, ...prev]);
    // 自动归入项目同级的“最近故事”中，排在首位
    const nextRecent = [newEpId, ...recentStoryIds.filter(id => id !== newEpId)];
    saveRecentStories(nextRecent);
    setActiveEpisode(newEpisode);
    setCurrentTab('workbench');
    showToast(`已从主页自建故事《${storyTitle}》，已自动归入项目同级的「最近故事」`);
  };

  // 从最近故事移除
  const handleRemoveRecentStory = (storyId: string) => {
    const nextRecent = recentStoryIds.filter(id => id !== storyId);
    saveRecentStories(nextRecent);
  };

  // 主题模式: dark | light | light-gradient
  const [currentTheme, setCurrentTheme] = useState<ThemeMode>('dark');

  const handleThemeChange = (mode: ThemeMode) => {
    setCurrentTheme(mode);
    document.documentElement.classList.remove('theme-dark', 'theme-light', 'theme-light-gradient');
    document.documentElement.classList.add(`theme-${mode}`);
    try {
      localStorage.setItem('storyos_theme', mode);
    } catch {
      // ignore
    }
    showToast(`已切换为${mode === 'dark' ? '深色' : mode === 'light' ? '浅色' : '浅色渐变'}主题`);
  };

  useEffect(() => {
    try {
      const savedTheme = localStorage.getItem('storyos_theme') as ThemeMode | null;
      if (savedTheme && ['dark', 'light', 'light-gradient'].includes(savedTheme)) {
        setCurrentTheme(savedTheme);
        document.documentElement.classList.remove('theme-dark', 'theme-light', 'theme-light-gradient');
        document.documentElement.classList.add(`theme-${savedTheme}`);
      } else {
        document.documentElement.classList.add('theme-dark');
      }
    } catch {
      document.documentElement.classList.add('theme-dark');
    }
  }, []);

  // Search and Notifications Modals
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: '1', title: '婚礼前夜 制作全量通过', desc: '20 帧全量渲染完成并通过逐帧语义审查，发布决策 GO', time: '刚刚', unread: true },
    { id: '2', title: '主角新娘 (P01) 视觉基准锁定', desc: '4:5 1080×1350 肖像一致性评分 98.8% (Ordinary01/Worst11/Anomaly03/Impact15)', time: '1小时前', unread: false },
    { id: '3', title: 'Release Preflight 合规放行', desc: '4:5 1080×1350 叙事画幅全量校验通过，无拉伸无黑边', time: '昨天', unread: false }
  ]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 2500);
  };

  // Keyboard shortcut Ctrl/Cmd + K for quick search & Escape to dismiss
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchModalOpen(prev => !prev);
      } else if (e.key === 'Escape') {
        setSearchModalOpen(false);
        setNotificationsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // 阶段真实流转切换
  const handleStageChange = (newStage: ProductionStage) => {
    const updated: Episode = {
      ...activeEpisode,
      currentStage: newStage,
      updatedAt: '刚刚',
    };
    setActiveEpisode(updated);
    setEpisodes(prev => prev.map(ep => ep.id === updated.id ? updated : ep));
    showToast(`阶段已真实切换为: ${newStage}`);
  };

  // 真实批次出图调度（动态累加出图帧数）
  const handleQuickGenerateNextBatch = () => {
    setIsGeneratingBatch(true);
    setTimeout(() => {
      setIsGeneratingBatch(false);
      const nextCompleted = Math.min(activeEpisode.totalFrames, activeEpisode.completedFrames + 5);
      const nextPercent = Math.round((nextCompleted / activeEpisode.totalFrames) * 100);

      const newItems: BatchItem[] = [21, 22, 23, 24, 25].map((idx) => ({
        id: `b5-f${idx}`,
        frameIndex: idx,
        prompt: `4:5 电影级镜头，主角林澈推开古宅偏殿木门，冷光穿透雨幕 (Frame #${idx})`,
        imageUrl: `https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=700&auto=format&fit=crop&q=80`,
        status: 'qa_passed',
        qaScore: 0.98,
        progress: 100,
        consistencyScore: 0.98,
        renderTime: '11.8s',
        seed: 4892010 + idx,
      }));

      const updated: Episode = {
        ...activeEpisode,
        completedFrames: nextCompleted,
        stageProgressPercent: nextPercent,
        currentStage: nextCompleted >= activeEpisode.totalFrames ? 'READY_TO_PUBLISH' : 'PROD_APPROVED',
        currentBatch: {
          batchId: 'BATCH_05',
          batchNumber: 5,
          batchName: '第 5 批次 (Frame #21 - #25)',
          targetFrames: '21-25',
          totalImages: newItems.length,
          createdAt: '刚刚',
          status: 'completed',
          items: newItems,
        },
        updatedAt: '刚刚',
      };

      setActiveEpisode(updated);
      setEpisodes(prev => prev.map(ep => ep.id === updated.id ? updated : ep));
      showToast(`第 5 批次 5 帧 (4:5 1080×1350) 已成功生成并入库 (${nextCompleted}/${activeEpisode.totalFrames} 帧)`);
    }, 1200);
  };

  // 命令输入调度
  const handleCommandSubmit = (commandText: string) => {
    showToast(`StoryOS 已调度: “${commandText.slice(0, 16)}...”`);

    if (commandText.length > 5) {
      const newEpId = `ep-cmd-${Date.now()}`;
      const title = commandText.length > 14 ? commandText.slice(0, 14) + '...' : commandText;
      const newEp = buildNewEpisode(newEpId, title, undefined, commandText);
      newEp.code = `EP-0${episodes.length + 1}`;
      newEp.currentStage = 'PROD_APPROVED';
      newEp.stageProgressPercent = 16;
      newEp.completedFrames = 5;

      setEpisodes(prev => [newEp, ...prev]);
      // 自动归入项目同级的“最近故事”中
      const nextRecent = [newEpId, ...recentStoryIds.filter(id => id !== newEpId)];
      saveRecentStories(nextRecent);
      setActiveEpisode(newEp);
      setCurrentTab('workbench');
      showToast(`已从主页调度生成《${newEp.title}》，已自动归入项目同级的「最近故事」`);
    }
  };

  const handleReviewAction = (frameId: string, action: 'pass' | 'inpaint' | 'reject') => {
    if (action === 'inpaint') {
      showToast(`Frame #${frameId} 已执行 Inpaint 倒影微瑕修复，质检通过`);
    } else if (action === 'pass') {
      showToast(`Frame #${frameId} 质检已核准通过`);
    }
  };

  const searchResults = episodes.filter(ep =>
    ep.title.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    ep.code.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    ep.synopsis.toLowerCase().includes(searchKeyword.toLowerCase())
  );

  return (
    <div id="storyos-workspace-root" className="flex h-screen w-screen overflow-hidden bg-[var(--bg-app)] text-[var(--text-primary)] font-sans antialiased select-text">
      {/* 1. 纯黑底白字极简左侧边栏 */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        activeEpisode={activeEpisode}
        allEpisodes={episodes}
        onSelectEpisode={(ep) => setActiveEpisode(ep)}
        projects={projects}
        onCreateProject={handleCreateProject}
        onRenameProject={handleRenameProject}
        onDeleteProject={handleDeleteProject}
        onCreateStoryInProject={handleCreateStoryInProject}
        onCreateStoryFromHome={handleCreateStoryFromHome}
        recentStoryIds={recentStoryIds}
        onRemoveRecentStory={handleRemoveRecentStory}
        onNewConversation={() => {
          handleCreateStoryFromHome();
        }}
        onOpenSearch={() => setSearchModalOpen(true)}
        onOpenNotifications={() => setNotificationsOpen(true)}
        unreadCount={notifications.filter(n => n.unread).length}
        onToggleContextPanel={() => setContextPanelOpen(!contextPanelOpen)}
        contextPanelOpen={contextPanelOpen}
        currentTheme={currentTheme}
        onThemeChange={handleThemeChange}
        onShowToast={showToast}
      />

      {/* 2. 中间主工作台 */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative min-w-0 bg-[var(--bg-app)]">
        {/* 顶部极简标题栏 */}
        <HeaderBar
          activeEpisode={activeEpisode}
          allEpisodes={episodes}
          onSelectEpisode={(ep) => setActiveEpisode(ep)}
          onToggleContextPanel={() => setContextPanelOpen(!contextPanelOpen)}
          contextPanelOpen={contextPanelOpen}
          onOpenSettings={() => setCurrentTab('settings')}
        />

        {/* 消息与活动主轴 (日志视图占满屏幕全屏铺开) */}
        <main className={`flex-1 ${currentTab === 'logs' ? 'p-0 overflow-hidden' : 'overflow-y-auto px-4 lg:px-5 py-4'} relative scrollbar-thin scrollbar-thumb-[var(--border-normal)] bg-[var(--bg-app)]`}>
          {/* 轻量 Toast */}
          {toastMessage && (
            <div className="fixed top-12 right-6 z-50 bg-[var(--bg-elevated)] text-[var(--text-primary)] px-3.5 py-1.5 rounded-[6px] text-xs font-medium flex items-center gap-2 shadow-lg border border-[var(--border-normal)]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#58A6FF]" />
              <span>{toastMessage}</span>
            </div>
          )}

          {/* 生产监控台主控页 (StoryOS 生产监控台 V1.0 - Dense Operations Console) */}
          {currentTab === 'production_monitor' && (
            <div className="w-full">
              <ProductionMonitorView
                onShowToast={showToast}
                onSelectStoryRun={(run) => {
                  const matchEp = episodes.find(e => e.title === run.storyName);
                  if (matchEp) {
                    setActiveEpisode(matchEp);
                  }
                }}
              />
            </div>
          )}

          {/* 主要流程全景规范与门禁时序视图 */}
          {currentTab === 'pipeline' && (
            <div className="max-w-5xl mx-auto">
              <ProductionPipelineView
                activeEpisode={activeEpisode}
                onStageChange={handleStageChange}
                onGoToWorkbench={() => setCurrentTab('workbench')}
                onShowToast={showToast}
              />
            </div>
          )}

          {/* 剧集库视图 */}
          {currentTab === 'episodes' && (
            <div className="max-w-4xl mx-auto">
              <SeriesLibraryView
                episodes={episodes}
                activeEpisode={activeEpisode}
                onSelectEpisode={(ep) => {
                  setActiveEpisode(ep);
                  setCurrentTab('workbench');
                }}
                onGoToWorkbench={() => setCurrentTab('workbench')}
                onNewStoryClick={() => handleCreateStoryFromHome()}
              />
            </div>
          )}

          {/* 运行日志审计视图 (占满屏幕，全屏展示) */}
          {currentTab === 'logs' && (
            <div className="w-full h-full flex flex-col overflow-hidden">
              <RuntimeLogsView />
            </div>
          )}

          {/* 系统设置视图 */}
          {currentTab === 'settings' && (
            <div className="max-w-4xl mx-auto">
              <SettingsView
                currentTheme={currentTheme}
                onThemeChange={handleThemeChange}
              />
            </div>
          )}

          {/* 核心工作流：呼吸感单主轴 */}
          {currentTab === 'workbench' && (
            <div className="max-w-3xl mx-auto space-y-3">
              {/* 单行极简流水线微型指示器（支持真实点击切换生产阶段） */}
              <StatusFlowBanner
                currentStage={activeEpisode.currentStage}
                onStageChange={handleStageChange}
                completedFrames={activeEpisode.completedFrames}
                totalFrames={activeEpisode.totalFrames}
                onOpenPipelineView={() => setCurrentTab('pipeline')}
              />

              {/* 视觉一致性与批次效率综合监控面板 */}
              <ProductionMetricsPanel
                activeEpisode={activeEpisode}
                onShowToast={showToast}
              />

              {/* 真正的对话与执行流 */}
              <ActivityStream
                activeEpisode={activeEpisode}
                onGenerateBatch={handleQuickGenerateNextBatch}
                isGeneratingBatch={isGeneratingBatch}
                onReviewAction={handleReviewAction}
                onShowToast={showToast}
              />
            </div>
          )}
        </main>

        {/* 3. 悬浮极简输入坞（纯黑底白字） */}
        {currentTab === 'workbench' && (
          <CommandDock
            onSendMessage={handleCommandSubmit}
            isLoading={isGeneratingBatch}
          />
        )}
      </div>

      {/* 4. 纯净右侧上下文与资产账本栏 (日志与大盘下自动让出全屏) */}
      {contextPanelOpen && currentTab !== 'production_monitor' && currentTab !== 'logs' && (
        <ContextPanel
          activeEpisode={activeEpisode}
          onClose={() => setContextPanelOpen(false)}
          onShowToast={showToast}
        />
      )}

      {/* 5. 全局搜索模态弹窗 (Ctrl + K / 侧边栏搜索) */}
      {searchModalOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-start justify-center pt-24 px-4 backdrop-blur-xs"
          onClick={() => setSearchModalOpen(false)}
        >
          <div
            className="bg-[var(--bg-elevated)] border border-[var(--border-normal)] rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl text-[var(--text-primary)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-3 border-b border-[var(--border-subtle)] flex items-center gap-2">
              <Search className="w-4 h-4 text-[var(--text-secondary)]" />
              <input
                type="text"
                autoFocus
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="搜索剧集编号、标题、剧情关键词..."
                className="w-full bg-transparent text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-hidden"
              />
              <button
                type="button"
                onClick={() => setSearchModalOpen(false)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-xs px-1.5 py-0.5 rounded cursor-pointer"
              >
                ESC
              </button>
            </div>

            <div className="max-h-72 overflow-y-auto p-2 space-y-1">
              {searchResults.length === 0 ? (
                <div className="py-6 text-center text-xs text-[var(--text-tertiary)] font-mono">未找到匹配的故事资产</div>
              ) : (
                searchResults.map(ep => (
                  <button
                    key={ep.id}
                    type="button"
                    onClick={() => {
                      setActiveEpisode(ep);
                      setCurrentTab('workbench');
                      setSearchModalOpen(false);
                      showToast(`已切换至: ${ep.code} ${ep.title}`);
                    }}
                    className="w-full text-left p-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors flex items-center justify-between cursor-pointer"
                  >
                    <div>
                      <div className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-2">
                        <span className="font-mono text-[var(--text-tertiary)] font-bold">{ep.code}</span>
                        <span>{ep.title}</span>
                      </div>
                      <div className="text-[11px] text-[var(--text-secondary)] truncate max-w-sm">{ep.synopsis}</div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border-normal)] text-[var(--text-secondary)]">
                      {ep.completedFrames}/{ep.totalFrames} 帧
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* 6. 通知与流水抽屉 */}
      {notificationsOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/70 flex justify-end backdrop-blur-xs"
          onClick={() => setNotificationsOpen(false)}
        >
          <div
            className="w-80 bg-[var(--bg-elevated)] border-l border-[var(--border-normal)] h-full p-4 flex flex-col space-y-3 shadow-2xl text-[var(--text-primary)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-[var(--text-primary)]" />
                <span className="text-xs font-bold text-[var(--text-primary)]">生产通知与质检流水</span>
              </div>
              <button
                type="button"
                onClick={() => setNotificationsOpen(false)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-xs cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2">
              {notifications.map(n => (
                <div
                  key={n.id}
                  className={`p-2.5 rounded-xl border text-xs space-y-1 ${
                    n.unread
                      ? 'bg-[var(--bg-surface)] border-[var(--border-strong)] text-[var(--text-primary)] shadow-xs'
                      : 'bg-[var(--bg-workspace)] border-[var(--border-subtle)] text-[var(--text-secondary)]'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span className="text-[var(--text-primary)]">{n.title}</span>
                    <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{n.time}</span>
                  </div>
                  <div className="text-[11px] leading-relaxed text-[var(--text-secondary)]">{n.desc}</div>
                </div>
              ))}
            </div>

            <button
              type="button"
              onClick={() => {
                setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
                showToast('已全部标记为已读');
              }}
              className="w-full py-1.5 rounded-lg bg-white text-black font-semibold text-xs hover:bg-zinc-200 transition-colors cursor-pointer shadow-xs"
            >
              全部标记为已读
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
