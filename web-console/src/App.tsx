import React, { lazy, Suspense, useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { HeaderBar } from './components/HeaderBar';

// Views
import { ProductionMonitorView } from './components/views/ProductionMonitorView';

import { MOCK_EPISODES } from './mockData';
import { Episode, NavigationTab, BatchItem } from './types';
import { Search, Bell } from 'lucide-react';

const PlatformDashboard = lazy(() => import('./pages/Dashboard'));
const AgentsConsole = lazy(() => import('./pages/Agents'));
const MemoryConsole = lazy(() => import('./pages/Memory'));
const ExecutionExplorer = lazy(() => import('./pages/ExecutionExplorer'));
const TraceExplorer = lazy(() => import('./pages/TraceExplorer'));
const RuntimeVisualization = lazy(() => import('./pages/RuntimeVisualization'));
const StatusFlowBanner = lazy(() => import('./components/StatusFlowBanner').then((module) => ({ default: module.StatusFlowBanner })));
const ActivityStream = lazy(() => import('./components/ActivityStream').then((module) => ({ default: module.ActivityStream })));
const CommandDock = lazy(() => import('./components/CommandDock').then((module) => ({ default: module.CommandDock })));
const ContextPanel = lazy(() => import('./components/ContextPanel').then((module) => ({ default: module.ContextPanel })));
const ProductionStagePanel = lazy(() => import('./components/ProductionStagePanel').then((module) => ({ default: module.ProductionStagePanel })));
const SeriesLibraryView = lazy(() => import('./components/views/SeriesLibraryView').then((module) => ({ default: module.SeriesLibraryView })));
const RuntimeLogsView = lazy(() => import('./components/views/RuntimeLogsView').then((module) => ({ default: module.RuntimeLogsView })));
const SettingsView = lazy(() => import('./components/views/SettingsView').then((module) => ({ default: module.SettingsView })));

// Keep the platform-backed pages reachable while the dense production console
// remains the default workspace.  These definitions are intentionally kept in
// one place so the console cannot silently invent a second API contract.
const BACKEND_ROUTE_CONTRACT = [
  { path: '/platform', Component: PlatformDashboard },
  { path: '/agents', Component: AgentsConsole },
  { path: '/memory', Component: MemoryConsole },
  { path: '/executions', Component: ExecutionExplorer },
  { path: '/traces', Component: TraceExplorer },
  { path: '/runtime', Component: RuntimeVisualization },
] as const;

function renderBackendRoute(): React.ReactNode | null {
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/';
  const route = BACKEND_ROUTE_CONTRACT.find((item) => item.path === pathname);
  if (!route) return null;
  const Component = route.Component;
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-tertiary)] flex items-center justify-center text-xs font-mono">
          Loading Platform Console…
        </div>
      }
    >
      <Component />
    </Suspense>
  );
}

function UnsupportedRoute() {
  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6 flex items-center justify-center">
      <section className="storyos-surface w-full max-w-lg p-5">
        <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">StoryOS / Route</div>
        <h1 className="mt-1 text-lg font-semibold">Unsupported Console Route</h1>
        <p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]">
          当前路径没有已接入的 StoryOS Console 能力。未配置的 Platform capability 不会回退成假页面。
        </p>
        <div className="mt-4 flex items-center gap-2">
          <a href="/" className="storyos-control h-8 px-3 inline-flex items-center text-xs">Production Console</a>
          <a href="/platform" className="h-8 px-3 rounded-[var(--radius-md)] bg-[var(--primary)] text-white inline-flex items-center text-xs font-medium">Platform Console</a>
        </div>
      </section>
    </main>
  );
}

function ConsoleSectionFallback({ label }: { label: string }) {
  return (
    <div className="storyos-surface min-h-24 flex items-center justify-center text-[11px] font-mono text-[var(--text-tertiary)]">
      Loading {label}…
    </div>
  );
}

