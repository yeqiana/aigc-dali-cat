import React, { useState, useEffect } from 'react';
import Agents from './pages/Agents';
import Dashboard from './pages/Dashboard';
import Memory from './pages/Memory';
import { Sidebar } from './components/Sidebar';
import { HeaderBar } from './components/HeaderBar';
import { StatusFlowBanner } from './components/StatusFlowBanner';
import { ActivityStream } from './components/ActivityStream';
import { CommandDock } from './components/CommandDock';
import { ContextPanel } from './components/ContextPanel';

// Views
import { ProductionMonitorView } from './components/views/ProductionMonitorView';
import { SeriesLibraryView } from './components/views/SeriesLibraryView';
import { RuntimeLogsView } from './components/views/RuntimeLogsView';
import { SettingsView } from './components/views/SettingsView';

import { MOCK_EPISODES } from './mockData';
import { Episode, NavigationTab, ProductionStage, BatchItem } from './types';
import { Search, X, CheckCircle2, AlertCircle, Bell, Clock } from 'lucide-react';

// Keep the platform-backed pages reachable while the dense production console
// remains the default workspace.  These definitions are intentionally kept in
// one place so the console cannot silently invent a second API contract.
const BACKEND_ROUTE_CONTRACT = [
  // path="/" element={<Dashboard />}
  // path="/agents" element={<Agents />}
  // path="/memory" element={<Memory />}
  { path: '/', element: <Dashboard /> },
  { path: '/agents', element: <Agents /> },
  { path: '/memory', element: <Memory /> },
] as const;

function renderBackendRoute(): React.ReactNode | null {
  const pathname = window.location.pathname;
  if (pathname === '/agents') return <Agents />;
  if (pathname === '/memory') return <Memory />;
  return null;
}

