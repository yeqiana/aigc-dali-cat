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
import { MOCK_STORY_RUNS, MOCK_MONITOR_METRICS } from '../../mockMonitorData';
import { StoryRunDetailView } from './StoryRunDetailView';
import { StatusBadge } from '../StatusBadge';

interface ProductionMonitorViewProps {
  onSelectStoryRun?: (run: StoryRunItem) => void;
  onShowToast: (msg: string) => void;
}

export const ProductionMonitorView: React.FC<ProductionMonitorViewProps> = ({
  onSelectStoryRun,
  onShowToast,
}) => {
  // 运行数据状态
  const [runs, setRuns] = useState<StoryRunItem[]>(MOCK_STORY_RUNS);
  const [metrics, setMetrics] = useState(MOCK_MONITOR_METRICS);

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

  // 模拟增量自动刷新
  useEffect(() => {
    if (refreshInterval <= 0) return;
    const interval = setInterval(() => {
      setIsRefreshing(true);
      setTimeout(() => setIsRefreshing(false), 300);
    }, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

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
    if (count <= 20) return { label: '正常', color: 'text-[var(--success)]', bg: 'bg-[var(--success)]/10' };
    if (count <= 50) return { label: '轻度积压', color: 'text-[var(--warning)]', bg: 'bg-[var(--warning)]/10' };
    if (count <= 100) return { label: '中度积压', color: 'text-[var(--warning)]', bg: 'bg-[var(--warning)]/10' };
    return { label: '严重积压', color: 'text-[var(--danger)]', bg: 'bg-[var(--danger)]/10' };
  };

  // Heartbeat 心跳状态规则：<15s 正常, 15–30s 弱提示, 30–120s 心跳延迟(黄), >120s 疑似失联(红)
  const getHeartbeatStatus = (seconds: number) => {
    if (seconds < 15) return { color: 'text-[var(--success)]', dot: 'bg-[var(--success)]', label: '正常' };
    if (seconds <= 30) return { color: 'text-[var(--text-secondary)]', dot: 'bg-[var(--text-tertiary)]', label: '弱提示' };
    if (seconds <= 120) return { color: 'text-[var(--warning)]', dot: 'bg-[var(--warning)]', label: '心跳延迟' };
    return { color: 'text-[var(--danger)]', dot: 'bg-[var(--danger)]', label: '疑似失联' };
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

  const getStageBadge = (stage: StoryRunStage, label: string) => {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded-[3px] bg-[var(--bg-subtle)] border border-[var(--border-subtle)] text-[var(--text-secondary)] text-[11px] font-mono whitespace-nowrap">
        {label}
      </span>
    );
  };

  return (
    <div id="storyos-production-monitor-view" className="space-y-4 text-[var(--text-primary)] font-sans pb-16 select-none">
      {/* 顶部标题与控制栏 (UI Baseline v1: 弱装饰、扁平) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-3">
          <h1 className="text-[18px] font-semibold text-[var(--text-primary)] tracking-tight flex items-center gap-2">
            <span>StoryOS 生产监控台</span>
            <span className="text-[11px] px-1.5 py-0.5 rounded-[4px] bg-[var(--bg-subtle)] text-[var(--text-secondary)] border border-[var(--border-normal)] font-mono font-normal">
              Console v1.0
            </span>
          </h1>
          <span className="text-xs text-[var(--text-tertiary)] hidden md:inline">
            Dense Operations Console · 高密度生产调度
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          {/* 自动刷新下拉切换 */}
          <div className="flex items-center gap-1.5 h-[32px] px-2 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-secondary)]">
            <span className={`w-1.5 h-1.5 rounded-full ${isRefreshing ? 'bg-[var(--success)] animate-ping' : 'bg-[var(--success)]'}`} />
            <span className="text-[var(--text-tertiary)]">刷新:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-transparent text-[var(--text-primary)] outline-hidden cursor-pointer"
            >
              <option value={5} className="bg-[var(--bg-subtle)]">5s</option>
              <option value={10} className="bg-[var(--bg-subtle)]">10s</option>
              <option value={30} className="bg-[var(--bg-subtle)]">30s</option>
              <option value={0} className="bg-[var(--bg-subtle)]">关闭</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => {
              setIsRefreshing(true);
              setTimeout(() => {
                setIsRefreshing(false);
                onShowToast('生产监控数据已同步刷新');
              }, 400);
            }}
            className="h-[32px] w-[32px] flex items-center justify-center rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-subtle)] transition-colors cursor-pointer"
            title="手动刷新"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-[var(--text-primary)]' : ''}`} />
          </button>
        </div>
      </div>

      {/* ======================= 1. Operational Status Bar (56–64px，严禁 6 张大 Card 堆砌) ======================= */}
      <div className="h-[56px] px-4 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] flex items-center justify-between overflow-x-auto text-xs font-mono">
        <div className="flex items-center gap-6 shrink-0">
          <div className="flex items-baseline gap-2">
            <span className="text-[11px] text-[var(--text-tertiary)]">全部任务</span>
            <span className="text-[18px] font-semibold text-[var(--text-primary)]">{runs.length}</span>
          </div>

          <div className="w-[1px] h-4 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-2">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)]" />
              <span>运行中</span>
            </span>
            <span className="text-[18px] font-semibold text-[var(--primary)]">
              {runs.filter(r => r.status === 'RUNNING').length}
            </span>
          </div>

          <div className="w-[1px] h-4 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-2">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
              <span>等待中</span>
            </span>
            <span className="text-[18px] font-semibold text-[var(--warning)]">
              {runs.filter(r => r.status === 'WAITING').length}
            </span>
          </div>

          <div className="w-[1px] h-4 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-2">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
              <span>重试中</span>
            </span>
            <span className="text-[18px] font-semibold text-[var(--warning)]">
              {runs.filter(r => r.status === 'RETRYING').length}
            </span>
          </div>

          <div className="w-[1px] h-4 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-2">
            <span className="text-[11px] text-[var(--danger)] font-medium flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)]" />
              <span>阻塞 (需人工)</span>
            </span>
            <span className="text-[18px] font-semibold text-[var(--danger)]">
              {runs.filter(r => r.status === 'BLOCKED').length}
            </span>
          </div>

          <div className="w-[1px] h-4 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-2">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
              <span>今日完成</span>
            </span>
            <span className="text-[18px] font-semibold text-[var(--text-primary)]">
              {runs.filter(r => r.status === 'COMPLETED').length + metrics.todayCompletedStories}
            </span>
          </div>
        </div>

        {/* 右侧紧凑型 Worker & Queue 指标 */}
        <div className="flex items-center gap-4 pl-6 border-l border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--text-tertiary)]">并发:</span>
            <span className="text-[var(--primary)] font-semibold">4 / 4 Slots</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--text-tertiary)]">队列:</span>
            <span className="text-[var(--warning)] font-semibold">{metrics.runtimeHealth.queueTotal} Queued</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--text-tertiary)]">底层健康:</span>
            <span className="text-[var(--success)]">100% OK</span>
          </div>
        </div>
      </div>

      {/* ======================= 2. Toolbar (高度 44–48px，控件 32px，radius 4px) ======================= */}
      <div className="min-h-[44px] px-3 py-1.5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] flex flex-col xl:flex-row xl:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-0 w-full xl:w-auto overflow-x-auto">
          {/* 搜索输入框 */}
          <div className="relative flex-1 min-w-[160px] max-w-xs">
            <Search className="w-3.5 h-3.5 text-[var(--text-tertiary)] absolute left-2.5 top-2.5 pointer-events-none" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="搜索剧集名称 / 任务 ID..."
              className="w-full h-[32px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-[4px] pl-8 pr-3 text-xs outline-hidden focus:border-[var(--primary)] placeholder:text-[var(--text-disabled)] font-mono transition-colors"
            />
          </div>

          {/* 状态下拉筛选 */}
          <div className="flex items-center gap-1.5">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-[32px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-[4px] px-2.5 text-xs outline-hidden cursor-pointer"
            >
              <option value="all">全部状态</option>
              <option value="RUNNING">RUNNING (运行中)</option>
              <option value="WAITING">WAITING (等待中)</option>
              <option value="RETRYING">RETRYING (重试中)</option>
              <option value="BLOCKED">BLOCKED (已阻塞)</option>
              <option value="COMPLETED">COMPLETED (已完成)</option>
            </select>
          </div>

          {/* 阶段下拉筛选 */}
          <div className="flex items-center gap-1.5">
            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              className="h-[32px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-[4px] px-2.5 text-xs outline-hidden cursor-pointer"
            >
              <option value="all">全部阶段</option>
              <option value="CREATE">Create</option>
              <option value="STORY_LOCK">Story Lock</option>
              <option value="STORYBOARD">Storyboard</option>
              <option value="CHARACTER_CONTRACT">Character Contract</option>
              <option value="VISUAL_LOCK">Visual Lock</option>
              <option value="PRODUCTION">Production</option>
              <option value="REVIEW">Review</option>
              <option value="COMPLETED">Completed</option>
            </select>
          </div>

          {/* 只看异常复选框 */}
          <label className="flex items-center gap-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer select-none ml-2">
            <input
              type="checkbox"
              checked={onlyException}
              onChange={(e) => setOnlyException(e.target.checked)}
              className="w-3.5 h-3.5 rounded-[3px] border-[var(--border-normal)] bg-[var(--bg-workspace)] text-[var(--danger)] focus:ring-0 cursor-pointer accent-[var(--danger)]"
            />
            <span className="text-xs flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-[var(--warning)]" />
              <span>只看异常</span>
            </span>
          </label>
        </div>

        {/* 查询与重置按钮 */}
        <div className="flex items-center gap-2 font-mono shrink-0 self-end xl:self-auto">
          <button
            type="button"
            onClick={handleResetFilter}
            className="h-[32px] px-3 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-subtle)] transition-colors cursor-pointer text-xs"
          >
            重置
          </button>
          <button
            type="button"
            onClick={() => onShowToast(`已过滤 ${filteredRuns.length} 项 Story 生产实例`)}
            className="h-[32px] px-3 rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] text-[var(--text-primary)] hover:bg-[var(--bg-muted)] transition-colors cursor-pointer text-xs flex items-center gap-1.5 font-medium"
          >
            <Filter className="w-3 h-3 text-[var(--primary)]" />
            <span>应用筛选</span>
          </button>
        </div>
      </div>

      {/* ======================= 3. Data Table (Core: Header 36px, Row 44px, Cell X 12px, Cell Y 8px) ======================= */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] overflow-hidden">
        <div className="h-[36px] px-3 bg-[var(--bg-workspace)] border-b border-[var(--border-subtle)] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[var(--text-secondary)] font-medium">
            <span>Story 调度主表</span>
            <span className="text-[var(--text-tertiary)] font-mono text-[11px]">({filteredRuns.length} 个实例)</span>
          </div>
          <div className="text-[11px] text-[var(--text-tertiary)] font-mono">
            加权总进度: 前置 (35%) + 生产帧 (45%) + 审核发布 (20%)
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="h-[36px] border-b border-[var(--border-subtle)] bg-[var(--bg-workspace)] text-[var(--text-tertiary)] font-mono text-[11px] uppercase tracking-wider font-medium">
                <th className="px-3 w-10 text-center">#</th>
                <th className="px-3">剧集名称</th>
                <th className="px-3">阶段</th>
                <th className="px-3">状态</th>
                <th className="px-3 w-36">总进度</th>
                <th className="px-3">帧数</th>
                <th className="px-3">当前动作</th>
                <th className="px-3">Run ID</th>
                <th className="px-3">耗时</th>
                <th className="px-3">心跳</th>
                <th className="px-3">异常摘要</th>
                <th className="px-3 text-right">操作</th>
              </tr>
            </thead>
            <tbody className="font-sans text-xs">
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={12} className="py-12 text-center text-[var(--text-tertiary)] font-mono">
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
                      className={`h-[42px] border-b border-[var(--border-subtle)] transition-colors group cursor-pointer relative ${
                        isSelected
                          ? 'bg-[var(--bg-muted)]'
                          : 'hover:bg-[var(--bg-subtle)]'
                      }`}
                      onClick={() => setSelectedRunForDetail(run)}
                    >
                      {/* 序号与选中指示条 */}
                      <td className="px-3 text-center text-[var(--text-tertiary)] font-mono text-[11px] relative">
                        {isSelected && (
                          <span className="absolute left-0 top-0 bottom-0 w-[2px] bg-[var(--primary)]" />
                        )}
                        {index + 1}
                      </td>

                      {/* 剧集名称 */}
                      <td className="px-3 font-medium text-[var(--text-primary)]">
                        <div className="flex items-center gap-2">
                          <span className="text-[13px] font-medium text-[var(--text-primary)] tracking-tight truncate max-w-[160px]">
                            {run.storyName}
                          </span>
                        </div>
                      </td>

                      {/* 当前阶段 */}
                      <td className="px-3">
                        {getStageBadge(run.currentStage, run.stageLabel)}
                      </td>

                      {/* 状态 Badge (Dot + 文字，克制无大胶囊) */}
                      <td className="px-3 whitespace-nowrap">
                        <StatusBadge
                          status={run.status}
                          label={run.status === 'WAITING' && run.waitingReason ? `Waiting (${run.waitingReason})` : undefined}
                        />
                      </td>

                      {/* 总进度 */}
                      <td className="px-3">
                        <div className="space-y-1 min-w-[100px]">
                          <div className="flex items-center justify-between font-mono text-[11px] text-[var(--text-secondary)]">
                            <span className="text-[var(--text-primary)] font-semibold">{run.progressPercent}%</span>
                          </div>
                          <div className="w-full h-[3px] rounded-[2px] bg-[var(--border-subtle)] overflow-hidden">
                            <div
                              className={`h-full rounded-[2px] transition-all duration-300 ${
                                run.status === 'BLOCKED'
                                   ? 'bg-[var(--danger)]'
                                   : run.progressPercent === 100
                                   ? 'bg-[var(--success)]'
                                   : 'bg-[var(--primary)]'
                              }`}
                              style={{ width: `${run.progressPercent}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      {/* Frame 进度 */}
                      <td className="px-3 font-mono text-xs text-[var(--text-secondary)] whitespace-nowrap">
                        <span className="text-[var(--text-primary)]">{run.completedFrames}</span> / {run.totalFrames}
                      </td>

                      {/* 当前动作 */}
                      <td className="px-3 text-xs text-[var(--text-secondary)] font-mono truncate max-w-[130px]" title={run.currentAction}>
                        {run.currentAction}
                      </td>

                      {/* Run ID */}
                      <td className="px-3 font-mono text-[var(--text-tertiary)] text-[11px] whitespace-nowrap">
                        {run.runId}
                      </td>

                      {/* 耗时 */}
                      <td className="px-3 font-mono text-[var(--text-secondary)] text-[11px] whitespace-nowrap">
                        {run.duration}
                      </td>

                      {/* 心跳监控 */}
                      <td className="px-3 font-mono text-[11px] whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 ${hb.color}`} title={`心跳规则: ${hb.label}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${hb.dot}`} />
                          <span>{run.lastHeartbeatAgo}</span>
                        </span>
                      </td>

                      {/* 异常摘要 */}
                      <td className="px-3 font-mono text-[11px]">
                        {run.exceptionSummary !== '-' ? (
                          <span className="text-[var(--danger)] font-medium bg-[var(--danger)]/10 px-1.5 py-0.5 rounded-[3px] border border-[var(--danger)]/20">
                            {run.exceptionSummary}
                          </span>
                        ) : (
                          <span className="text-[var(--text-disabled)]">-</span>
                        )}
                      </td>

                      {/* 操作栏 (Ghost / Secondary 紧凑按钮) */}
                      <td className="px-3 text-right space-x-1.5 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => setSelectedRunForDetail(run)}
                          className="h-[26px] px-2 rounded-[3px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] text-[var(--text-primary)] hover:bg-[var(--bg-muted)] font-mono text-[11px] cursor-pointer font-medium transition-colors"
                        >
                          详情
                        </button>

                        {run.status === 'RUNNING' && (
                          <button
                            type="button"
                            onClick={() => handleTogglePause(run.runId)}
                            className="h-[26px] px-2 rounded-[3px] bg-transparent border border-transparent hover:border-[var(--border-subtle)] hover:bg-[var(--bg-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-mono text-[11px] cursor-pointer transition-colors"
                          >
                            暂停
                          </button>
                        )}

                        {run.status === 'WAITING' && run.waitingReason === '用户手动暂停' && (
                          <button
                            type="button"
                            onClick={() => handleTogglePause(run.runId)}
                            className="h-[26px] px-2 rounded-[3px] bg-[var(--success)]/10 border border-[var(--success)]/30 text-[var(--success)] hover:bg-[var(--success)]/20 font-mono text-[11px] cursor-pointer transition-colors"
                          >
                            恢复
                          </button>
                        )}

                        {run.status === 'BLOCKED' && (
                          <button
                            type="button"
                            onClick={() => handleRetryRun(run.runId)}
                            className="h-[26px] px-2 rounded-[3px] bg-[var(--danger)]/10 text-[var(--danger)] border border-[var(--danger)]/30 hover:bg-[var(--danger)]/20 font-mono text-[11px] cursor-pointer font-medium transition-colors"
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

      {/* ======================= 4. Asymmetric Operations Strip (非对称工业台：左侧槽位矩阵，右侧事件排障流水) ======================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3 text-xs">
        {/* 左侧 7 列：并发槽位与队列排队流水 (Active Slots & Queue Pipeline) */}
        <div className="lg:col-span-7 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <Cpu className="w-3.5 h-3.5 text-[var(--primary)]" />
              <span className="text-[var(--text-primary)] font-medium text-xs">GPU Worker 槽位调度矩阵</span>
              <span className="text-[10px] font-mono text-[var(--primary)] bg-[var(--primary)]/10 px-1.5 py-0.2 rounded-[3px] border border-[var(--primary)]/20">
                4 / 4 满载
              </span>
            </div>
            <div className="text-[11px] font-mono text-[var(--text-tertiary)]">
              队列积压: <span className="text-[var(--warning)] font-semibold">{metrics.queueStats.totalWaiting}</span> 待消费
            </div>
          </div>

          {/* 4 个槽位横向排布 */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 my-2.5 font-mono text-[11px]">
            {metrics.activeWorkers.map((w) => (
              <div key={w.id} className="p-2.5 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] hover:border-[var(--border-normal)] transition-colors flex flex-col justify-between">
                <div className="flex items-center justify-between text-[var(--text-tertiary)]">
                  <span className="text-[var(--text-primary)] font-semibold">{w.id}</span>
                  <span className="inline-flex items-center gap-1 text-[10px] text-[var(--success)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
                    <span>BUSY</span>
                  </span>
                </div>
                <div className="truncate text-[var(--text-secondary)] font-sans mt-1 text-[11px]">{w.storyName}</div>
                <div className="text-[10px] text-[var(--primary)] mt-0.5">{w.currentFrame}</div>
              </div>
            ))}
          </div>

          {/* 队列进度与分布 */}
          <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between font-mono text-[11px]">
            <div className="flex items-center gap-3">
              <span className="text-[var(--text-tertiary)]">分级流转:</span>
              <span className="text-[var(--text-secondary)]">生成中 <span className="text-[var(--primary)] font-semibold">4</span></span>
              <span className="text-[var(--text-tertiary)]">·</span>
              <span className="text-[var(--text-secondary)]">等待锁 <span className="text-[var(--warning)] font-semibold">18</span></span>
              <span className="text-[var(--text-tertiary)]">·</span>
              <span className="text-[var(--text-secondary)]">自动退避 <span className="text-[var(--warning)] font-semibold">2</span></span>
            </div>
            <div className="text-[10px] text-[var(--text-tertiary)]">
              调度器健康度: <span className="text-[var(--success)]">99.8%</span>
            </div>
          </div>
        </div>

        {/* 右侧 5 列：异常分流拦截与系统 Trace 流 (Exceptions & Telemetry Stream) */}
        <div className="lg:col-span-5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] p-3 flex flex-col justify-between">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-3.5 h-3.5 text-[var(--danger)]" />
              <span className="text-[var(--text-primary)] font-medium text-xs">异常拦截与实时 Trace</span>
            </div>
            <div className="flex items-center gap-2 font-mono text-[10px]">
              <span className="text-[var(--danger)] bg-[var(--danger)]/10 px-1.5 py-0.5 rounded-[3px] font-medium border border-[var(--danger)]/20">
                {metrics.exceptionStats.manualActionRequired} 需人工处理
              </span>
              <span className="text-[var(--warning)] bg-[var(--warning)]/10 px-1.5 py-0.5 rounded-[3px] border border-[var(--warning)]/20">
                {metrics.exceptionStats.autoRecovering} 自愈中
              </span>
            </div>
          </div>

          {/* 实时 Trace 事件日志行 (工控风格) */}
          <div className="space-y-1.5 my-2 font-mono text-[11px]">
            {metrics.recentEvents.slice(0, 3).map((ev, i) => (
              <div key={i} className="flex items-center gap-2 p-1.5 rounded-[3px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-tertiary)] shrink-0 text-[10px]">{ev.time}</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] shrink-0" />
                <span className="text-[var(--text-primary)] font-sans truncate shrink-0 max-w-[90px]">{ev.story}</span>
                <span className="text-[var(--text-secondary)] truncate text-[10px]">{ev.text}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-[10px] font-mono text-[var(--text-tertiary)]">
            <span>日志缓冲: 实时就绪</span>
            <span className="text-[var(--success)]">Trace 延迟 &lt; 80ms</span>
          </div>
        </div>
      </div>
    </div>
  );
};