function ProductionConsole() {
  const [episodes, setEpisodes] = useState<Episode[]>(MOCK_EPISODES);
  const [activeEpisode, setActiveEpisode] = useState<Episode>(MOCK_EPISODES[0]);
  const [currentTab, setCurrentTab] = useState<NavigationTab>('production_monitor');
  const [isGeneratingBatch, setIsGeneratingBatch] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [contextPanelOpen, setContextPanelOpen] = useState(false);

  // Search and Notifications Modals
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: '1', title: '[示例] Batch #04 质检状态', desc: '前端示例：Frame #16 - #20 标记完成，Frame #18 建议局部微调', time: '5分钟前', unread: true },
    { id: '2', title: '[示例] 主角视觉基准', desc: '前端示例：4:5 1080×1350 肖像一致性评分 98.6%', time: '1小时前', unread: false },
    { id: '3', title: '[示例] EP-01 阶段状态', desc: '前端示例：显示为生产通过，不代表 Episode Authority', time: '昨天', unread: false }
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

  // 前端演示批次调度；正式生产阶段只由 StoryOS canonical state transition 推进。
  const handleQuickGenerateNextBatch = () => {
    setIsGeneratingBatch(true);
    setTimeout(() => {
      setIsGeneratingBatch(false);
      const nextCompleted = Math.min(activeEpisode.totalFrames, activeEpisode.completedFrames + 5);

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
        currentStage: nextCompleted >= activeEpisode.totalFrames ? 'PUBLISH_READY' : 'PRODUCTION_PASSED',
        currentBatch: {
          batchId: 'BATCH_05',
          batchName: '第 5 批次 (Frame #21 - #25)',
          status: 'completed',
          items: newItems,
        },
        updatedAt: '刚刚',
      };

      setActiveEpisode(updated);
      setEpisodes(prev => prev.map(ep => ep.id === updated.id ? updated : ep));
      showToast(`示例批次已更新 (${nextCompleted}/${activeEpisode.totalFrames} 帧)，未写入生产 Authority`);
    }, 1200);
  };

  // 命令输入调度
  const handleCommandSubmit = (commandText: string) => {
    showToast(`前端示例指令已应用: “${commandText.slice(0, 16)}...” · 未写入 Runtime/Authority`);

    if (commandText.length > 5) {
      const newEp: Episode = {
        ...activeEpisode,
        id: `ep-${Date.now()}`,
        code: `EP-0${episodes.length + 1}`,
        title: commandText.length > 14 ? commandText.slice(0, 14) + '...' : commandText,
        synopsis: commandText,
        completedFrames: 0,
        totalFrames: 32,
        currentStage: 'IDEA_LOCKED',
        updatedAt: '刚刚',
      };

      setEpisodes(prev => [newEp, ...prev]);
      setActiveEpisode(newEp);
      setCurrentTab('workbench');
      showToast(`已创建前端示例剧目: ${newEp.code}；未写入生产 Authority`);
    }
  };

  const handleReviewAction = (frameId: string, action: 'pass' | 'inpaint' | 'reject') => {
    if (action === 'inpaint') {
      showToast(`Frame #${frameId} 已更新前端示例 Inpaint 状态 · 未写入 Review Authority`);
    } else if (action === 'pass') {
      showToast(`Frame #${frameId} 已更新前端示例 PASS 状态 · 未写入 Review Authority`);
    }
  };

  const searchResults = episodes.filter(ep =>
    ep.title.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    ep.code.toLowerCase().includes(searchKeyword.toLowerCase()) ||
    ep.synopsis.toLowerCase().includes(searchKeyword.toLowerCase())
  );

  return (
    <div id="storyos-workspace-root" className="storyos-shell flex h-screen w-screen overflow-hidden font-sans antialiased select-text">
      {/* 1. 纯黑底白字极简左侧边栏 */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        activeEpisode={activeEpisode}
        allEpisodes={episodes}
        onSelectEpisode={(ep) => setActiveEpisode(ep)}
        onNewConversation={() => {
          setCurrentTab('workbench');
          showToast('已进入前端示例剧作会话 · 未创建生产 Episode');
        }}
        onOpenSearch={() => setSearchModalOpen(true)}
        onOpenNotifications={() => setNotificationsOpen(true)}
        unreadCount={notifications.filter(n => n.unread).length}
      />

      {/* 2. 中间主工作台 */}
      <div className="storyos-workspace flex-1 flex flex-col h-screen overflow-hidden relative min-w-0">
        {/* 顶部极简标题栏 */}
        <HeaderBar
          activeEpisode={activeEpisode}
          allEpisodes={episodes}
          onSelectEpisode={(ep) => setActiveEpisode(ep)}
          onToggleContextPanel={() => setContextPanelOpen(!contextPanelOpen)}
          contextPanelOpen={contextPanelOpen}
        />

        {/* 消息与活动主轴 (UI Baseline v1: bg-app #0B0D10, 桌面 padding 16px/20px/24px) */}
        <main className="flex-1 overflow-y-auto px-4 lg:px-5 py-4 relative bg-[var(--bg-app)]">
          {/* 轻量纯黑白 Toast */}
          {toastMessage && (
            <div className="fixed top-12 right-6 z-50 storyos-elevated text-[var(--text-primary)] px-3.5 py-1.5 text-xs font-medium flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--info)]" />
              <span>{toastMessage}</span>
            </div>
          )}

          {/* 生产监控台主控页 (StoryOS 生产监控台 V1.0 - Dense Operations Console) */}
          {currentTab === 'production_monitor' && (
            <div className="w-full">
              <ProductionMonitorView
                onShowToast={showToast}
              />
            </div>
          )}

          {/* 剧集库视图 */}
          {currentTab === 'episodes' && (
            <Suspense fallback={<ConsoleSectionFallback label="Episodes" />}>
              <div className="max-w-4xl mx-auto">
                <SeriesLibraryView
                  episodes={episodes}
                  activeEpisode={activeEpisode}
                  onSelectEpisode={(ep) => {
                    setActiveEpisode(ep);
                    setCurrentTab('workbench');
                  }}
                  onGoToWorkbench={() => setCurrentTab('workbench')}
                  onNewStoryClick={() => setCurrentTab('workbench')}
                />
              </div>
            </Suspense>
          )}

          {/* 运行日志审计视图 */}
          {currentTab === 'logs' && (
            <Suspense fallback={<ConsoleSectionFallback label="Runtime Logs" />}>
              <div className="max-w-4xl mx-auto">
                <RuntimeLogsView />
              </div>
            </Suspense>
          )}

          {/* 系统设置视图 */}
          {currentTab === 'settings' && (
            <Suspense fallback={<ConsoleSectionFallback label="Settings" />}>
              <div className="max-w-4xl mx-auto">
                <SettingsView />
              </div>
            </Suspense>
          )}

          {/* 核心工作流：Operator Console / Production Stage 双区 */}
          {currentTab === 'workbench' && (
            <Suspense fallback={<ConsoleSectionFallback label="Workbench" />}>
              <div className="grid min-h-full grid-cols-1 xl:grid-cols-[minmax(360px,38%)_minmax(0,62%)] gap-4 pb-24">
                <section aria-label="Operator Console" className="min-w-0">
                  <StatusFlowBanner
                    currentStage={activeEpisode.currentStage}
                    completedFrames={activeEpisode.completedFrames}
                    totalFrames={activeEpisode.totalFrames}
                  />
                  <ActivityStream
                    activeEpisode={activeEpisode}
                    onGenerateBatch={handleQuickGenerateNextBatch}
                    isGeneratingBatch={isGeneratingBatch}
                    onReviewAction={handleReviewAction}
                    onShowToast={showToast}
                  />
                </section>

                <ProductionStagePanel
                  activeEpisode={activeEpisode}
                  isGeneratingBatch={isGeneratingBatch}
                  onSelectFrame={(frame) => showToast(`已选中 Frame #${frame.frameIndex} · ${frame.status}`)}
                />
              </div>
            </Suspense>
          )}
        </main>

        {/* 3. 悬浮极简输入坞（纯黑底白字） */}
        {currentTab === 'workbench' && (
          <Suspense fallback={null}>
            <CommandDock
              onSendMessage={handleCommandSubmit}
              isLoading={isGeneratingBatch}
            />
          </Suspense>
        )}
      </div>

      {/* 4. 纯净右侧上下文与资产账本栏 */}
      {contextPanelOpen && currentTab !== 'production_monitor' && (
        <Suspense fallback={null}>
          <ContextPanel
            activeEpisode={activeEpisode}
            onShowToast={showToast}
          />
        </Suspense>
      )}

      {/* 5. 全局搜索模态弹窗 (Ctrl + K / 侧边栏搜索) */}
      {searchModalOpen && (
        <div
          className="storyos-overlay fixed inset-0 z-50 flex items-start justify-center pt-24 px-4"
          onClick={() => setSearchModalOpen(false)}
        >
          <div
            className="storyos-elevated max-w-lg w-full overflow-hidden"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="搜索 StoryOS 示例剧集"
          >
            <div className="p-3 border-b border-[var(--border-subtle)] flex items-center gap-2">
              <Search className="w-4 h-4 text-[var(--text-tertiary)]" />
              <input
                type="text"
                autoFocus
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="搜索剧集编号、标题、剧情关键词..."
                className="w-full bg-transparent text-sm text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] focus:outline-hidden"
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
                    className="w-full text-left p-2 rounded-[var(--radius-sm)] hover:bg-[var(--bg-hover)] transition-colors flex items-center justify-between cursor-pointer"
                  >
                    <div>
                      <div className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-2">
                        <span className="font-mono text-[var(--text-tertiary)] font-semibold">{ep.code}</span>
                        <span>{ep.title}</span>
                      </div>
                      <div className="text-[11px] text-[var(--text-tertiary)] truncate max-w-sm">{ep.synopsis}</div>
                    </div>
                    <span className="storyos-status storyos-status--neutral font-mono">
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
          className="storyos-overlay fixed inset-0 z-50 flex justify-end"
          onClick={() => setNotificationsOpen(false)}
        >
          <div
            className="storyos-drawer w-[var(--drawer-width)] max-w-[90vw] h-full p-4 flex flex-col space-y-3"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="生产通知与质检流水"
          >
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-[var(--primary)]" />
                <span className="text-xs font-semibold text-[var(--text-primary)]">生产通知与质检流水</span>
              </div>
              <button
                type="button"
                onClick={() => setNotificationsOpen(false)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] text-xs cursor-pointer"
                aria-label="关闭通知抽屉"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2">
              {notifications.map(n => (
                <div
                  key={n.id}
                  className={`p-2.5 rounded-[var(--radius-md)] border text-xs space-y-1 ${
                    n.unread ? 'bg-[var(--bg-selected)] border-[var(--border-strong)] text-[var(--text-primary)]' : 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-secondary)]'
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
              className="storyos-control w-full px-3 font-semibold text-xs cursor-pointer"
            >
              全部标记为已读
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const backendPage = renderBackendRoute();
  if (backendPage) return backendPage;
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/';
  return pathname === '/' ? <ProductionConsole /> : <UnsupportedRoute />;
}