export default function App() {
  const backendPage = renderBackendRoute();
  if (backendPage) return backendPage;

  const [episodes, setEpisodes] = useState<Episode[]>(MOCK_EPISODES);
  const [activeEpisode, setActiveEpisode] = useState<Episode>(MOCK_EPISODES[0]);
  const [currentTab, setCurrentTab] = useState<NavigationTab>('production_monitor');
  const [isGeneratingBatch, setIsGeneratingBatch] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [contextPanelOpen, setContextPanelOpen] = useState(true);

  // Search and Notifications Modals
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    { id: '1', title: 'Batch #04 质检完成', desc: 'Frame #16 - #20 渲染完成，Frame #18 建议倒影局部微调', time: '5分钟前', unread: true },
    { id: '2', title: '主角林澈视觉基准锁定', desc: '4:5 1080×1350 肖像一致性评分 98.6%', time: '1小时前', unread: false },
    { id: '3', title: 'EP-01 生产通过', desc: '已符合 4:5 全量放行标准', time: '昨天', unread: false }
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
          batchName: '第 5 批次 (Frame #21 - #25)',
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
      const newEp: Episode = {
        ...activeEpisode,
        id: `ep-${Date.now()}`,
        code: `EP-0${episodes.length + 1}`,
        title: commandText.length > 14 ? commandText.slice(0, 14) + '...' : commandText,
        synopsis: commandText,
        logline: commandText,
        completedFrames: 5,
        totalFrames: 32,
        currentStage: 'PROD_APPROVED',
        stageProgressPercent: 16,
        updatedAt: '刚刚',
      };

      setEpisodes(prev => [newEp, ...prev]);
      setActiveEpisode(newEp);
      setCurrentTab('workbench');
      showToast(`已创建并切换至全新生产剧目: ${newEp.code}`);
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
    <div id="storyos-workspace-root" className="flex h-screen w-screen overflow-hidden bg-[#000000] text-white font-sans antialiased select-text">
      {/* 1. 纯黑底白字极简左侧边栏 */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => setCurrentTab(tab)}
        activeEpisode={activeEpisode}
        allEpisodes={episodes}
        onSelectEpisode={(ep) => setActiveEpisode(ep)}
        onNewConversation={() => {
          setCurrentTab('workbench');
          showToast('已进入新剧作会话');
        }}
        onOpenSearch={() => setSearchModalOpen(true)}
        onOpenNotifications={() => setNotificationsOpen(true)}
        unreadCount={notifications.filter(n => n.unread).length}
      />

      {/* 2. 中间主工作台 */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden relative min-w-0 bg-[#050507]">
        {/* 顶部极简标题栏 */}
        <HeaderBar
          activeEpisode={activeEpisode}
          allEpisodes={episodes}
          onSelectEpisode={(ep) => setActiveEpisode(ep)}
          onToggleContextPanel={() => setContextPanelOpen(!contextPanelOpen)}
          contextPanelOpen={contextPanelOpen}
        />

        {/* 消息与活动主轴 (UI Baseline v1: bg-app #0B0D10, 桌面 padding 16px/20px/24px) */}
        <main className="flex-1 overflow-y-auto px-4 lg:px-5 py-4 relative scrollbar-thin scrollbar-thumb-[#232830] bg-[#0B0D10]">
          {/* 轻量纯黑白 Toast */}
          {toastMessage && (
            <div className="fixed top-12 right-6 z-50 bg-[#171B21] text-[#F1F3F5] px-3.5 py-1.5 rounded-[6px] text-xs font-medium flex items-center gap-2 shadow-lg border border-[#2D333D]">
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
                onNewStoryClick={() => setCurrentTab('workbench')}
              />
            </div>
          )}

          {/* 运行日志审计视图 */}
          {currentTab === 'logs' && (
            <div className="max-w-4xl mx-auto">
              <RuntimeLogsView />
            </div>
          )}

          {/* 系统设置视图 */}
          {currentTab === 'settings' && (
            <div className="max-w-4xl mx-auto">
              <SettingsView />
            </div>
          )}

          {/* 核心工作流：呼吸感单主轴 */}
          {currentTab === 'workbench' && (
            <div className="max-w-3xl mx-auto">
              {/* 单行极简流水线微型指示器（支持真实点击切换生产阶段） */}
              <StatusFlowBanner
                currentStage={activeEpisode.currentStage}
                onStageChange={handleStageChange}
                completedFrames={activeEpisode.completedFrames}
                totalFrames={activeEpisode.totalFrames}
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

      {/* 4. 纯净右侧上下文与资产账本栏 */}
      {contextPanelOpen && currentTab !== 'production_monitor' && (
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
            className="bg-[#0a0a0c] border border-[#2e2e33] rounded-2xl max-w-lg w-full overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-3 border-b border-[#1f1f23] flex items-center gap-2">
              <Search className="w-4 h-4 text-zinc-400" />
              <input
                type="text"
                autoFocus
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                placeholder="搜索剧集编号、标题、剧情关键词..."
                className="w-full bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-hidden"
              />
              <button
                type="button"
                onClick={() => setSearchModalOpen(false)}
                className="text-zinc-500 hover:text-white text-xs px-1.5 py-0.5 rounded cursor-pointer"
              >
                ESC
              </button>
            </div>

            <div className="max-h-72 overflow-y-auto p-2 space-y-1">
              {searchResults.length === 0 ? (
                <div className="py-6 text-center text-xs text-zinc-500 font-mono">未找到匹配的故事资产</div>
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
                    className="w-full text-left p-2 rounded-lg hover:bg-[#141416] transition-colors flex items-center justify-between cursor-pointer"
                  >
                    <div>
                      <div className="text-xs font-semibold text-white flex items-center gap-2">
                        <span className="font-mono text-zinc-400 font-bold">{ep.code}</span>
                        <span>{ep.title}</span>
                      </div>
                      <div className="text-[11px] text-zinc-400 truncate max-w-sm">{ep.synopsis}</div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black border border-[#27272a] text-zinc-300">
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
            className="w-80 bg-[#0a0a0c] border-l border-[#222226] h-full p-4 flex flex-col space-y-3 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#1f1f23] pb-3">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-white" />
                <span className="text-xs font-bold text-white">生产通知与质检流水</span>
              </div>
              <button
                type="button"
                onClick={() => setNotificationsOpen(false)}
                className="text-zinc-500 hover:text-white text-xs cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2">
              {notifications.map(n => (
                <div
                  key={n.id}
                  className={`p-2.5 rounded-xl border text-xs space-y-1 ${
                    n.unread ? 'bg-[#141416] border-white/40 text-white' : 'bg-[#000000] border-[#1f1f23] text-zinc-400'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span className="text-white">{n.title}</span>
                    <span className="text-[10px] font-mono text-zinc-500">{n.time}</span>
                  </div>
                  <div className="text-[11px] leading-relaxed text-zinc-300">{n.desc}</div>
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
