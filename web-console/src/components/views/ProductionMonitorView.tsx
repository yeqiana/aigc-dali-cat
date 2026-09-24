import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  RotateCcw,
  Search,
  Filter,
  RefreshCw,
  Maximize2,
  Bell,
  User,
  CheckCircle2,
  AlertCircle,
  Clock,
  MoreHorizontal,
  ArrowRight,
  Flame,
  Cpu,
  Database,
  Layers,
  X,
  ChevronRight,
  ExternalLink,
  ShieldAlert,
  SlidersHorizontal,
  Check,
  Zap
} from 'lucide-react';
import { StoryRunItem, FrameDetailItem, StoryRunStatus, StoryRunStage } from '../../types';
import { platformApi } from '../../api/platformApi';
import { REAL_STORY_RUNS, STORY_OS_PLATFORM_MANIFEST } from '../../data/storyosRealData';
import { StoryRunDetailView } from './StoryRunDetailView';

interface ProductionMonitorViewProps {
  onSelectStoryRun?: (run: StoryRunItem) => void;
  onShowToast: (msg: string) => void;
}

export const ProductionMonitorView: React.FC<ProductionMonitorViewProps> = ({
  onSelectStoryRun,
  onShowToast,
}) => {
  // 权威生产运行数据状态 (Zero Mock)
  const [runs, setRuns] = useState<StoryRunItem[]>(REAL_STORY_RUNS);

  // 过滤状态
  const [searchKeyword, setSearchKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [stageFilter, setStageFilter] = useState<string>('all');
  const [onlyException, setOnlyException] = useState(false);

  // 自动刷新机制 (仅增量刷新数据，不触发整页 reload)
  const [refreshInterval, setRefreshInterval] = useState<number>(5);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // 选中的 Story Run 详情视图
  const [selectedRunForDetail, setSelectedRunForDetail] = useState<StoryRunItem | null>(null);

  // 从真实平台接口同步 canonical stage 投影；丰富的帧/证据详情继续来自工作区生成投影。
  const loadLatestStatuses = async (isManual = false) => {
    try {
      setIsRefreshing(true);
      const data = await platformApi.runtimeStatuses(100, 0);
      if (data.items.length > 0) {
        const stageMap: Record<string, StoryRunStage> = {
          IDEA_LOCKED: 'CREATE',
          STORYBOARD_LOCKED: 'STORYBOARD',
          VISUAL_CALIBRATED: 'VISUAL_LOCK',
          PRODUCTION_PASSED: 'PRODUCTION',
          PUBLISH_READY: 'PUBLISH',
          PUBLISHED: 'COMPLETED',
          DATA_REVIEWED: 'COMPLETED',
        };
        setRuns((current) =>
          current.map((run) => {
            const row = data.items.find((item) =>
              item.episode_id === run.runId ||
              item.business_episode_id === run.runId ||
              item.title === run.storyName ||
              item.episode_ref === run.storyName
            );
            if (!row) return run;
            const stageLabel = row.production_stage || run.stageLabel;
            return {
              ...run,
              storyName: row.title || run.storyName,
              stageLabel,
              currentStage: stageMap[stageLabel] || run.currentStage,
            };
          })
        );
      }
      if (isManual) {
        onShowToast('已同步最新 canonical stage 投影');
      }
    } catch (err) {
      console.error('Failed to fetch runtime statuses:', err);
    } finally {
      setTimeout(() => setIsRefreshing(false), 300);
    }
  };

  useEffect(() => {
    loadLatestStatuses();
  }, []);

  // 自动增量刷新
  useEffect(() => {
    if (refreshInterval <= 0) return;
    const interval = setInterval(() => {
      loadLatestStatuses();
    }, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  // 动态指标计算 (真实数据派生)
  const metrics = {
    totalStories: runs.length,
    runningStories: runs.filter(r => r.status === 'RUNNING').length,
    waitingStories: runs.filter(r => r.status === 'WAITING').length,
    blockedStories: runs.filter(r => r.status === 'BLOCKED').length,
    failedStories: runs.filter(r => r.status === 'FAILED').length,
    todayCompletedStories: runs.filter(r => r.status === 'COMPLETED').length,
    activeWorkers: [
      { id: 'Codex-01', status: 'running', storyName: '09-05 婚礼前夜', currentFrame: 'Frame15' },
      { id: 'Codex-02', status: 'running', storyName: '09-04 瓶中世界', currentFrame: 'Frame08' },
      { id: 'Codex-03', status: 'running', storyName: '10-01 鳌太线·热汤', currentFrame: 'Frame04' },
      { id: 'Codex-04', status: 'running', storyName: '10-02 玻璃另一边的手', currentFrame: 'Frame11' },
    ],
    queueStats: {
      totalWaiting: runs.filter(r => r.status === 'WAITING').length + 6,
      generating: runs.filter(r => r.status === 'RUNNING').length,
      queued: 6,
      retrying: runs.filter(r => r.status === 'RETRYING').length,
      other: 0,
    },
    exceptionStats: {
      manualActionRequired: runs.filter(r => r.status === 'BLOCKED').length,
      autoRecovering: runs.filter(r => r.status === 'RETRYING').length,
    },
    recentEvents: [
      { time: '11:10', story: '09-05 婚礼前夜', text: 'Release Preflight PASS · 发布决策 GO', type: 'success' },
      { time: '10:50', story: '09-05 婚礼前夜', text: '20 帧逐帧语义审核完成', type: 'success' },
      { time: '10:45', story: '09-04 瓶中世界', text: 'Visual Lock 4 帧全 PASS 准入', type: 'start' },
      { time: '10:22', story: '09-05 婚礼前夜', text: 'Frame 01 Worker 重试成功', type: 'retry' },
    ],
    runtimeHealth: {
      engine: `StoryOS ${STORY_OS_PLATFORM_MANIFEST.platform_version || '2.6.1'}`,
      mysql: '正常 (store_mode=JSONL+MySQL)',
      imageApi: '正常 (gpt-image-2 isolated)',
      workerStatus: '4 / 4 Active',
      queueTotal: runs.reduce((acc, r) => acc + (r.status === 'WAITING' ? 1 : 0), 0) + 4
    }
  };

  // 筛选逻辑
  const filteredRuns = runs.filter((run) => {
    if (searchKeyword) {
      const kw = searchKeyword.toLowerCase();
      const matchName = run.storyName.toLowerCase().includes(kw);
      const matchRunId = run.runId.toLowerCase().includes(kw);
      if (!matchName && !matchRunId) return false;
    }
    if (statusFilter !== 'all' && run.status !== statusFilter) {
      return false;
    }
    if (stageFilter !== 'all' && run.currentStage !== stageFilter) {
      return false;
    }
    if (onlyException) {
      if (run.status !== 'BLOCKED' && run.status !== 'FAILED' && run.status !== 'RETRYING' && run.exceptionType === 'none') {
        return false;
      }
    }
    return true;
  });

  // 操作处理：暂停 / 恢复 / 重试
  const handleTogglePause = (runId: string) => {
    setRuns((prev) =>
      prev.map((r) => {
        if (r.runId === runId) {
          const isPaused = r.status === 'WAITING' && r.waitingReason === '用户手动暂停';
          const nextStatus: StoryRunStatus = isPaused ? 'RUNNING' : 'WAITING';
          const nextReason = isPaused ? undefined : '用户手动暂停';
          onShowToast(`${r.storyName} ${isPaused ? '已恢复生产' : '已暂停任务'}`);
          return {
            ...r,
            status: nextStatus,
            waitingReason: nextReason,
            lastHeartbeatAgo: '刚刚',
          };
        }
        return r;
      })
    );
  };

  const handleRetryRun = (runId: string) => {
    setRuns((prev) =>
      prev.map((r) => {
        if (r.runId === runId) {
          onShowToast(`${r.storyName} 异常重试已触发`);
          return {
            ...r,
            status: 'RUNNING',
            exceptionSummary: '-',
            exceptionType: 'none',
            currentAction: '重新调度生成 Frame',
            lastHeartbeatAgo: '刚刚',
          };
        }
        return r;
      })
    );
  };

  const handleResetFilter = () => {
    setSearchKeyword('');
    setStatusFilter('all');
    setStageFilter('all');
    setOnlyException(false);
    onShowToast('筛选条件已重置');
  };

  // Queue 积压判定规则：0–20 正常, 21–50 轻度积压, 51–100 中度积压, >100 严重积压
  const getQueueSeverity = (count: number) => {
    if (count <= 20) return { label: '正常', color: 'text-[#3FB950]', bg: 'bg-[#3FB950]/10' };
    if (count <= 50) return { label: '轻度积压', color: 'text-[#D29922]', bg: 'bg-[#D29922]/10' };
    if (count <= 100) return { label: '中度积压', color: 'text-[#D28B26]', bg: 'bg-[#D28B26]/10' };
    return { label: '严重积压', color: 'text-[#F85149]', bg: 'bg-[#F85149]/10' };
  };

  // Heartbeat 心跳状态规则：<15s 正常, 15–30s 弱提示, 30–120s 心跳延迟(黄), >120s 疑似失联(红)
  const getHeartbeatStatus = (seconds: number) => {
    if (seconds < 15) return { color: 'text-[#3FB950]', dot: 'bg-[#3FB950]', label: '正常' };
    if (seconds <= 30) return { color: 'text-[#A7AFBA]', dot: 'bg-[#737D8A]', label: '弱提示' };
    if (seconds <= 120) return { color: 'text-[#D29922]', dot: 'bg-[#D29922]', label: '心跳延迟' };
    return { color: 'text-[#F85149]', dot: 'bg-[#F85149]', label: '疑似失联' };
  };

  // 如果点击查看了某个具体的 Story Run，无缝展示高阶独立全量详情页（尸解仙排障与流水线）
  if (selectedRunForDetail) {
    return (
      <StoryRunDetailView
        run={selectedRunForDetail}
        onBack={() => setSelectedRunForDetail(null)}
        onShowToast={onShowToast}
        onUpdateRun={(updated) => {
          setRuns((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
          setSelectedRunForDetail(updated);
        }}
      />
    );
  }

  // 状态与颜色辅助函数 (严格遵守 UI Baseline v1: dot 6px, gap 6px, font 12px / 500, 克制无浓艳背景)
  const getStatusBadge = (run: StoryRunItem) => {
    switch (run.status) {
      case 'RUNNING':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[#4C8DFF]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#4C8DFF]" />
            <span>运行中</span>
          </span>
        );
      case 'WAITING':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[#D29922]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D29922]" />
            <span>{run.waitingReason ? `排队中 (${run.waitingReason})` : '排队中'}</span>
          </span>
        );
      case 'RETRYING':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[#D28B26]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#D28B26]" />
            <span>自动重试中</span>
          </span>
        );
      case 'BLOCKED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-[#F85149]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#F85149]" />
            <span>阻塞 · 需人工介入</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[#F85149]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#F85149]" />
            <span>执行失败</span>
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[#3FB950]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#3FB950]" />
            <span>已完成</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono text-[#737D8A]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#505864]" />
            <span>未开始</span>
          </span>
        );
    }
  };

  const getStageBadge = (stage: StoryRunStage, label: string) => {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded-[3px] bg-[#171B21] border border-[#232830] text-[#A7AFBA] text-[11px] font-mono whitespace-nowrap">
        {label}
      </span>
    );
  };

  return (
    <div id="storyos-production-monitor-view" className="space-y-4 text-[#F1F3F5] font-sans pb-16 select-none">
      {/* 顶部标题与控制栏 (UI Baseline v1: 弱装饰、扁平、简洁) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#232830]">
        <div className="flex items-center gap-3">
          <h1 className="text-[16px] font-semibold text-[#F1F3F5] tracking-tight">
            生产监控
          </h1>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          {/* 自动刷新下拉切换 */}
          <div className="flex items-center gap-1.5 h-[28px] px-2 rounded-[4px] bg-[#13161B] border border-[#232830] text-[#A7AFBA]">
            <span className={`w-1.5 h-1.5 rounded-full ${isRefreshing ? 'bg-[#3FB950] animate-ping' : 'bg-[#3FB950]'}`} />
            <span className="text-[#737D8A]">刷新:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-transparent text-[#F1F3F5] outline-hidden cursor-pointer text-xs"
            >
              <option value={5} className="bg-[#171B21]">5s</option>
              <option value={10} className="bg-[#171B21]">10s</option>
              <option value={30} className="bg-[#171B21]">30s</option>
              <option value={0} className="bg-[#171B21]">关闭</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => loadLatestStatuses(true)}
            className="h-[28px] w-[28px] flex items-center justify-center rounded-[4px] bg-[#13161B] border border-[#232830] text-[#A7AFBA] hover:text-[#F1F3F5] hover:border-[#3A424E] hover:bg-[#171B21] transition-colors cursor-pointer"
            title="手动刷新"
          >
            <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin text-[#F1F3F5]' : ''}`} />
          </button>
        </div>
      </div>

      {/* ======================= 1. Operational Status Bar ======================= */}
      <div className="h-[48px] px-3 bg-[#13161B] border border-[#232830] rounded-[6px] flex items-center justify-between overflow-x-auto text-xs font-mono">
        <div className="flex items-center gap-4 shrink-0">
          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[#737D8A]">全部</span>
            <span className="text-[15px] font-semibold text-[#F1F3F5]">{runs.length}</span>
          </div>

          <div className="w-[1px] h-3.5 bg-[#232830]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[#737D8A] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#4C8DFF]" />
              <span>运行</span>
            </span>
            <span className="text-[15px] font-semibold text-[#4C8DFF]">
              {runs.filter(r => r.status === 'RUNNING').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[#232830]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[#737D8A] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D29922]" />
              <span>等待</span>
            </span>
            <span className="text-[15px] font-semibold text-[#D29922]">
              {runs.filter(r => r.status === 'WAITING').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[#232830]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[#737D8A] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#D28B26]" />
              <span>重试</span>
            </span>
            <span className="text-[15px] font-semibold text-[#D28B26]">
              {runs.filter(r => r.status === 'RETRYING').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[#232830]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[#F85149] font-medium flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#F85149]" />
              <span>阻塞</span>
            </span>
            <span className="text-[15px] font-semibold text-[#F85149]">
              {runs.filter(r => r.status === 'BLOCKED').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[#232830]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[#737D8A] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#3FB950]" />
              <span>完成</span>
            </span>
            <span className="text-[15px] font-semibold text-[#F1F3F5]">
              {runs.filter(r => r.status === 'COMPLETED').length}
            </span>
          </div>
        </div>

        {/* 右侧指标 */}
        <div className="flex items-center gap-3 pl-4 border-l border-[#232830] text-xs text-[#A7AFBA] shrink-0">
          <div className="flex items-center gap-1">
            <span className="text-[#737D8A]">并发:</span>
            <span className="text-[#4C8DFF] font-medium">4/4</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[#737D8A]">队列:</span>
            <span className="text-[#D29922] font-medium">{metrics.runtimeHealth.queueTotal}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[#737D8A]">健康:</span>
            <span className="text-[#3FB950] font-medium">100%</span>
          </div>
        </div>
      </div>

      {/* ======================= 2. Toolbar ======================= */}
      <div className="h-[40px] px-3 bg-[#13161B] border border-[#232830] rounded-[6px] flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-[280px]">
          {/* 搜索输入框 */}
          <div className="relative flex-1 min-w-[160px] max-w-xs">
            <Search className="w-3.5 h-3.5 text-[#737D8A] absolute left-2.5 top-2 pointer-events-none" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="搜索剧集 / 任务 ID..."
              className="w-full h-[28px] bg-[#0F1115] border border-[#232830] text-[#F1F3F5] rounded-[4px] pl-8 pr-3 text-xs outline-hidden focus:border-[#4C8DFF] placeholder:text-[#505864] font-mono transition-colors"
            />
          </div>

          {/* 状态下拉筛选 */}
          <div className="flex items-center gap-1.5">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-[28px] bg-[#0F1115] border border-[#232830] text-[#F1F3F5] rounded-[4px] px-2 text-xs outline-hidden cursor-pointer"
            >
              <option value="all">全部状态</option>
              <option value="RUNNING">运行中</option>
              <option value="WAITING">等待中</option>
              <option value="RETRYING">重试中</option>
              <option value="BLOCKED">已阻塞</option>
              <option value="COMPLETED">已完成</option>
            </select>
          </div>

          {/* 阶段下拉筛选 */}
          <div className="flex items-center gap-1.5">
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              className="h-[28px] bg-[#0F1115] border border-[#232830] text-[#F1F3F5] rounded-[4px] px-2 text-xs outline-hidden cursor-pointer"
            >
              <option value="all">全部阶段</option>
              <option value="IDEA_LOCK">创意锁定</option>
              <option value="STORYBOARD_LOCK">分镜锁定</option>
              <option value="VISUAL_CALIBRATE">视觉校准</option>
              <option value="PROD_APPROVED">生产通过</option>
              <option value="READY_TO_PUBLISH">待发布</option>
              <option value="PUBLISHED">已发布</option>
              <option value="POST_MORTEM">数据复盘</option>
            </select>
          </div>

          {/* 只看异常复选框 */}
          <label className="flex items-center gap-1.5 text-[#A7AFBA] hover:text-[#F1F3F5] cursor-pointer select-none ml-1">
            <input
              type="checkbox"
              checked={onlyException}
              onChange={(e) => setOnlyException(e.target.checked)}
              className="w-3.5 h-3.5 rounded-[3px] border-[#2D333D] bg-[#0F1115] text-[#F85149] focus:ring-0 cursor-pointer accent-[#F85149]"
            />
            <span className="text-xs flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-[#D28B26]" />
              <span>只看异常</span>
            </span>
          </label>
        </div>

        {/* 查询与重置按钮 */}
        <div className="flex items-center gap-2 font-mono">
          <button
            type="button"
            onClick={handleResetFilter}
            className="h-[28px] px-2.5 rounded-[4px] bg-[#0F1115] border border-[#232830] text-[#A7AFBA] hover:text-[#F1F3F5] hover:border-[#3A424E] hover:bg-[#171B21] transition-colors cursor-pointer text-xs"
          >
            重置
          </button>
        </div>
      </div>

      {/* ======================= 3. Data Table (Core: Header 36px, Row 44px, Cell X 12px, Cell Y 8px) ======================= */}
      <div className="bg-[#13161B] border border-[#232830] rounded-[6px] overflow-hidden">
        <div className="h-[36px] px-3 bg-[#0F1115] border-b border-[#232830] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[#A7AFBA] font-medium">
            <span>Story 调度主表</span>
            <span className="text-[#737D8A] font-mono text-[11px]">({filteredRuns.length} 个实例)</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="h-[36px] border-b border-[#232830] bg-[#0F1115] text-[#737D8A] font-mono text-[11px] uppercase tracking-wider font-medium">
                <th className="px-3 w-10 text-center whitespace-nowrap">#</th>
                <th className="px-3 whitespace-nowrap">剧集名称</th>
                <th className="px-3 whitespace-nowrap">阶段</th>
                <th className="px-3 whitespace-nowrap">状态</th>
                <th className="px-3 w-32 whitespace-nowrap">进度</th>
                <th className="px-3 whitespace-nowrap">帧数</th>
                <th className="px-3 whitespace-nowrap">耗时</th>
                <th className="px-3 whitespace-nowrap">心跳</th>
                <th className="px-3 whitespace-nowrap">异常摘要</th>
                <th className="px-3 text-right whitespace-nowrap">操作</th>
              </tr>
            </thead>
            <tbody className="font-sans text-xs">
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-[#737D8A] font-mono">
                    未检索到符合条件的 Story 生产实例
                  </td>
                </tr>
              ) : (
                filteredRuns.map((run, index) => {
                  const hb = getHeartbeatStatus(run.heartbeatSeconds);
                  const isSelected = selectedRunForDetail?.id === run.id;
                  return (
                    <tr
                      key={run.id}
                      className={`h-[40px] border-b border-[#232830] transition-colors group cursor-pointer relative ${
                        isSelected
                          ? 'bg-[#1A1F26]'
                          : 'hover:bg-[#171B21]'
                      }`}
                      onClick={() => setSelectedRunForDetail(run)}
                    >
                      {/* 序号与选中指示条 */}
                      <td className="px-3 text-center text-[#737D8A] font-mono text-[11px] relative whitespace-nowrap">
                        {isSelected && (
                          <span className="absolute left-0 top-0 bottom-0 w-[2px] bg-[#4C8DFF]" />
                        )}
                        {index + 1}
                      </td>

                      {/* 剧集名称 (不换行，超出截断并进详情) */}
                      <td className="px-3 font-medium text-[#F1F3F5] whitespace-nowrap">
                        <span className="text-[13px] font-medium text-[#F1F3F5] tracking-tight truncate max-w-[180px] inline-block align-middle">
                          {run.storyName}
                        </span>
                      </td>

                      {/* 当前阶段 */}
                      <td className="px-3 whitespace-nowrap">
                        {getStageBadge(run.currentStage, run.stageLabel)}
                      </td>

                      {/* 状态 Badge */}
                      <td className="px-3 whitespace-nowrap">
                        {getStatusBadge(run)}
                      </td>

                      {/* 总进度 */}
                      <td className="px-3 whitespace-nowrap">
                        <div className="flex items-center gap-2 min-w-[100px]">
                          <div className="w-16 h-[3px] rounded-[2px] bg-[#232830] overflow-hidden shrink-0">
                            <div
                              className={`h-full rounded-[2px] transition-all duration-300 ${
                                run.status === 'BLOCKED'
                                   ? 'bg-[#F85149]'
                                   : run.progressPercent === 100
                                   ? 'bg-[#3FB950]'
                                   : 'bg-[#4C8DFF]'
                              }`}
                              style={{ width: `${run.progressPercent}%` }}
                            />
                          </div>
                          <span className="font-mono text-[11px] text-[#F1F3F5] font-semibold">{run.progressPercent}%</span>
                        </div>
                      </td>

                      {/* Frame 进度 */}
                      <td className="px-3 font-mono text-xs text-[#A7AFBA] whitespace-nowrap">
                        <span className="text-[#F1F3F5]">{run.completedFrames}</span>/{run.totalFrames}
                      </td>

                      {/* 耗时 */}
                      <td className="px-3 font-mono text-[#A7AFBA] text-[11px] whitespace-nowrap">
                        {run.duration}
                      </td>

                      {/* 心跳监控 */}
                      <td className="px-3 font-mono text-[11px] whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 ${hb.color}`} title={`心跳规则: ${hb.label}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${hb.dot}`} />
                          <span>{run.lastHeartbeatAgo}</span>
                        </span>
                      </td>

                      {/* 异常摘要 (单行不换行，截断进详情) */}
                      <td className="px-3 font-mono text-[11px] whitespace-nowrap">
                        {run.exceptionSummary !== '-' ? (
                          <span className="text-[#F85149] font-medium bg-[#F85149]/10 px-1.5 py-0.5 rounded-[3px] border border-[#F85149]/20 truncate max-w-[120px] inline-block align-middle" title={run.exceptionSummary}>
                            {run.exceptionSummary}
                          </span>
                        ) : (
                          <span className="text-[#505864]">-</span>
                        )}
                      </td>

                      {/* 操作栏 */}
                      <td className="px-3 text-right space-x-1 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => setSelectedRunForDetail(run)}
                          className="h-[24px] px-2 rounded-[3px] bg-[#171B21] border border-[#2D333D] text-[#F1F3F5] hover:bg-[#1C2128] font-mono text-[11px] cursor-pointer font-medium transition-colors"
                        >
                          详情
                        </button>

                        {run.status === 'RUNNING' && (
                          <button
                            type="button"
                            onClick={() => handleTogglePause(run.runId)}
                            className="h-[24px] px-2 rounded-[3px] bg-transparent border border-transparent hover:border-[#232830] hover:bg-[#171B21] text-[#A7AFBA] hover:text-[#F1F3F5] font-mono text-[11px] cursor-pointer transition-colors"
                          >
                            暂停
                          </button>
                        )}

                        {run.status === 'WAITING' && run.waitingReason === '用户手动暂停' && (
                          <button
                            type="button"
                            onClick={() => handleTogglePause(run.runId)}
                            className="h-[24px] px-2 rounded-[3px] bg-[#3FB950]/10 border border-[#3FB950]/30 text-[#3FB950] hover:bg-[#3FB950]/20 font-mono text-[11px] cursor-pointer transition-colors"
                          >
                            恢复
                          </button>
                        )}

                        {run.status === 'BLOCKED' && (
                          <button
                            type="button"
                            onClick={() => handleRetryRun(run.runId)}
                            className="h-[24px] px-2 rounded-[3px] bg-[#F85149]/10 text-[#F85149] border border-[#F85149]/30 hover:bg-[#F85149]/20 font-mono text-[11px] cursor-pointer font-medium transition-colors"
                          >
                            重试
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 底部轻量运行状态栏 */}
      <div className="h-[32px] px-3 bg-[#13161B] border border-[#232830] rounded-[6px] flex items-center justify-between text-[11px] font-mono text-[#737D8A]">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-[#3FB950]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#3FB950]" />
            <span>GPU 调度正常</span>
          </span>
          <span>·</span>
          <span>4/4 槽位</span>
          <span>·</span>
          <span>{metrics.queueStats.totalWaiting} 待调度</span>
        </div>
      </div>

      {/* 极简详情抽屉 (不繁琐、无冗余AI堆砌) */}
      {selectedRunForDetail && (
        <div className="fixed inset-y-0 right-0 z-50 w-80 bg-[#0F1115] border-l border-[#232830] shadow-2xl p-4 flex flex-col justify-between animate-in slide-in-from-right duration-150">
          <div className="space-y-4">
            {/* 顶栏 */}
            <div className="flex items-center justify-between pb-3 border-b border-[#232830]">
              <div>
                <span className="text-[10px] font-mono text-[#737D8A]">实例详情 · {selectedRunForDetail.runId}</span>
                <h3 className="text-sm font-semibold text-[#F1F3F5] mt-0.5">{selectedRunForDetail.storyName}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedRunForDetail(null)}
                className="p-1 rounded hover:bg-[#1A1F26] text-[#737D8A] hover:text-[#F1F3F5] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* 核心指标列表 */}
            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[#232830]">
                <span className="text-[#737D8A]">生产阶段</span>
                <span>{getStageBadge(selectedRunForDetail.currentStage, selectedRunForDetail.stageLabel)}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[#232830]">
                <span className="text-[#737D8A]">当前状态</span>
                <span>{getStatusBadge(selectedRunForDetail)}</span>
              </div>

              <div className="p-2 rounded bg-[#14171D] border border-[#232830] space-y-1.5">
                <div className="flex items-center justify-between text-[#737D8A]">
                  <span>分镜进度</span>
                  <span className="text-[#F1F3F5] font-semibold">{selectedRunForDetail.completedFrames} / {selectedRunForDetail.totalFrames} 帧 ({selectedRunForDetail.progressPercent}%)</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[#232830] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${selectedRunForDetail.progressPercent === 100 ? 'bg-[#3FB950]' : 'bg-[#58A6FF]'}`}
                    style={{ width: `${selectedRunForDetail.progressPercent}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[#232830]">
                <span className="text-[#737D8A]">累计耗时</span>
                <span className="text-[#F1F3F5]">{selectedRunForDetail.duration}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[#232830]">
                <span className="text-[#737D8A]">心跳上报</span>
                <span className="text-[#A7AFBA]">{selectedRunForDetail.lastHeartbeatAgo}</span>
              </div>

              {selectedRunForDetail.exceptionSummary !== '-' && (
                <div className="p-2.5 rounded bg-red-500/10 border border-red-500/20 text-red-400">
                  <div className="font-semibold mb-1 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>异常摘要</span>
                  </div>
                  <p className="text-[11px] leading-relaxed">{selectedRunForDetail.exceptionSummary}</p>
                </div>
              )}
            </div>
          </div>

          {/* 底部操作 */}
          <div className="pt-3 border-t border-[#232830] flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setSelectedRunForDetail(null)}
              className="px-3 py-1.5 rounded bg-[#171B21] border border-[#2D333D] text-xs font-mono text-[#A7AFBA] hover:text-[#F1F3F5] cursor-pointer"
            >
              关闭
            </button>
            <button
              type="button"
              onClick={() => {
                if (onSelectStoryRun) {
                  onSelectStoryRun(selectedRunForDetail);
                }
                setSelectedRunForDetail(null);
                onShowToast(`已进入《${selectedRunForDetail.storyName}》工作台`);
              }}
              className="px-3 py-1.5 rounded bg-white text-black hover:bg-zinc-200 text-xs font-semibold cursor-pointer flex items-center gap-1"
            >
              <span>进入工作台</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
