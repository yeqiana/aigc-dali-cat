import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Play,
  Pause,
  RotateCcw,
  Layers,
  Cpu,
  AlertCircle,
  Flame,
  Terminal,
  FileCode,
  Activity,
  Server,
  CheckCircle2,
  Clock,
  ShieldAlert,
  Copy,
  Check,
  Download,
  X,
  Search,
  Sparkles,
  ChevronRight,
  ChevronDown,
  Maximize2,
  Eye,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import {
  StoryRunItem,
  FrameDetailItem,
  StoryRunStage,
  FrameStatus
} from '../../types';
import { StatusBadge } from '../StatusBadge';

interface StoryRunDetailViewProps {
  run: StoryRunItem;
  onBack: () => void;
  onShowToast: (msg: string) => void;
  onUpdateRun?: (updated: StoryRunItem) => void;
}

type DetailTabKey =
  | 'overview'
  | 'exceptions'
  | 'events'
  | 'artifacts'
  | 'logs'
  | 'runtime';

type DangerousActionType = 'REGENERATE' | 'SKIP' | 'FORCE_PASS' | 'CANCEL';

export const StoryRunDetailView: React.FC<StoryRunDetailViewProps> = ({
  run,
  onBack,
  onShowToast,
  onUpdateRun
}) => {
  // 默认进入「概览」Tab
  const [activeTab, setActiveTab] = useState<DetailTabKey>('overview');

  // 默认打开 Frame 09（方便展示异常排错诊断）或 Frame 08（展示 PASSED 态）
  const [selectedFrame, setSelectedFrame] = useState<FrameDetailItem | null>(() => {
    const f09 = run.frames.find(f => f.frameNo === 9);
    return f09 || run.frames[0] || null;
  });

  const [selectedStageKey, setSelectedStageKey] = useState<StoryRunStage>(run.currentStage);
  const [promptExpanded, setPromptExpanded] = useState(false);
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [logFilter, setLogFilter] = useState<'ALL' | 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'>('ALL');
  const [logSearch, setLogSearch] = useState('');

  // 高清大图全屏预览模态框
  const [imageModalUrl, setImageModalUrl] = useState<string | null>(null);

  // 破坏性操作二次确认模态
  const [confirmAction, setConfirmAction] = useState<{
    type: DangerousActionType;
    frame: FrameDetailItem;
  } | null>(null);

  // 心跳判定函数
  const getHeartbeatStatus = (seconds: number) => {
    if (seconds < 15) return { color: 'text-emerald-400', dot: 'bg-emerald-400', label: '正常' };
    if (seconds <= 30) return { color: 'text-zinc-300', dot: 'bg-zinc-400', label: '弱提示' };
    if (seconds <= 120) return { color: 'text-amber-400', dot: 'bg-amber-400', label: '心跳延迟' };
    return { color: 'text-red-400', dot: 'bg-red-400', label: '疑似失联' };
  };

  const hb = getHeartbeatStatus(run.heartbeatSeconds);

  // 监听 Escape 键，安全级联关闭大图预览、二次确认弹窗或 Frame 抽屉
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (imageModalUrl) {
          setImageModalUrl(null);
        } else if (confirmAction) {
          setConfirmAction(null);
        } else if (selectedFrame) {
          setSelectedFrame(null);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [imageModalUrl, confirmAction, selectedFrame]);

  // 复制文本辅助
  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    onShowToast(`${label}已复制到剪贴板`);
    setTimeout(() => setCopiedText(null), 2000);
  };

  // 执行 Frame 状态变更高危操作
  const executeDangerousAction = () => {
    if (!confirmAction) return;
    const { type, frame } = confirmAction;

    if (type === 'REGENERATE') {
      onShowToast(`已为 ${frame.frameCode} 触发重新生成 (Attempt 重置)`);
      if (onUpdateRun) {
        const updatedFrames = run.frames.map(f => {
          if (f.frameNo === frame.frameNo) {
            return {
              ...f,
              status: 'GENERATING' as const,
              currentSubAction: 'IMAGE_GENERATION',
              attempt: '2 / 3',
              duration: '1s 正在渲染',
              lastError: undefined,
              failureStage: undefined
            };
          }
          return f;
        });
        const newRun = { ...run, frames: updatedFrames };
        onUpdateRun(newRun);
        setSelectedFrame(updatedFrames.find(f => f.frameNo === frame.frameNo) || null);
      }
    } else if (type === 'SKIP') {
      onShowToast(`已跳过 ${frame.frameCode} 并写入占位插槽`);
      if (onUpdateRun) {
        const updatedFrames = run.frames.map(f => {
          if (f.frameNo === frame.frameNo) {
            return {
              ...f,
              status: 'PASSED' as const,
              duration: '已跳过 (占位)',
              lastError: undefined
            };
          }
          return f;
        });
        const newRun = {
          ...run,
          frames: updatedFrames,
          completedFrames: Math.min(run.totalFrames, run.completedFrames + 1)
        };
        onUpdateRun(newRun);
        setSelectedFrame(updatedFrames.find(f => f.frameNo === frame.frameNo) || null);
      }
    } else if (type === 'FORCE_PASS') {
      onShowToast(`已强制将 ${frame.frameCode} 标记为 PASSED`);
      if (onUpdateRun) {
        const updatedFrames = run.frames.map(f => {
          if (f.frameNo === frame.frameNo) {
            return {
              ...f,
              status: 'PASSED' as const,
              duration: '强制放行',
              lastError: undefined
            };
          }
          return f;
        });
        const newRun = {
          ...run,
          frames: updatedFrames,
          completedFrames: Math.min(run.totalFrames, run.completedFrames + 1)
        };
        onUpdateRun(newRun);
        setSelectedFrame(updatedFrames.find(f => f.frameNo === frame.frameNo) || null);
      }
    } else if (type === 'CANCEL') {
      onShowToast(`已取消 ${frame.frameCode} 的当前渲染任务`);
      if (onUpdateRun) {
        const updatedFrames = run.frames.map(f => {
          if (f.frameNo === frame.frameNo) {
            return {
              ...f,
              status: 'QUEUED' as const,
              currentSubAction: undefined,
              duration: '等待调度'
            };
          }
          return f;
        });
        const newRun = { ...run, frames: updatedFrames };
        onUpdateRun(newRun);
        setSelectedFrame(updatedFrames.find(f => f.frameNo === frame.frameNo) || null);
      }
    }

    setConfirmAction(null);
  };

  // 立即重试当前 Frame（如 Frame 09）
  const handleImmediateRetry = (frame: FrameDetailItem) => {
    onShowToast(`已立即为 ${frame.frameCode} 派发重试请求`);
    if (onUpdateRun) {
      const updatedFrames = run.frames.map(f => {
        if (f.frameNo === frame.frameNo) {
          return {
            ...f,
            status: 'GENERATING' as const,
            currentSubAction: 'IMAGE_GENERATION',
            attempt: '2 / 3 (重试中)',
            duration: '2s 渲染中',
            nextRetryInSeconds: undefined
          };
        }
        return f;
      });
      const newRun = { ...run, frames: updatedFrames };
      onUpdateRun(newRun);
      setSelectedFrame(updatedFrames.find(f => f.frameNo === frame.frameNo) || null);
    }
  };

  // 过滤后的日志
  const filteredLogs = (run.logs || []).filter(lg => {
    if (logFilter !== 'ALL' && lg.level !== logFilter) return false;
    if (logSearch && !lg.message.toLowerCase().includes(logSearch.toLowerCase()) && !lg.component.toLowerCase().includes(logSearch.toLowerCase())) {
      return false;
    }
    return true;
  });

  // 获取 Frame 卡片底部状态文本规范
  const getFrameBottomLabel = (frame: FrameDetailItem): string => {
    switch (frame.status) {
      case 'PASSED':
        return frame.duration || 'PASSED';
      case 'GENERATING':
        return frame.currentSubAction ? `IMAGE_GEN / ${frame.duration || '14s'}` : `Generating ${frame.duration || '14s'}`;
      case 'RETRYING':
        return `RETRY ${frame.attempt.replace(/\s+/g, '')}`;
      case 'QUEUED':
        return 'QUEUED';
      case 'BLOCKED':
        return 'BLOCKED';
      case 'NOT_STARTED':
      default:
        return 'NOT_STARTED';
    }
  };

  // 选中的 Stage
  const currentSelectedStage = run.pipelineStages.find(s => s.key === selectedStageKey) || run.pipelineStages[0];

  return (
    <div className="flex flex-col h-full bg-[var(--bg-app)] text-[var(--text-primary)] overflow-hidden select-none font-sans">
      {/* ========================================================================= */}
      {/* 1. 顶部 Header 强化区 (遵循用户定版的正式 StoryOS V1 生产详情规范) */}
      {/* ========================================================================= */}
      <div className="bg-[var(--bg-workspace)] border-b border-[var(--border-subtle)] px-5 py-3 shrink-0 flex flex-col gap-2.5">
        {/* 第一行：面包屑与全局快捷操作 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono">
            <button
              type="button"
              onClick={onBack}
              className="px-2.5 py-1 rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-primary)] transition-colors flex items-center gap-1.5 cursor-pointer font-medium"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>返回生产监控</span>
            </button>
            <span className="text-[var(--text-disabled)]">/</span>
            <span className="text-[var(--text-secondary)]">生产监控</span>
            <span className="text-[var(--text-disabled)]">/</span>
            <span className="text-[var(--text-primary)] font-semibold font-sans">{run.storyName}</span>
            <span className="text-[var(--text-disabled)]">/</span>
            <span className="text-[var(--text-tertiary)] font-mono">{run.runId}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onShowToast('已导出当前 Run 生产审计报告 (JSON)')}
              className="px-2.5 py-1 rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-xs font-mono flex items-center gap-1.5 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
              <span>导出报告</span>
            </button>
            <button
              type="button"
              onClick={() => onShowToast(run.status === 'RUNNING' ? '已向集群下发暂停信号' : '已恢复生产调度')}
              className={`px-3 py-1 rounded-[4px] border text-xs font-mono font-medium flex items-center gap-1.5 transition-colors cursor-pointer ${
                run.status === 'RUNNING'
                  ? 'bg-[var(--warning)]/10 border-[var(--warning)]/30 text-[var(--warning)] hover:bg-[var(--warning)]/20'
                  : 'bg-[var(--success)]/10 border-[var(--success)]/30 text-[var(--success)] hover:bg-[var(--success)]/20'
              }`}
            >
              {run.status === 'RUNNING' ? (
                <>
                  <Pause className="w-3.5 h-3.5" />
                  <span>暂停生产</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  <span>恢复生产</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 第二行：核心 Header 标题 / 运行态 / 当前具体动作 / 心跳 */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-0.5">
          {/* 左侧：故事名称 + Run ID + 状态徽章 */}
          <div className="flex items-center gap-3.5">
            <div className="flex items-baseline gap-2.5">
              <h1 className="text-xl font-bold text-[var(--text-primary)] tracking-tight font-sans">
                {run.storyName}
              </h1>
              <span className="text-xs font-mono text-[var(--text-secondary)] bg-[var(--bg-subtle)] px-2 py-0.5 rounded-[4px] border border-[var(--border-normal)]">
                {run.runId}
              </span>
            </div>

            {/* 状态徽章 (严格按 StoryOS 契约渲染) */}
            <StatusBadge status={run.status} pulse={run.status === 'RUNNING'} />

            {/* 细分子动作指示器 (用户明确要求的核心指引) */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs font-mono">
              <span className="text-[var(--text-tertiary)]">当前动作:</span>
              <span className="text-[var(--text-primary)] font-medium flex items-center gap-1">
                <span>Production</span>
                <span className="text-[var(--text-disabled)]">·</span>
                <span>Frame14</span>
                <span className="text-[var(--text-disabled)]">·</span>
                <span className="text-[var(--primary)]">IMAGE_GENERATION</span>
              </span>
            </div>
          </div>

          {/* 右侧：耗时 + 心跳 */}
          <div className="flex items-center gap-4 text-xs font-mono text-[var(--text-secondary)]">
            <div>
              <span className="text-[var(--text-tertiary)] mr-1.5">耗时</span>
              <span className="text-[var(--text-primary)] font-semibold tabular-nums">{run.duration}</span>
            </div>

            <div className="flex items-center gap-1.5">
              <span className="text-[var(--text-tertiary)] mr-1">Heartbeat</span>
              <span className={`flex items-center gap-1 font-medium tabular-nums ${hb.color}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${hb.dot}`} />
                {run.lastHeartbeatAgo}
              </span>
            </div>
          </div>
        </div>

        {/* 第三行：六大专业 Tab (严格按照用户定版命名，扁平运维控制台风格，绝无消费级白底白斑) */}
        <div className="flex items-center gap-1 border-t border-[var(--border-subtle)] pt-2 overflow-x-auto no-scrollbar">
          {[
            { key: 'overview', label: '概览', icon: Activity },
            {
              key: 'exceptions',
              label: '异常',
              icon: ShieldAlert,
              badge: run.exceptionSummary !== '-' ? '1' : undefined,
              warn: run.exceptionSummary !== '-'
            },
            { key: 'events', label: '事件', icon: Clock, badge: 'Trace' },
            { key: 'artifacts', label: 'Artifacts', icon: FileCode },
            { key: 'logs', label: '日志', icon: Terminal },
            { key: 'runtime', label: '运行环境', icon: Server },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key as DetailTabKey)}
                className={`px-3 py-1.5 rounded-[4px] text-xs font-mono font-medium flex items-center gap-2 transition-colors cursor-pointer whitespace-nowrap ${
                  isActive
                    ? 'bg-[var(--bg-subtle)] text-[var(--text-primary)] border border-[var(--border-normal)] font-semibold'
                    : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] border border-transparent'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[var(--primary)]' : 'text-[var(--text-tertiary)]'}`} />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-[3px] font-mono ${
                    isActive
                      ? 'bg-[var(--bg-muted)] text-[var(--text-primary)] border border-[var(--border-normal)]'
                      : tab.warn
                      ? 'bg-[var(--danger)]/15 text-[var(--danger)] border border-[var(--danger)]/30'
                      : 'bg-[var(--bg-subtle)] text-[var(--text-secondary)]'
                  }`}>
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 2. 主体工作区 + 独立右侧 Frame Drawer (绝非弹窗嵌套) */}
      {/* ========================================================================= */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* 左侧主要内容面板 */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* ========================================================================= */}
          {/* Tab 1: 概览 (Overview) —— 融合 Story 摘要、Pipeline、Frame 生产矩阵 */}
          {/* ========================================================================= */}
          {activeTab === 'overview' && (
            <div className="space-y-6 max-w-6xl">
              {/* 1.1 Story 摘要卡片 (生产信息优先，故事介绍弱化为单行) */}
              <div className="p-4 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2.5 border-b border-[var(--border-subtle)]">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xs font-bold text-[var(--text-primary)] font-mono uppercase tracking-wider">
                      Story 摘要
                    </span>
                    <span className="text-[var(--text-disabled)]">/</span>
                    <span className="text-xs font-mono text-[var(--text-secondary)] font-medium">
                      {run.progressPercent}% · Production · {run.completedFrames}/{run.totalFrames} · Frame14 · IMAGE_GENERATION
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-xs font-mono text-[var(--text-secondary)]">
                    <div>
                      <span className="text-[var(--text-tertiary)]">承载 Worker:</span>{' '}
                      <span className="text-[var(--text-primary)]">{run.runtimeEnv?.workerId || 'Worker-01'}</span>
                    </div>
                    <div>
                      <span className="text-[var(--text-tertiary)]">创建时间:</span>{' '}
                      <span className="text-[var(--text-secondary)] tabular-nums">{run.createdAt}</span>
                    </div>
                  </div>
                </div>

                {/* 加权进度条与剧情单行辅助说明 */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-[var(--text-tertiary)]">综合流水线加权进度:</span>
                    <span className="text-[var(--text-primary)] font-semibold tabular-nums">{run.progressPercent}% (前置 35% + 生产 45% + 交付 20%)</span>
                  </div>
                  <div className="w-full h-1.5 rounded-[2px] bg-[var(--bg-workspace)] overflow-hidden border border-[var(--border-subtle)]">
                    <div
                      className="h-full bg-[var(--primary)] rounded-[2px] transition-all"
                      style={{ width: `${run.progressPercent}%` }}
                    />
                  </div>
                </div>

                {/* 弱化后的故事简介 (紧凑单行) */}
                <div className="text-xs text-[var(--text-tertiary)] font-sans truncate pt-0.5">
                  <span className="text-[var(--text-disabled)] font-mono mr-1.5">[梗概]</span>
                  <span>{run.storyDescription}</span>
                </div>
              </div>

              {/* 1.2 PIPELINE 8 阶段流水线 (Production 显示内部进度 14/20 与进度条) */}
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center gap-2">
                    <Layers className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
                    <span>PIPELINE (8 Stages)</span>
                  </div>
                  <span className="text-[11px] font-mono text-[var(--text-tertiary)]">
                    点击阶段卡片可在下方展开阶段输入输出契约
                  </span>
                </div>

                {/* 8 个阶段卡片横向布局 */}
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                  {run.pipelineStages.map((stage) => {
                    const isDone = stage.status === 'completed';
                    const isRunning = stage.status === 'running';
                    const isWarn = stage.status === 'warning';
                    const isSelected = selectedStageKey === stage.key;
                    const isProductionStage = stage.key === 'PRODUCTION';

                    return (
                      <button
                        key={stage.key}
                        type="button"
                        onClick={() => setSelectedStageKey(stage.key)}
                        className={`p-2.5 rounded-[4px] border text-left flex flex-col justify-between transition-colors cursor-pointer min-h-[92px] ${
                          isSelected ? 'ring-1 ring-[var(--primary)] border-[var(--primary)] bg-[var(--bg-subtle)]' : ''
                        } ${
                          !isSelected && isDone
                            ? 'bg-[var(--success)]/10 border-[var(--success)]/30 text-[var(--success)]'
                            : !isSelected && isRunning
                            ? 'bg-[var(--bg-subtle)] border-[var(--primary)]/40 text-[var(--primary)]'
                            : !isSelected && isWarn
                            ? 'bg-[var(--danger)]/10 border-[var(--danger)]/30 text-[var(--danger)]'
                            : !isSelected
                            ? 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--text-tertiary)] hover:border-[var(--border-strong)]'
                            : ''
                        }`}
                      >
                        <div className="flex items-center justify-between text-xs font-mono">
                          <span className="font-medium text-xs font-sans truncate">
                            {stage.label}
                          </span>
                          <span className="text-[11px]">{isDone ? '✓' : isRunning ? '●' : isWarn ? '!' : '○'}</span>
                        </div>

                        {/* 如果是长阶段 Production，必须显示内部进度 14 / 20 与进度条 */}
                        {isProductionStage ? (
                          <div className="space-y-1.5 my-1">
                            <div className="w-full h-1 rounded-[2px] bg-[var(--bg-workspace)] overflow-hidden border border-[var(--border-subtle)]">
                              <div
                                className="h-full bg-[var(--primary)] rounded-[2px] transition-all"
                                style={{ width: `${(run.completedFrames / run.totalFrames) * 100}%` }}
                              />
                            </div>
                            <div className="flex items-center justify-between text-[11px] font-mono text-[var(--text-primary)] font-semibold tabular-nums">
                              <span>{run.completedFrames} / {run.totalFrames}</span>
                              <span className="text-[var(--text-tertiary)] text-[10px] font-normal">28m</span>
                            </div>
                          </div>
                        ) : (
                          <div className="text-[11px] font-mono mt-2 text-[var(--text-tertiary)]">
                            {stage.timeCost || '待开始'}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>

                {/* 选中的 Stage 深度详情折叠区 */}
                {currentSelectedStage && (
                  <div className="p-3.5 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2.5 text-xs font-mono">
                    <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[var(--text-primary)] font-semibold font-sans">
                          {currentSelectedStage.label} 阶段契约
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-[3px] font-semibold ${
                          currentSelectedStage.status === 'completed'
                            ? 'bg-[var(--success)]/15 text-[var(--success)] border border-[var(--success)]/30'
                            : currentSelectedStage.status === 'running'
                            ? 'bg-[var(--primary)]/15 text-[var(--primary)] border border-[var(--primary)]/30'
                            : 'bg-[var(--bg-subtle)] text-[var(--text-tertiary)] border border-[var(--border-normal)]'
                        }`}>
                          {currentSelectedStage.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="text-[var(--text-tertiary)] text-[11px]">
                        耗时: <strong className="text-[var(--text-primary)] tabular-nums">{currentSelectedStage.timeCost || '-'}</strong> · Trace: <code className="text-[var(--text-secondary)]">{currentSelectedStage.traceId || 'TR-STG-001'}</code>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-[11px]">
                      <div className="p-2 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)]">
                        <span className="text-[var(--text-tertiary)] block mb-1">输入依赖 (Input Artifacts):</span>
                        <span className="text-[var(--text-secondary)]">
                          {currentSelectedStage.inputArtifacts?.join(', ') || '无前置强依赖'}
                        </span>
                      </div>
                      <div className="p-2 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)]">
                        <span className="text-[var(--text-tertiary)] block mb-1">交付产物 (Output Artifacts):</span>
                        <span className="text-[var(--success)]">
                          {currentSelectedStage.outputArtifacts?.join(', ') || '执行中生成...'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* 1.3 FRAME PRODUCTION (01 ~ 20 矩阵网格) */}
              <div className="space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center gap-2">
                      <Flame className="w-3.5 h-3.5 text-[var(--text-primary)]" />
                      <span>FRAME PRODUCTION (01 - 20)</span>
                    </h2>
                    <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5 font-mono">
                      点击任意卡片在右侧呼出该分镜深度诊断抽屉
                    </p>
                  </div>

                  {/* 状态规范图例 */}
                  <div className="flex flex-wrap items-center gap-3 text-[11px] font-mono text-[var(--text-secondary)]">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)]" />
                      <span>PASSED (14)</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--primary)] animate-pulse" />
                      <span>RUNNING (1)</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
                      <span>RETRYING (1)</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
                      <span>QUEUED (4)</span>
                    </span>
                  </div>
                </div>

                {/* 20 帧网格 (点击卡片在右侧直接展示 Frame Drawer) */}
                <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-10 gap-2">
                  {run.frames.map((f) => {
                    const isPassed = f.status === 'PASSED';
                    const isGen = f.status === 'GENERATING';
                    const isRetry = f.status === 'RETRYING';
                    const isBlocked = f.status === 'BLOCKED';
                    const isQueued = f.status === 'QUEUED';
                    const isSelected = selectedFrame?.frameNo === f.frameNo;

                    return (
                      <button
                        key={f.frameNo}
                        type="button"
                        onClick={() => setSelectedFrame(f)}
                        className={`p-1.5 rounded-[4px] border text-left flex flex-col justify-between aspect-3/4 transition-colors cursor-pointer relative overflow-hidden group ${
                          isSelected ? 'ring-1 ring-[var(--primary)] border-[var(--primary)]' : ''
                        } ${
                          isPassed
                            ? 'bg-[var(--bg-workspace)] border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--border-strong)]'
                            : isGen
                            ? 'bg-[var(--primary)]/10 border-[var(--primary)]/50 text-[var(--primary)]'
                            : isRetry
                            ? 'bg-[var(--warning)]/15 border-[var(--warning)]/50 text-[var(--warning)]'
                            : isBlocked
                            ? 'bg-[var(--danger)]/15 border-[var(--danger)]/50 text-[var(--danger)]'
                            : isQueued
                            ? 'bg-[var(--bg-surface)] border-[var(--border-subtle)] text-[var(--warning)] hover:border-[var(--border-strong)]'
                            : 'bg-[var(--bg-workspace)] border-[var(--border-subtle)] text-[var(--text-disabled)]'
                        }`}
                      >
                        {/* 顶部序号与状态标记 */}
                        <div className="flex items-center justify-between text-[11px] font-mono z-10">
                          <span className="font-semibold bg-[var(--bg-app)]/80 px-1 py-0.2 rounded-[2px]">
                            {String(f.frameNo).padStart(2, '0')}
                          </span>
                          <span className="w-1.5 h-1.5 rounded-full" style={{
                            backgroundColor: isPassed ? 'var(--success)' : isGen ? 'var(--primary)' : isRetry ? 'var(--warning)' : isBlocked ? 'var(--danger)' : isQueued ? 'var(--warning)' : 'var(--text-disabled)'
                          }} />
                        </div>

                        {/* 缩略图预览 */}
                        {f.thumbnail ? (
                          <img
                            src={f.thumbnail}
                            alt={f.frameCode}
                            className="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-90 transition-opacity"
                          />
                        ) : null}

                        {/* 底部业务状态文本 (绝不靠颜色猜) */}
                        <div className="mt-auto z-10 bg-[var(--bg-app)]/90 px-1 py-0.5 rounded-[2px] text-[10px] font-mono truncate text-center font-medium">
                          {getFrameBottomLabel(f)}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* Tab 2: 异常 (Exceptions) */}
          {/* ========================================================================= */}
          {activeTab === 'exceptions' && (
            <div className="space-y-4 max-w-5xl">
              <div>
                <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center gap-2">
                  <ShieldAlert className="w-3.5 h-3.5 text-[var(--danger)]" />
                  <span>异常审计与自愈机制</span>
                </h2>
                <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                  严格区分“需要人工处理（红色）”与“系统正在自动恢复（橙黄色）”
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* 需人工处理卡片 */}
                <div className="p-3.5 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold font-mono text-[var(--text-primary)] flex items-center gap-1.5">
                      <AlertCircle className="w-3.5 h-3.5 text-[var(--success)]" />
                      <span>需人工介入处理 (0 项阻塞)</span>
                    </span>
                    <span className="text-[10px] font-mono text-[var(--success)] bg-[var(--success)]/15 border border-[var(--success)]/30 px-1.5 py-0.5 rounded-[3px]">
                      HEALTHY
                    </span>
                  </div>
                  <p className="text-xs text-[var(--text-tertiary)]">
                    当前 Run 无任何阻塞死锁异常，所有核心资产契约（Character Contract、Visual Lock）已按时交付。
                  </p>
                </div>

                {/* 自动恢复中卡片 */}
                <div className="p-3.5 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold font-mono text-[var(--warning)] flex items-center gap-1.5">
                      <RotateCcw className="w-3.5 h-3.5 text-[var(--warning)]" />
                      <span>系统自愈中 (1 项生效中)</span>
                    </span>
                    <span className="text-[10px] font-mono text-[var(--warning)] bg-[var(--warning)]/15 border border-[var(--warning)]/30 px-1.5 py-0.5 rounded-[3px]">
                      AUTO-RETRY
                    </span>
                  </div>
                  <div className="p-2.5 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-xs font-mono space-y-1">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">目标分镜:</span>
                      <span className="text-[var(--text-primary)] font-semibold">Frame 09</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">异常代码:</span>
                      <span className="text-[var(--warning)] font-semibold">NETWORK_ERROR (Socket Timeout)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">退避重试:</span>
                      <span className="text-[var(--text-secondary)] tabular-nums">Attempt 2 / 3 (17s 后自动触发)</span>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      const f09 = run.frames.find(f => f.frameNo === 9);
                      if (f09) {
                        setSelectedFrame(f09);
                        handleImmediateRetry(f09);
                      }
                    }}
                    className="w-full h-[30px] rounded-[4px] bg-[var(--warning)] text-black font-semibold text-xs font-mono hover:bg-[var(--warning)]/90 transition-colors cursor-pointer"
                  >
                    立即手动触发 Attempt 2/3
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* Tab 3: 事件 (Events) */}
          {/* ========================================================================= */}
          {activeTab === 'events' && (
            <div className="space-y-4 max-w-5xl">
              <div>
                <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center gap-2">
                  <Clock className="w-3.5 h-3.5 text-[var(--text-primary)]" />
                  <span>分布式链路事件流水 (Trace Events)</span>
                </h2>
                <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                  精确至毫秒级的分布式全流程审计时间轴
                </p>
              </div>

              <div className="space-y-1.5 font-mono text-xs">
                {(run.events || []).map((ev) => (
                  <div
                    key={ev.id}
                    className="p-2.5 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex items-start justify-between gap-4 hover:border-[var(--border-strong)] transition-colors"
                  >
                    <div className="flex items-start gap-2.5">
                      <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                        ev.status === 'success' ? 'bg-[var(--success)]' : ev.status === 'error' ? 'bg-[var(--danger)]' : ev.status === 'warn' ? 'bg-[var(--warning)]' : 'bg-[var(--primary)]'
                      }`} />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-[var(--text-primary)] font-semibold">{ev.eventName}</span>
                          <span className="text-[10px] text-[var(--text-tertiary)] bg-[var(--bg-workspace)] px-1.5 py-0.2 rounded-[2px] border border-[var(--border-subtle)]">
                            {ev.stage}
                          </span>
                        </div>
                        <div className="text-[var(--text-secondary)] font-sans text-xs mt-0.5">
                          {ev.detail}
                        </div>
                      </div>
                    </div>
                    <span className="text-[var(--text-tertiary)] text-[11px] tabular-nums shrink-0">{ev.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* Tab 4: Artifacts (产物清单) */}
          {/* ========================================================================= */}
          {activeTab === 'artifacts' && (
            <div className="space-y-4 max-w-5xl">
              <div>
                <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center gap-2">
                  <FileCode className="w-3.5 h-3.5 text-[var(--text-primary)]" />
                  <span>产物交付清单 (Artifacts)</span>
                </h2>
                <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                  流水线各阶段生成的机器与人类可读资产
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(run.artifacts || []).map((art) => (
                  <div key={art.id} className="p-3 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-2 hover:border-[var(--border-strong)] transition-colors">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-xs font-semibold font-mono text-[var(--text-primary)] flex items-center gap-1.5">
                          <span>📦</span>
                          <span>{art.name}</span>
                        </div>
                        <div className="text-[11px] text-[var(--text-tertiary)] font-mono mt-0.5">
                          {art.stage} · {art.size} · {art.updatedAt}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => onShowToast(`正在下载产物: ${art.name}`)}
                        className="p-1 hover:text-[var(--text-primary)] text-[var(--text-tertiary)] rounded-[4px] hover:bg-[var(--bg-muted)] cursor-pointer"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {art.previewSnippet && (
                      <pre className="p-2 rounded-[3px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] font-mono overflow-x-auto">
                        {art.previewSnippet}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* Tab 5: 日志 (Runtime Logs) */}
          {/* ========================================================================= */}
          {activeTab === 'logs' && (
            <div className="space-y-3 max-w-5xl">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center gap-2">
                    <Terminal className="w-3.5 h-3.5 text-[var(--text-primary)]" />
                    <span>执行终端日志 (Console Logs)</span>
                  </h2>
                </div>

                {/* 过滤条 */}
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-disabled)]" />
                    <input
                      type="text"
                      value={logSearch}
                      onChange={(e) => setLogSearch(e.target.value)}
                      placeholder="搜索日志..."
                      className="h-[28px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] rounded-[4px] pl-8 pr-2.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-disabled)] focus:outline-none focus:border-[var(--primary)] font-mono"
                    />
                  </div>

                  <div className="flex items-center gap-0.5 bg-[var(--bg-workspace)] p-0.5 rounded-[4px] border border-[var(--border-subtle)] text-xs font-mono h-[28px]">
                    {(['ALL', 'INFO', 'WARN', 'ERROR'] as const).map(lvl => (
                      <button
                        key={lvl}
                        type="button"
                        onClick={() => setLogFilter(lvl)}
                        className={`px-2 py-0.5 rounded-[3px] cursor-pointer text-xs ${
                          logFilter === lvl ? 'bg-[var(--bg-muted)] text-[var(--text-primary)] font-semibold' : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'
                        }`}
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* 终端黑色面板 */}
              <div className="p-3.5 rounded-[6px] bg-[var(--bg-app)] border border-[var(--border-subtle)] font-mono text-[11px] space-y-1.5 max-h-[500px] overflow-y-auto">
                {filteredLogs.map(lg => {
                  const isErr = lg.level === 'ERROR';
                  const isWarn = lg.level === 'WARN';
                  return (
                    <div key={lg.id} className="flex items-start gap-2.5 leading-relaxed">
                      <span className="text-[var(--text-disabled)] tabular-nums shrink-0">{lg.timestamp}</span>
                      <span className={`px-1 py-0.2 rounded-[2px] text-[10px] shrink-0 font-semibold ${
                        isErr ? 'bg-[var(--danger)]/20 text-[var(--danger)]' : isWarn ? 'bg-[var(--warning)]/20 text-[var(--warning)]' : 'bg-[var(--bg-subtle)] text-[var(--text-tertiary)]'
                      }`}>
                        {lg.level}
                      </span>
                      <span className="text-[var(--text-tertiary)] shrink-0">[{lg.component}]</span>
                      <span className={isErr ? 'text-[var(--danger)] font-semibold' : isWarn ? 'text-[var(--warning)]' : 'text-[var(--text-secondary)]'}>
                        {lg.message}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* Tab 6: 运行环境 (Runtime Env) */}
          {/* ========================================================================= */}
          {activeTab === 'runtime' && (
            <div className="space-y-4 max-w-5xl font-mono text-xs">
              <div>
                <h2 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider font-mono flex items-center gap-2">
                  <Server className="w-3.5 h-3.5 text-[var(--text-primary)]" />
                  <span>底层硬件与推理环境 (Infrastructure Topology)</span>
                </h2>
                <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                  Worker 节点、模型路由引擎、心跳链路拓扑
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
                  <div className="text-[var(--text-primary)] font-semibold pb-2 border-b border-[var(--border-subtle)] flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-[var(--success)]" />
                    <span>Worker 推理节点</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">Worker 实例:</span>
                      <span className="text-[var(--text-primary)] font-semibold">{run.runtimeEnv?.workerId || 'worker-node-01-eu'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">GPU 硬件规格:</span>
                      <span className="text-[var(--text-secondary)]">{run.runtimeEnv?.gpuNode || 'NVIDIA A100-SXM4-80GB'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">心跳检测间隔:</span>
                      <span className="text-[var(--success)] font-semibold">{run.runtimeEnv?.heartbeatInterval || '5000 ms'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">并发池插槽:</span>
                      <span className="text-[var(--text-secondary)]">{run.runtimeEnv?.activeConcurrency || '4 Slots'}</span>
                    </div>
                  </div>
                </div>

                <div className="p-3.5 rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
                  <div className="text-[var(--text-primary)] font-semibold pb-2 border-b border-[var(--border-subtle)] flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-[var(--primary)]" />
                    <span>模型与出图规范</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">模型引擎:</span>
                      <span className="text-[var(--text-primary)] font-semibold">{run.runtimeEnv?.modelProvider || 'gpt-image-2.5-flare'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">默认画幅比例:</span>
                      <span className="text-[var(--text-secondary)]">{run.runtimeEnv?.aspectRatio || '4:5 竖版'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">原生输出分辨率:</span>
                      <span className="text-[var(--text-secondary)]">{run.runtimeEnv?.imageResolution || '1080 × 1350 px'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ========================================================================= */}
        {/* 3. 右侧 Frame 详情抽屉 (Right Drawer) —— UI Baseline v1: 宽度 440px/480px, bg var(--bg-surface) */}
        {/* ========================================================================= */}
        {selectedFrame && (
          <div className="w-[440px] xl:w-[480px] shrink-0 border-l border-[var(--border-subtle)] bg-[var(--bg-surface)] flex flex-col h-full overflow-y-auto animate-in slide-in-from-right duration-200">
            {/* 抽屉头部 */}
            <div className="h-[48px] px-4 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-workspace)] shrink-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold font-mono text-[var(--text-primary)]">
                  {selectedFrame.frameCode}
                </span>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-[3px] font-medium ${
                  selectedFrame.status === 'PASSED'
                    ? 'bg-[var(--success)]/15 text-[var(--success)] border border-[var(--success)]/30'
                    : selectedFrame.status === 'RETRYING'
                    ? 'bg-[var(--warning)]/20 text-[var(--warning)] border border-[var(--warning)]/30'
                    : selectedFrame.status === 'BLOCKED'
                    ? 'bg-[var(--danger)]/20 text-[var(--danger)] border border-[var(--danger)]/30'
                    : selectedFrame.status === 'GENERATING'
                    ? 'bg-[var(--primary)]/20 text-[var(--primary)] border border-[var(--primary)]/30'
                    : 'bg-[var(--bg-subtle)] text-[var(--text-secondary)]'
                }`}>
                  {selectedFrame.status}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFrame(null)}
                className="p-1 hover:text-[var(--text-primary)] rounded-[4px] hover:bg-[var(--bg-muted)] cursor-pointer text-[var(--text-tertiary)]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* 抽屉滚动内容 */}
            <div className="p-4 space-y-4 text-xs font-mono flex-1 overflow-y-auto">
              {/* ===================== [上半部分：人看的信息] ===================== */}
              <div className="space-y-3">
                {/* 最终大图展示 */}
                {selectedFrame.thumbnail ? (
                  <div className="rounded-[4px] overflow-hidden border border-[var(--border-subtle)] relative group aspect-[4/5] bg-[var(--bg-app)]">
                    <img
                      src={selectedFrame.thumbnail}
                      alt={selectedFrame.frameCode}
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent p-3 text-[11px] text-[var(--text-secondary)] flex justify-between items-center">
                      <span className="font-sans font-medium text-[var(--text-primary)]">渲染原图</span>
                      <button
                        type="button"
                        onClick={() => setImageModalUrl(selectedFrame.thumbnail || null)}
                        className="px-2 py-1 rounded-[3px] bg-[var(--bg-app)]/80 hover:bg-[var(--bg-muted)] hover:text-white border border-[var(--border-normal)] transition-colors text-[10px] flex items-center gap-1 cursor-pointer"
                      >
                        <Maximize2 className="w-3 h-3" />
                        <span>全屏预览</span>
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-[4px] border border-dashed border-[var(--border-normal)] aspect-[4/5] bg-[var(--bg-workspace)] flex flex-col items-center justify-center text-[var(--text-tertiary)] text-xs p-4 text-center">
                    <Flame className="w-7 h-7 text-[var(--warning)] mb-2 opacity-50" />
                    <span className="text-[var(--text-secondary)]">暂无最终渲染图</span>
                    <span className="text-[10px] text-[var(--text-disabled)] mt-1">
                      {selectedFrame.status === 'RETRYING' ? '自动重试中，请稍候...' : '任务排队调度中'}
                    </span>
                  </div>
                )}

                {/* 基础元数据网格 */}
                <div className="bg-[var(--bg-workspace)] p-3 rounded-[4px] border border-[var(--border-subtle)] space-y-2">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-tertiary)]">状态 (Status):</span>
                    <span className={`font-semibold ${
                      selectedFrame.status === 'PASSED' ? 'text-[var(--success)]' :
                      selectedFrame.status === 'RETRYING' ? 'text-[var(--warning)]' :
                      selectedFrame.status === 'GENERATING' ? 'text-[var(--primary)]' : 'text-[var(--text-secondary)]'
                    }`}>
                      {selectedFrame.status}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[var(--text-tertiary)]">耗时 (Duration):</span>
                    <span className="text-[var(--text-primary)] font-medium tabular-nums">{selectedFrame.duration || '33s'}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[var(--text-tertiary)]">Attempt 次数:</span>
                    <span className="text-[var(--text-primary)] font-semibold tabular-nums">{selectedFrame.attempt}</span>
                  </div>

                  {selectedFrame.completedAt && (
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">完成时间:</span>
                      <span className="text-[var(--text-secondary)] tabular-nums">{selectedFrame.completedAt}</span>
                    </div>
                  )}

                  {selectedFrame.currentSubAction && (
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">子阶段动作:</span>
                      <span className="text-[var(--primary)] font-semibold">{selectedFrame.currentSubAction}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* ===================== [生成信息] ===================== */}
              <div className="space-y-3 pt-1 border-t border-[var(--border-subtle)]">
                <div className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider flex items-center justify-between">
                  <span>生成信息</span>
                  <span className="text-[10px] text-[var(--text-tertiary)] font-normal">Inference Details</span>
                </div>

                <div className="bg-[var(--bg-workspace)] p-3 rounded-[4px] border border-[var(--border-subtle)] space-y-2">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-tertiary)]">Provider:</span>
                    <span className="text-[var(--text-primary)] font-mono">{selectedFrame.provider || 'gpt-image-2.5-flare'}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-[var(--text-tertiary)]">Model:</span>
                    <span className="text-[var(--text-primary)] font-mono">{selectedFrame.modelName || 'flux-cinematic-pro'}</span>
                  </div>

                  {selectedFrame.artifactName && (
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--text-tertiary)]">Artifact:</span>
                      <button
                        type="button"
                        onClick={() => onShowToast(`正在下载产物: ${selectedFrame.artifactName}`)}
                        className="text-[var(--success)] hover:underline flex items-center gap-1 cursor-pointer"
                      >
                        <span>{selectedFrame.artifactName}</span>
                        <span className="text-[var(--text-tertiary)]">({selectedFrame.artifactSize || '4.2 MB'})</span>
                        <ChevronRight className="w-3 h-3 text-[var(--text-tertiary)]" />
                      </button>
                    </div>
                  )}

                  {selectedFrame.traceId && (
                    <div className="flex justify-between items-center">
                      <span className="text-[var(--text-tertiary)]">Trace:</span>
                      <button
                        type="button"
                        onClick={() => handleCopy(selectedFrame.traceId || '', 'Trace ID')}
                        className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] underline cursor-pointer flex items-center gap-1 text-[11px]"
                      >
                        <span>{selectedFrame.traceId}</span>
                        {copiedText === 'Trace ID' ? <Check className="w-3 h-3 text-[var(--success)]" /> : <Copy className="w-3 h-3 text-[var(--text-tertiary)]" />}
                      </button>
                    </div>
                  )}
                </div>

                {/* References 引用列表 (带小预览图) */}
                {selectedFrame.referenceItems && selectedFrame.referenceItems.length > 0 && (
                  <div className="space-y-1.5">
                    <div className="text-[var(--text-tertiary)] text-[11px] flex items-center justify-between">
                      <span>References (特征契约):</span>
                      <span className="text-[var(--text-disabled)] text-[10px]">已绑定视觉特征</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {selectedFrame.referenceItems.map((ref, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 p-1.5 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-colors"
                        >
                          {ref.url && (
                            <img
                              src={ref.url}
                              alt={ref.name}
                              className="w-7 h-7 rounded-[3px] object-cover shrink-0 cursor-pointer"
                              onClick={() => setImageModalUrl(ref.url || null)}
                            />
                          )}
                          <div className="truncate">
                            <span className="block text-[var(--text-primary)] font-semibold truncate text-[11px]">{ref.name}</span>
                            <span className="text-[10px] text-[var(--text-tertiary)]">{ref.type || 'reference'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Prompt 提示词 (可折叠/展开与一键复制) */}
                {selectedFrame.prompt && (
                  <div className="space-y-1.5">
                    <div className="text-[var(--text-tertiary)] text-[11px] flex items-center justify-between">
                      <span>Prompt (生图提示词):</span>
                      <button
                        type="button"
                        onClick={() => handleCopy(selectedFrame.prompt || '', 'Prompt')}
                        className="text-[var(--text-primary)] hover:underline flex items-center gap-1 text-[10px] cursor-pointer"
                      >
                        {copiedText === 'Prompt' ? <Check className="w-3 h-3 text-[var(--success)]" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedText === 'Prompt' ? '已复制' : '复制 Prompt'}</span>
                      </button>
                    </div>
                    <div className="p-2.5 rounded-[4px] bg-[var(--bg-app)] border border-[var(--border-subtle)] text-[var(--text-secondary)] text-[11px] leading-relaxed relative">
                      <p className={promptExpanded ? '' : 'line-clamp-3'}>
                        {selectedFrame.prompt}
                      </p>
                      <button
                        type="button"
                        onClick={() => setPromptExpanded(!promptExpanded)}
                        className="mt-1 text-[10px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] flex items-center gap-0.5 cursor-pointer"
                      >
                        <span>{promptExpanded ? '收起提示词' : '查看完整提示词 >'}</span>
                        {promptExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* ===================== [异常诊断区 (仅异常 Frame 专属展示)] ===================== */}
              {(selectedFrame.status === 'RETRYING' || selectedFrame.status === 'BLOCKED' || selectedFrame.lastError) && (
                <div className="space-y-2 pt-1 border-t border-[var(--border-subtle)]">
                  <div className="text-xs font-bold text-[var(--warning)] uppercase tracking-wider flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-[var(--warning)]" />
                      <span>异常诊断</span>
                    </span>
                    <span className="text-[10px] text-[var(--warning)]/80 font-normal">Diagnostic</span>
                  </div>

                  <div className="p-3 rounded-[4px] bg-[var(--bg-workspace)] border border-[var(--warning)]/30 space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">Error:</span>
                      <span className="text-[var(--warning)] font-semibold">{selectedFrame.lastError || 'NETWORK_ERROR'}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">Failure Stage:</span>
                      <span className="text-[var(--text-secondary)]">{selectedFrame.failureStage || 'provider_download'}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">Last Attempt:</span>
                      <span className="text-[var(--text-secondary)] tabular-nums">{selectedFrame.failedAt || '11:18:22'}</span>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-[var(--text-tertiary)]">Retry:</span>
                      <span className="text-[var(--text-primary)] font-semibold tabular-nums">{selectedFrame.attempt}</span>
                    </div>

                    {selectedFrame.status === 'RETRYING' && (
                      <div className="flex justify-between text-[var(--warning)] font-semibold pt-1 border-t border-[var(--warning)]/20">
                        <span>Next Retry:</span>
                        <span className="tabular-nums">{selectedFrame.nextRetryInSeconds || 17}s 倒计时</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 分镜事件历史 */}
              {selectedFrame.recentEvents && selectedFrame.recentEvents.length > 0 && (
                <div className="space-y-1.5 pt-1 border-t border-[var(--border-subtle)]">
                  <div className="text-[var(--text-tertiary)] text-[11px]">Frame Event Stream:</div>
                  <div className="space-y-1 p-2 rounded-[4px] bg-[var(--bg-app)] border border-[var(--border-subtle)] text-[11px]">
                    {selectedFrame.recentEvents.map((ev, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <span className="text-[var(--text-disabled)] tabular-nums shrink-0">{ev.time}</span>
                        <span className={ev.type === 'error' ? 'text-[var(--danger)] font-semibold' : ev.type === 'schedule' ? 'text-[var(--warning)]' : 'text-[var(--text-secondary)]'}>
                          {ev.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* ========================================================================= */}
            {/* 抽屉底部操作条 —— 严格根据 Frame 状态动态变化，严禁在 PASSED 下出现“跳过此帧” */}
            {/* ========================================================================= */}
            <div className="p-3 border-t border-[var(--border-subtle)] bg-[var(--bg-workspace)] shrink-0">
              {/* 1. PASSED 状态：查看原图 / 重新生成 / 日志 (跳过此帧绝不出现) */}
              {selectedFrame.status === 'PASSED' && (
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setImageModalUrl(selectedFrame.thumbnail || null)}
                    className="h-[32px] rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>查看原图</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setConfirmAction({ type: 'REGENERATE', frame: selectedFrame })}
                    className="h-[32px] rounded-[4px] bg-[var(--primary)] text-white font-medium hover:bg-[var(--primary)]/90 transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>重新生成</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab('logs');
                      setLogSearch(selectedFrame.frameCode);
                    }}
                    className="h-[32px] rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5"
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    <span>日志</span>
                  </button>
                </div>
              )}

              {/* 2. RUNNING 状态：查看运行 / 取消本次 */}
              {selectedFrame.status === 'GENERATING' && (
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab('logs');
                      setLogSearch(selectedFrame.frameCode);
                    }}
                    className="h-[32px] rounded-[4px] bg-[var(--primary)] text-white font-medium hover:bg-[var(--primary)]/90 transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    <span>查看运行日志</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setConfirmAction({ type: 'CANCEL', frame: selectedFrame })}
                    className="h-[32px] rounded-[4px] bg-[var(--danger)]/15 border border-[var(--danger)]/40 text-[var(--danger)] hover:bg-[var(--danger)]/25 transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>取消本次</span>
                  </button>
                </div>
              )}

              {/* 3. RETRYING 状态：立即重试 / 停止重试 / 日志 */}
              {selectedFrame.status === 'RETRYING' && (
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => handleImmediateRetry(selectedFrame)}
                    className="h-[32px] rounded-[4px] bg-[var(--warning)] text-black font-semibold hover:bg-[var(--warning)]/90 transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>立即重试</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setConfirmAction({ type: 'SKIP', frame: selectedFrame })}
                    className="h-[32px] rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-xs font-mono cursor-pointer"
                  >
                    停止并跳过
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab('logs');
                      setLogSearch(selectedFrame.frameCode);
                    }}
                    className="h-[32px] rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5"
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    <span>日志</span>
                  </button>
                </div>
              )}

              {/* 4. BLOCKED 状态：重试 / 强制通过 / 跳过此帧 */}
              {selectedFrame.status === 'BLOCKED' && (
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => handleImmediateRetry(selectedFrame)}
                    className="h-[32px] rounded-[4px] bg-[var(--primary)] text-white font-medium hover:bg-[var(--primary)]/90 transition-colors text-xs font-mono cursor-pointer"
                  >
                    重试修复
                  </button>

                  <button
                    type="button"
                    onClick={() => setConfirmAction({ type: 'FORCE_PASS', frame: selectedFrame })}
                    className="h-[32px] rounded-[4px] bg-[var(--success)]/15 border border-[var(--success)]/40 text-[var(--success)] hover:bg-[var(--success)]/25 transition-colors text-xs font-mono cursor-pointer"
                  >
                    强制通过
                  </button>

                  <button
                    type="button"
                    onClick={() => setConfirmAction({ type: 'SKIP', frame: selectedFrame })}
                    className="h-[32px] rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-xs font-mono cursor-pointer"
                  >
                    跳过此帧
                  </button>
                </div>
              )}

              {/* 5. QUEUED 状态：提前执行 / 取消排队 */}
              {selectedFrame.status === 'QUEUED' && (
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleImmediateRetry(selectedFrame)}
                    className="h-[32px] rounded-[4px] bg-[var(--primary)] text-white font-medium hover:bg-[var(--primary)]/90 transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5 shadow-sm"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>提前优先执行</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setConfirmAction({ type: 'CANCEL', frame: selectedFrame })}
                    className="h-[32px] rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors text-xs font-mono cursor-pointer"
                  >
                    取消排队
                  </button>
                </div>
              )}

              {/* 6. NOT_STARTED 状态：立即触发生成 */}
              {selectedFrame.status === 'NOT_STARTED' && (
                <button
                  type="button"
                  onClick={() => handleImmediateRetry(selectedFrame)}
                  className="w-full h-[32px] rounded-[4px] bg-[var(--primary)] text-white font-medium hover:bg-[var(--primary)]/90 transition-colors text-xs font-mono cursor-pointer flex items-center justify-center gap-1.5 shadow-sm"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>立即触发此帧渲染</span>
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 4. 二次确认模态框 (覆盖：重新生成、跳过、强制通过、取消本次) */}
      {/* ========================================================================= */}
      {confirmAction && (
        <div className="fixed inset-0 z-70 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[6px] max-w-sm w-full p-4 space-y-3.5 text-[var(--text-primary)] shadow-2xl animate-in fade-in">
            <div className="flex items-center gap-2 text-[var(--warning)] font-semibold text-sm">
              <AlertTriangle className="w-4 h-4 text-[var(--warning)] shrink-0" />
              <span>
                {confirmAction.type === 'REGENERATE' && `确认重新生成 ${confirmAction.frame.frameCode}？`}
                {confirmAction.type === 'SKIP' && `确认跳过 ${confirmAction.frame.frameCode}？`}
                {confirmAction.type === 'FORCE_PASS' && `确认强制放行 ${confirmAction.frame.frameCode}？`}
                {confirmAction.type === 'CANCEL' && `确认取消 ${confirmAction.frame.frameCode} 渲染？`}
              </span>
            </div>

            <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-sans">
              {confirmAction.type === 'REGENERATE' && '重新生成将覆盖当前分镜的产物图，并重新向推理引擎发起出图任务。'}
              {confirmAction.type === 'SKIP' && '跳过该帧将写入系统预设占位，并推进流水线至下一个分镜。后续可在分镜审核中单独补发。'}
              {confirmAction.type === 'FORCE_PASS' && '强制放行将跳过机器一致性质检，并直接标记该帧为 PASSED 状态。'}
              {confirmAction.type === 'CANCEL' && '取消本次渲染将立即中断 Worker 端的生成管线，并将任务回退至排队态。'}
            </p>

            <div className="flex justify-end gap-2 pt-1 font-mono text-xs">
              <button
                type="button"
                onClick={() => setConfirmAction(null)}
                className="h-[30px] px-3 rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-muted)] transition-colors cursor-pointer"
              >
                取消
              </button>
              <button
                type="button"
                onClick={executeDangerousAction}
                className="h-[30px] px-3.5 rounded-[4px] bg-[var(--primary)] text-white font-medium hover:bg-[var(--primary)]/90 transition-colors cursor-pointer shadow-sm"
              >
                确认执行
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. 高清原图全屏预览模态框 */}
      {/* ========================================================================= */}
      {imageModalUrl && (
        <div
          className="fixed inset-0 z-80 bg-black/90 flex items-center justify-center p-6 backdrop-blur-md"
          onClick={() => setImageModalUrl(null)}
        >
          <div className="relative max-w-4xl w-full max-h-[90vh] flex flex-col items-center">
            <button
              type="button"
              onClick={() => setImageModalUrl(null)}
              className="absolute -top-10 right-0 p-1.5 rounded-[4px] bg-[var(--bg-subtle)] border border-[var(--border-normal)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)] text-[var(--text-secondary)] cursor-pointer transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
            <img
              src={imageModalUrl}
              alt="High Res Preview"
              className="max-h-[85vh] object-contain rounded-[4px] border border-[var(--border-subtle)] shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </div>
  );
};
