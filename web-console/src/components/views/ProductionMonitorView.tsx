import React, { useState, useEffect, useRef } from 'react';
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
import { REAL_STORY_RUNS } from '../../data/storyosRunSnapshots';
import { isHistoricalRunIndex, loadHistoricalRunDetail } from '../../data/storyosRunLoader';
import { STORY_OS_PLATFORM_MANIFEST } from '../../data/storyosManifestSnapshot';
import { StoryRunDetailView } from './StoryRunDetailView';
import { RuntimeAuthorityPanel } from './RuntimeAuthorityPanel';
import { ExclusiveReadGate } from '../../api/exclusiveReadGate';
import { summarizeRuntimeCoverage } from '../../api/runtimeCoverage';
import type { RuntimeStatusSummary } from '../../api/platformApi';

interface ProductionMonitorViewProps {
  onSelectStoryRun?: (run: StoryRunItem) => void;
  onShowToast: (msg: string) => void;
}

export const ProductionMonitorView: React.FC<ProductionMonitorViewProps> = ({
  onSelectStoryRun,
  onShowToast,
}) => {
  // 历史运行快照，仅用于展示，不代表当前实时运行状态
  const [runs, setRuns] = useState<StoryRunItem[]>(REAL_STORY_RUNS);
  const [runtimeRows, setRuntimeRows] = useState<RuntimeStatusSummary[]>([]);
  const runtimeRowsRef = useRef<RuntimeStatusSummary[]>([]);
  const runtimeOffsetRef = useRef(0);
  const [runtimeHasMore, setRuntimeHasMore] = useState(false);
  const [runtimeLoadingMore, setRuntimeLoadingMore] = useState(false);
  const [runtimeCoverage, setRuntimeCoverage] = useState(summarizeRuntimeCoverage(0, null, false));

  // 过滤状态
  const [searchKeyword, setSearchKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [stageFilter, setStageFilter] = useState<string>('all');
  const [onlyException, setOnlyException] = useState(false);

  // 自动刷新机制 (仅增量刷新数据，不触发整页 reload)
  const [refreshInterval, setRefreshInterval] = useState<number>(15);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [apiState, setApiState] = useState<'loading' | 'ok' | 'partial' | 'offline'>('loading');
  const [lastSync, setLastSync] = useState<string | null>(null);
  const requestGate = useRef(new ExclusiveReadGate());
  const [apiWarning, setApiWarning] = useState<string | null>(null);

  // 选中的 Story Run 详情视图
  const [selectedRunForDetail, setSelectedRunForDetail] = useState<StoryRunItem | null>(null);
  const [pendingRunId, setPendingRunId] = useState<string | null>(null);
  const [runLoadError, setRunLoadError] = useState<string | null>(null);
  const runLoadGeneration = useRef(0);
  const selectRun = async (run: StoryRunItem) => {
    if (!isHistoricalRunIndex(run)) { setSelectedRunForDetail(run);return; }
    const generation = ++runLoadGeneration.current;
    setPendingRunId(run.id);setRunLoadError(null);
    try {
      const detail = await loadHistoricalRunDetail(run.id);
      if (generation !== runLoadGeneration.current) return;
      if (detail.id !== run.id) throw new Error('Run 详情身份不匹配');
      setRuns(previous => previous.map(entry => entry.id === run.id ? detail : entry));
      setSelectedRunForDetail(detail);
    } catch(error) {
      if (generation === runLoadGeneration.current) setRunLoadError(error instanceof Error?error.message:'历史 Run 加载失败');
    } finally {if (generation === runLoadGeneration.current) setPendingRunId(null);}
  };

  // 从真实平台接口同步 canonical stage 投影；丰富的帧/证据详情继续来自工作区生成投影。
  const loadLatestStatuses = async (isManual = false) => {
    // 用户展开多页时暂停后台首屏轮询，以免 15 秒后把已加载的下一页静默清空。
    // 手动刷新明确恢复到第一页，并重新读取最新摘要。
    if (!isManual && runtimeOffsetRef.current > 100) return;
    // 同一页面只允许一个阶段查询在途；旧请求不能覆盖刷新后的数据。
    const generation = requestGate.current.begin();
    if (generation === null) {
      if (isManual) onShowToast('正在读取阶段摘要，请稍候');
      return;
    }
    try {
      setIsRefreshing(true);
      const data = await platformApi.runtimeStatuses(100, 0);
      if (!requestGate.current.isCurrent(generation)) return;
      setApiState(data.errors?.length ? 'partial' : 'ok');
      setApiWarning(data.errors?.length ? 'Platform API 返回部分错误，请勿据此推断未返回的故事状态。' : null);
      setLastSync(new Date().toLocaleTimeString('zh-CN',{hour12:false}));
      // 不将平台阶段数据按标题合并进历史 Story Run；两种证据各自独立展示。
      runtimeRowsRef.current = data.items ?? [];
      runtimeOffsetRef.current = (data.items ?? []).length;
      setRuntimeRows(runtimeRowsRef.current);
      setRuntimeHasMore(Boolean(data.has_more));
      setRuntimeCoverage(summarizeRuntimeCoverage(runtimeRowsRef.current.length, data.total, Boolean(data.has_more), data.errors ?? []));
      if (isManual) {
        onShowToast(data.errors?.length ? '接口仅部分返回；未覆盖工作区快照' : '已读取最新阶段摘要，其他指标仍为工作区快照');
      }
    } catch (err) {
      if (!requestGate.current.isCurrent(generation)) return;
      console.error('Failed to fetch runtime statuses:', err);
      setApiState('offline');
      runtimeRowsRef.current = [];
      runtimeOffsetRef.current = 0;
      setRuntimeRows([]);
      setRuntimeHasMore(false);
      setRuntimeCoverage(summarizeRuntimeCoverage(0, null, false));
      setApiWarning('无法连接 Platform API。以下运行记录仅为本地工作区快照，不代表当前在线执行状态。');
      if (isManual) onShowToast('同步失败：无法连接 Platform API');
    } finally {
      if (requestGate.current.finish(generation)) setIsRefreshing(false);
    }
  };

  // 只读分页。复用同一代际锁，确保手动刷新、轮询、下一页互不覆盖。
  const loadNextRuntimePage = async () => {
    if (!runtimeHasMore) return;
    const generation = requestGate.current.begin();
    if (generation === null) return;
    const offset = runtimeOffsetRef.current;
    setRuntimeLoadingMore(true);
    try {
      const data = await platformApi.runtimeStatuses(100, offset);
      if (!requestGate.current.isCurrent(generation)) return;
      const page = data.items ?? [];
      const existing = new Set(runtimeRowsRef.current.map(r => r.episode_id || r.episode_ref).filter(Boolean));
      const next = [...runtimeRowsRef.current];
      for (const record of page) {
        const key = record.episode_id || record.episode_ref;
        if (key && existing.has(key)) continue;
        if (key) existing.add(key);
        next.push(record);
      }
      runtimeRowsRef.current = next;
      runtimeOffsetRef.current = offset + page.length;
      const hasMore = Boolean(data.has_more) && page.length > 0;
      setRuntimeHasMore(hasMore);
      setRuntimeRows(next);
      setRuntimeCoverage(summarizeRuntimeCoverage(next.length, data.total, hasMore, data.errors ?? []));
      setApiState(data.errors?.length ? 'partial' : 'ok');
      if (data.errors?.length) onShowToast('下一页返回部分错误，阶段记录可能不完整');
    } catch {
      if (requestGate.current.isCurrent(generation)) onShowToast('下一页读取失败，已保留成功加载的记录');
    } finally {
      if (requestGate.current.finish(generation)) setRuntimeLoadingMore(false);
    }
  };

  useEffect(() => {
    loadLatestStatuses();
    return () => {
      // 组件卸载/StrictMode 重新挂载时废弃当前结果，不更新已卸载页面。
      requestGate.current.invalidate();
    };
  }, []);

  // 自动刷新不会和手动刷新并发，也不会在卸载后覆盖较新请求
  useEffect(() => {
    if (refreshInterval <= 0) return;
    const interval = setInterval(() => {
      loadLatestStatuses();
    }, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  // 仅显示现有证据快照可证实的数量；不推测 Worker、GPU 或平台健康度。
  const metrics = {
    queueWaiting: runs.filter(r => r.status === 'WAITING').length,
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
      if (!['BLOCKED', 'FAILED', 'RETRYING'].includes(run.status) && run.exceptionType !== 'manual' && run.exceptionType !== 'auto_retry') {
        return false;
      }
    }
    return true;
  });

  // 本端没有已验证的暂停/恢复/重试写入契约；严禁前端自改 status 并声称成功。
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

  // 本地快照的相对心跳文本并非在线探活结果，不可根据旧秒数显示实时健康。
  const getHeartbeatStatus = (_seconds: number) => ({ color: 'text-[var(--text-tertiary)]', dot: 'bg-[var(--text-tertiary)]', label: '历史快照（未验证当前心跳）' });

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
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[var(--info)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--info)]" />
            <span>运行中</span>
          </span>
        );
      case 'WAITING':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[var(--warning)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
            <span>{run.waitingReason ? `排队中 (${run.waitingReason})` : '排队中'}</span>
          </span>
        );
      case 'RETRYING':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[var(--warning)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
            <span>自动重试中</span>
          </span>
        );
      case 'BLOCKED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-[var(--danger)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)]" />
            <span>阻塞 · 需人工介入</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[var(--danger)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)]" />
            <span>执行失败</span>
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[var(--success)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
            <span>已完成</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--text-tertiary)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-disabled)]" />
            <span>未开始</span>
          </span>
        );
    }
  };

  const getStageBadge = (stage: StoryRunStage, label: string) => {
    return (
      <span className="inline-flex items-center rounded-[7px] border border-[var(--border-normal)] bg-[var(--bg-elevated)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-secondary)] whitespace-nowrap">
        {label}
      </span>
    );
  };

  return (
    <div id="storyos-production-monitor-view" className="mx-auto max-w-[1500px] space-y-5 pb-16 font-sans text-[var(--text-primary)]">
      {/* 顶部标题与控制栏 (UI Baseline v1: 弱装饰、扁平、简洁) */}
      <div className="os-card flex flex-col gap-4 px-5 py-5 sm:flex-row sm:items-center sm:justify-between md:px-6">
        <div className="flex flex-col items-start gap-1">
          <h1 className="os-page-heading">
            生产监控
          </h1><p className="mt-1.5 text-[12px] leading-5 text-[var(--text-secondary)]">实时状态以只读 API 为准；历史 Run 快照仅用于追溯。</p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {/* 自动刷新下拉切换 */}
          <div className="flex items-center gap-1.5 h-[28px] px-2 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-secondary)]">
            <span className={`w-1.5 h-1.5 rounded-full ${isRefreshing ? 'bg-[var(--success)] animate-ping' : 'bg-[var(--success)]'}`} />
            <span className="text-[var(--text-tertiary)]">刷新:</span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="bg-transparent text-[var(--text-primary)] outline-hidden cursor-pointer text-xs"
            >
              <option value={5} className="bg-[var(--bg-elevated)]">5s</option>
              <option value={10} className="bg-[var(--bg-elevated)]">10s</option>
              <option value={30} className="bg-[var(--bg-elevated)]">30s</option>
              <option value={0} className="bg-[var(--bg-elevated)]">关闭</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => loadLatestStatuses(true)}
            className="h-[28px] w-[28px] flex items-center justify-center rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer"
            title="手动刷新"
          >
            <RefreshCw className={`w-3 h-3 ${isRefreshing ? 'animate-spin text-[var(--text-primary)]' : ''}`} />
          </button>
        </div>
      </div>

      <p role="status" className="os-source-info px-4 py-3 text-[12px] leading-5">状态数据与历史工作区 Run 快照分开呈现；历史运行状态、心跳和帧数并非实时。暂停与重试尚未接入。</p>
      <RuntimeAuthorityPanel items={runtimeRows} coverage={runtimeCoverage} hasMore={runtimeHasMore} loadingMore={runtimeLoadingMore} onLoadMore={loadNextRuntimePage} dataState={apiState} lastSync={lastSync}/>

      <div role="status" className="os-source-info flex flex-wrap items-center justify-between gap-2 px-4 py-3 text-[12px] text-[var(--text-secondary)]"><span>{apiState === 'loading' ? '正在读取 Platform API 阶段摘要…' : apiState === 'ok' ? 'Platform API 阶段摘要已读取；其余运行指标仍来自本地快照' : apiWarning}</span><span className="shrink-0 text-[var(--text-tertiary)]">{lastSync ? `最近获取 ${lastSync}` : '未获得有效在线证据'}</span></div>
      <p className="os-section-heading pt-3">历史工作区运行快照（非实时）</p>
      {/* ======================= 1. Operational Status Bar ======================= */}
      <div className="os-card flex flex-wrap items-center justify-between gap-4 px-5 py-4 text-xs">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[var(--text-tertiary)]">全部</span>
            <span className="text-[15px] font-semibold text-[var(--text-primary)]">{runs.length}</span>
          </div>

          <div className="w-[1px] h-3.5 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--info)]" />
              <span>运行</span>
            </span>
            <span className="text-[15px] font-semibold text-[var(--info)]">
              {runs.filter(r => r.status === 'RUNNING').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
              <span>等待</span>
            </span>
            <span className="text-[15px] font-semibold text-[var(--warning)]">
              {runs.filter(r => r.status === 'WAITING').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
              <span>重试</span>
            </span>
            <span className="text-[15px] font-semibold text-[var(--warning)]">
              {runs.filter(r => r.status === 'RETRYING').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[var(--danger)] font-medium flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--danger)]" />
              <span>阻塞</span>
            </span>
            <span className="text-[15px] font-semibold text-[var(--danger)]">
              {runs.filter(r => r.status === 'BLOCKED').length}
            </span>
          </div>

          <div className="w-[1px] h-3.5 bg-[var(--border-subtle)]" />

          <div className="flex items-baseline gap-1.5">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
              <span>完成</span>
            </span>
            <span className="text-[15px] font-semibold text-[var(--text-primary)]">
              {runs.filter(r => r.status === 'COMPLETED').length}
            </span>
          </div>
        </div>

        {/* 右侧指标 */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t border-[var(--border-subtle)] pt-3 text-xs text-[var(--text-secondary)] lg:border-l lg:border-t-0 lg:pl-5 lg:pt-0">
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-tertiary)]">并发:</span>
            <span className="text-[var(--text-tertiary)] font-medium">未提供</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-tertiary)]">快照等待:</span>
            <span className="text-[var(--warning)] font-medium">{metrics.queueWaiting}</span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-[var(--text-tertiary)]">健康:</span>
            <span className="text-[var(--text-tertiary)] font-medium">未验证</span>
          </div>
        </div>
      </div>

      {/* ======================= 2. Toolbar ======================= */}
      <div className="os-card flex min-h-[62px] flex-wrap items-center justify-between gap-3 px-4 py-3 text-xs">
        <div className="flex flex-1 flex-wrap items-center gap-2 min-w-[260px]">
          {/* 搜索输入框 */}
          <div className="relative flex-1 min-w-[160px] max-w-xs">
            <Search className="w-3.5 h-3.5 text-[var(--text-tertiary)] absolute left-2.5 top-2 pointer-events-none" />
            <input
              type="text"
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
              placeholder="搜索剧集 / 任务 ID..."
              className="h-9 w-full rounded-[8px] border border-[var(--border-normal)] bg-[var(--bg-app)] pl-8 pr-3 text-[12px] text-[var(--text-primary)] outline-none focus:border-[var(--focus)] placeholder:text-[var(--text-tertiary)]"
            />
          </div>

          {/* 状态下拉筛选 */}
          <div className="flex items-center gap-1.5">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="h-[28px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-[4px] px-2 text-xs outline-hidden cursor-pointer"
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
              className="h-[28px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[var(--text-primary)] rounded-[4px] px-2 text-xs outline-hidden cursor-pointer"
            >
              <option value="all">全部阶段</option>
              <option value="CREATE">创意</option>
              <option value="STORYBOARD">分镜</option>
              <option value="VISUAL_LOCK">视觉锁定</option>
              <option value="PRODUCTION">生产</option>
              <option value="PUBLISH">发布</option>
              <option value="COMPLETED">已完成</option>

            </select>
          </div>

          {/* 只看异常复选框 */}
          <label className="flex items-center gap-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer select-none ml-1">
            <input
              type="checkbox"
              checked={onlyException}
              onChange={(e) => setOnlyException(e.target.checked)}
              className="w-3.5 h-3.5 rounded-[3px] border-[#2D333D] bg-[var(--bg-workspace)] text-[var(--danger)] focus:ring-0 cursor-pointer accent-[var(--danger)]"
            />
            <span className="text-xs flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-[var(--warning)]" />
              <span>只看异常</span>
            </span>
          </label>
        </div>

        {/* 查询与重置按钮 */}
        <div className="flex items-center gap-2 font-mono">
          <button
            type="button"
            onClick={handleResetFilter}
            className="h-[28px] px-2.5 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] hover:bg-[var(--bg-elevated)] transition-colors cursor-pointer text-xs"
          >
            重置
          </button>
        </div>
      </div>

      {/* ======================= 3. Data Table (Core: Header 36px, Row 44px, Cell X 12px, Cell Y 8px) ======================= */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] overflow-hidden">
        <div className="h-[36px] px-3 bg-[var(--bg-workspace)] border-b border-[var(--border-subtle)] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[var(--text-secondary)] font-medium">
            <span>Story 调度主表</span>
            <span className="text-[var(--text-tertiary)] font-mono text-[11px]">({filteredRuns.length} 个实例)</span>
            {pendingRunId && <span role="status" className="text-[11px] text-[var(--text-secondary)]">正在按需读取历史 Run 详情…</span>}
            {runLoadError && <span role="alert" className="text-[11px] text-[var(--warning)]">历史详情读取失败：{runLoadError}；请重新点击记录重试。</span>}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="h-[36px] border-b border-[var(--border-subtle)] bg-[var(--bg-workspace)] text-[var(--text-tertiary)] font-mono text-[11px] uppercase tracking-wider font-medium">
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
                  <td colSpan={10} className="py-12 text-center text-[var(--text-tertiary)] font-mono">
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
                      className={`h-[40px] border-b border-[var(--border-subtle)] transition-colors group cursor-pointer relative ${
                        isSelected
                          ? 'bg-[#1A1F26]'
                          : 'hover:bg-[var(--bg-elevated)]'
                      }`}
                      onClick={() => void selectRun(run)}
                    >
                      {/* 序号与选中指示条 */}
                      <td className="px-3 text-center text-[var(--text-tertiary)] font-mono text-[11px] relative whitespace-nowrap">
                        {isSelected && (
                          <span className="absolute left-0 top-0 bottom-0 w-[2px] bg-[var(--info)]" />
                        )}
                        {index + 1}
                      </td>

                      {/* 剧集名称 (不换行，超出截断并进详情) */}
                      <td className="px-3 font-medium text-[var(--text-primary)] whitespace-nowrap">
                        <span className="text-[13px] font-medium text-[var(--text-primary)] tracking-tight truncate max-w-[180px] inline-block align-middle">
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
                          <div className="w-16 h-[3px] rounded-[2px] bg-[var(--border-subtle)] overflow-hidden shrink-0">
                            <div
                              className={`h-full rounded-[2px] transition-all duration-300 ${
                                run.status === 'BLOCKED'
                                   ? 'bg-[var(--danger)]'
                                   : run.progressPercent === 100
                                   ? 'bg-[var(--success)]'
                                   : 'bg-[var(--info)]'
                              }`}
                              style={{ width: `${run.progressPercent}%` }}
                            />
                          </div>
                          <span className="font-mono text-[11px] text-[var(--text-primary)] font-semibold">{run.progressPercent}%</span>
                        </div>
                      </td>

                      {/* Frame 进度 */}
                      <td className="px-3 font-mono text-xs text-[var(--text-secondary)] whitespace-nowrap">
                        <span className="text-[var(--text-primary)]">{run.completedFrames}</span>/{run.totalFrames}
                      </td>

                      {/* 耗时 */}
                      <td className="px-3 font-mono text-[var(--text-secondary)] text-[11px] whitespace-nowrap">
                        {run.duration}
                      </td>

                      {/* 心跳监控 */}
                      <td className="px-3 font-mono text-[11px] whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 ${hb.color}`} title={`心跳规则: ${hb.label}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${hb.dot}`} />
                          <span title="历史工作区快照，非实时探活">快照 {run.lastHeartbeatAgo}</span>
                        </span>
                      </td>

                      {/* 异常摘要 (单行不换行，截断进详情) */}
                      <td className="px-3 font-mono text-[11px] whitespace-nowrap">
                        {run.exceptionSummary !== '-' ? (
                          <span className="text-[var(--danger)] font-medium bg-[var(--danger)]/10 px-1.5 py-0.5 rounded-[3px] border border-[var(--danger)]/20 truncate max-w-[120px] inline-block align-middle" title={run.exceptionSummary}>
                            {run.exceptionSummary}
                          </span>
                        ) : (
                          <span className="text-[var(--text-disabled)]">-</span>
                        )}
                      </td>

                      {/* 操作栏 */}
                      <td className="px-3 text-right space-x-1 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <button
                          type="button"
                          onClick={() => void selectRun(run)}
                          className="h-[24px] px-2 rounded-[3px] bg-[var(--bg-elevated)] border border-[#2D333D] text-[var(--text-primary)] hover:bg-[#1C2128] font-mono text-[11px] cursor-pointer font-medium transition-colors"
                        >
                          详情
                        </button>

                        {run.status === 'RUNNING' && (
                          <button
                            type="button"
                            disabled title="当前仅供查看；暂停/恢复需要受控 Runtime API"
                            className="h-[24px] px-2 rounded-[3px] opacity-45 cursor-not-allowed bg-transparent border border-transparent hover:border-[var(--border-subtle)] hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] font-mono text-[11px] cursor-pointer transition-colors"
                          >
                            暂停
                          </button>
                        )}

                        {run.status === 'WAITING' && run.waitingReason === '用户手动暂停' && (
                          <button
                            type="button"
                            disabled title="当前仅供查看；暂停/恢复需要受控 Runtime API"
                            className="h-[24px] px-2 rounded-[3px] bg-[var(--success)]/10 border border-[var(--success)]/30 text-[var(--success)] hover:bg-[var(--success)]/20 font-mono text-[11px] cursor-pointer transition-colors"
                          >
                            恢复
                          </button>
                        )}

                        {run.status === 'BLOCKED' && (
                          <button
                            type="button"
                            disabled title="当前仅供查看；重试需要受控 Runtime API"
                            className="h-[24px] px-2 rounded-[3px] bg-[var(--danger)]/10 text-[var(--danger)] border border-[var(--danger)]/30 hover:bg-[var(--danger)]/20 font-mono text-[11px] cursor-pointer font-medium transition-colors"
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
      <div className="h-[32px] px-3 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] flex items-center justify-between text-[11px] font-mono text-[var(--text-tertiary)]">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-[var(--success)]">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
            <span>本地运行证据快照（非在线状态）</span>
          </span>
          <span>·</span>
          <span>实际槽位以 Runner 为准</span>
          <span>·</span>
          <span>{metrics.queueWaiting} 条快照等待记录</span>
        </div>
      </div>

      {/* 极简详情抽屉 (不繁琐、无冗余AI堆砌) */}
      {selectedRunForDetail && (
        <div className="fixed inset-y-0 right-0 z-50 w-80 bg-[var(--bg-workspace)] border-l border-[var(--border-subtle)] shadow-2xl p-4 flex flex-col justify-between animate-in slide-in-from-right duration-150">
          <div className="space-y-4">
            {/* 顶栏 */}
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <div>
                <span className="text-[10px] font-mono text-[var(--text-tertiary)]">实例详情 · {selectedRunForDetail.runId}</span>
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mt-0.5">{selectedRunForDetail.storyName}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedRunForDetail(null)}
                className="p-1 rounded hover:bg-[#1A1F26] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* 核心指标列表 */}
            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-tertiary)]">生产阶段</span>
                <span>{getStageBadge(selectedRunForDetail.currentStage, selectedRunForDetail.stageLabel)}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-tertiary)]">当前状态</span>
                <span>{getStatusBadge(selectedRunForDetail)}</span>
              </div>

              <div className="p-2 rounded bg-[#14171D] border border-[var(--border-subtle)] space-y-1.5">
                <div className="flex items-center justify-between text-[var(--text-tertiary)]">
                  <span>分镜进度</span>
                  <span className="text-[var(--text-primary)] font-semibold">{selectedRunForDetail.completedFrames} / {selectedRunForDetail.totalFrames} 帧 ({selectedRunForDetail.progressPercent}%)</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-[var(--border-subtle)] overflow-hidden">
                  <div
                    className={`h-full rounded-full ${selectedRunForDetail.progressPercent === 100 ? 'bg-[var(--success)]' : 'bg-[#58A6FF]'}`}
                    style={{ width: `${selectedRunForDetail.progressPercent}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-tertiary)]">累计耗时</span>
                <span className="text-[var(--text-primary)]">{selectedRunForDetail.duration}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-[#14171D] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-tertiary)]">心跳上报</span>
                <span className="text-[var(--text-secondary)]">{selectedRunForDetail.lastHeartbeatAgo}</span>
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
          <div className="pt-3 border-t border-[var(--border-subtle)] flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setSelectedRunForDetail(null)}
              className="px-3 py-1.5 rounded bg-[var(--bg-elevated)] border border-[#2D333D] text-xs font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] cursor-pointer"
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
