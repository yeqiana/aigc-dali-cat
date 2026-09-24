import React, { useState } from 'react';
import { Plus, Copy, Check, FileCode, Download, Flame, ChevronDown } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell
} from 'recharts';
import { Episode } from '../types';

interface ContextPanelProps {
  activeEpisode: Episode;
  onClose?: () => void;
  onShowToast: (msg: string) => void;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({
  activeEpisode,
  onClose,
  onShowToast,
}) => {
  const [activeJson, setActiveJson] = useState<{ title: string; json: any } | null>(null);
  const [copied, setCopied] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(false); // 默认隐藏生产热力图

  // 计算批次热力数据 (基于每批 5 帧)
  const batchSize = 5;
  const totalBatches = Math.max(1, Math.ceil(activeEpisode.totalFrames / batchSize));
  const batchHeatData = Array.from({ length: totalBatches }, (_, i) => {
    const batchNum = i + 1;
    const startFrame = i * batchSize + 1;
    const endFrame = Math.min(activeEpisode.totalFrames, (i + 1) * batchSize);
    const totalInBatch = endFrame - startFrame + 1;

    // 计算已完成帧数
    const completedInBatch = Math.max(0, Math.min(totalInBatch, activeEpisode.completedFrames - (startFrame - 1)));
    const rate = Math.round((completedInBatch / totalInBatch) * 100);
    const isDone = completedInBatch === totalInBatch;
    const isInProgress = completedInBatch > 0 && completedInBatch < totalInBatch;

    return {
      batchKey: `B${batchNum}`,
      name: `B${batchNum}`,
      fullName: `第${batchNum}批次`,
      range: `#${startFrame}-#${endFrame}`,
      completed: completedInBatch,
      total: totalInBatch,
      rate,
      fillColor: isDone ? '#58A6FF' : (isInProgress ? '#3FB950' : '#8B949E'),
      status: isDone ? '已交付' : (isInProgress ? '生产中' : '待调度'),
    };
  });

  const completionPercent = Math.round((activeEpisode.completedFrames / activeEpisode.totalFrames) * 100);

  const specFiles = [
    {
      name: 'episode-state.json',
      desc: '剧集生产阶段与全帧状态',
      data: {
        episodeId: activeEpisode.code,
        title: activeEpisode.title,
        currentStage: activeEpisode.currentStage,
        completedFrames: activeEpisode.completedFrames,
        totalFrames: activeEpisode.totalFrames,
        aspectRatio: '4:5 (1080×1350)',
        qaStatus: '严格门禁已启用',
      }
    },
    {
      name: 'runtime-request.json',
      desc: '生图引擎与并发规格',
      data: activeEpisode.runtimeRequest
    },
    {
      name: 'production-ledger.json',
      desc: '4:5 资产生产与消耗账本',
      data: {
        totalGpuSeconds: 842.5,
        estimatedCostYuan: '¥14.2',
        retryTimes: 2,
        anomalyInterceptions: 1,
      }
    }
  ];

  const handleCopy = () => {
    if (!activeJson) return;
    navigator.clipboard.writeText(JSON.stringify(activeJson.json, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
    onShowToast('JSON 配置已复制至剪贴板');
  };

  const handleDownloadAll = () => {
    onShowToast('已导出当前剧集 4:5 资产清单与生产账本');
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[var(--bg-elevated)] border border-[var(--border-normal)] p-2 rounded-[6px] text-xs font-mono text-[var(--text-primary)] shadow-2xl z-50">
          <div className="font-bold flex items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-1 mb-1">
            <span>{data.fullName}</span>
            <span className="text-[10px] text-[var(--text-tertiary)]">{data.range}</span>
          </div>
          <div className="text-[11px] text-[var(--text-secondary)] space-y-0.5">
            <div className="flex justify-between gap-3">
              <span className="text-[var(--text-tertiary)]">状态:</span>
              <span className="font-medium text-[var(--text-primary)]">{data.status}</span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-[var(--text-tertiary)]">已产帧数:</span>
              <span className="font-bold text-[var(--text-primary)]">{data.completed} / {data.total} 帧</span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-[var(--text-tertiary)]">批次完成率:</span>
              <span className="font-mono text-[#58A6FF]">{data.rate}%</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <aside className="w-64 sm:w-72 shrink-0 bg-[var(--bg-workspace)] border-l border-[var(--border-subtle)] flex flex-col h-full text-xs font-sans select-none text-[var(--text-secondary)]">
      <div className="p-3 space-y-4 overflow-y-auto scrollbar-none flex-1">
        {/* 0. 生产进度热力一览图 (默认隐藏，点击可展开) */}
        <div className="rounded-[6px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] overflow-hidden">
          <button
            type="button"
            onClick={() => setShowHeatmap(!showHeatmap)}
            className="w-full flex items-center justify-between p-2.5 text-[11px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
          >
            <span className="font-semibold flex items-center gap-1.5 text-[var(--text-primary)]">
              <Flame className="w-3.5 h-3.5 text-[#58A6FF]" />
              <span>生产热力图</span>
            </span>
            <div className="flex items-center gap-1.5 text-[10px] text-[var(--text-tertiary)]">
              <span className="font-mono text-[var(--text-secondary)] font-medium">{activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧 ({completionPercent}%)</span>
              <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-tertiary)] transition-transform ${showHeatmap ? 'rotate-180' : ''}`} />
            </div>
          </button>

          {showHeatmap && (
            <div className="p-2 border-t border-[var(--border-subtle)] space-y-2 bg-[var(--bg-elevated)]">
              {/* Recharts 批次热力柱状图 */}
              <div className="h-28 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={batchHeatData}
                    margin={{ top: 8, right: 4, left: -22, bottom: 0 }}
                  >
                    <XAxis
                      dataKey="name"
                      tick={{ fill: 'var(--text-tertiary)', fontSize: 10, fontFamily: 'monospace' }}
                      axisLine={{ stroke: 'var(--border-subtle)' }}
                      tickLine={false}
                    />
                    <YAxis
                      domain={[0, 5]}
                      ticks={[0, 2, 5]}
                      tick={{ fill: 'var(--text-tertiary)', fontSize: 9, fontFamily: 'monospace' }}
                      axisLine={{ stroke: 'var(--border-subtle)' }}
                      tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-hover)' }} />
                    <Bar
                      dataKey="completed"
                      radius={[3, 3, 0, 0]}
                      isAnimationActive={false}
                    >
                      {batchHeatData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={entry.fillColor}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* 逐帧微型热力网格 (展示全帧 32 格) */}
              <div className="pt-1.5 border-t border-[var(--border-subtle)]">
                <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-tertiary)] mb-1.5">
                  <span>逐帧实施热力分布</span>
                  <span>共 {activeEpisode.totalFrames} 帧</span>
                </div>
                <div className="grid grid-cols-8 gap-1">
                  {Array.from({ length: activeEpisode.totalFrames }, (_, idx) => {
                    const frameIndex = idx + 1;
                    const isDone = frameIndex <= activeEpisode.completedFrames;
                    const isCurrentBatch = frameIndex > activeEpisode.completedFrames && frameIndex <= activeEpisode.completedFrames + 5;

                    return (
                      <div
                        key={frameIndex}
                        title={`Frame #${frameIndex} · ${isDone ? '已质检交付 (PASS)' : (isCurrentBatch ? '当前正在出图' : '待调度队列')}`}
                        className={`h-2.5 rounded-[2px] transition-colors cursor-help ${
                          isDone
                            ? 'bg-[#58A6FF]'
                            : isCurrentBatch
                            ? 'bg-amber-400 animate-pulse'
                            : 'bg-[var(--bg-surface)] border border-[var(--border-subtle)]'
                        }`}
                      />
                    );
                  })}
                </div>

                {/* 热力图例 */}
                <div className="flex items-center justify-between pt-2 text-[10px] font-mono text-[var(--text-tertiary)]">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-[2px] bg-[#58A6FF] inline-block" />
                    <span>已交付</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-[2px] bg-amber-400 inline-block" />
                    <span>出图中</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-[2px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] inline-block" />
                    <span>未排期</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 1. 交付与成片切片 */}
        <div>
          <div className="flex items-center justify-between text-[var(--text-tertiary)] pb-1.5 border-b border-[var(--border-subtle)] text-[11px] font-mono">
            <span className="text-[var(--text-primary)] font-semibold">成片切片包</span>
            <button
              type="button"
              onClick={() => onShowToast('已新建切片配置')}
              className="p-1 hover:text-[var(--text-primary)] rounded hover:bg-[var(--bg-hover)] cursor-pointer"
              title="添加新切片规则"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="mt-2 space-y-1.5">
            <button
              type="button"
              onClick={() => setActiveJson({
                title: 'release-manifest.json',
                json: {
                  status: '待终审放行',
                  episode: activeEpisode.code,
                  aspectRatio: '4:5 1080×1350',
                  completedFrames: activeEpisode.completedFrames,
                  totalFrames: activeEpisode.totalFrames,
                  qaGate: 'PASS'
                }
              })}
              className="w-full text-left p-2 rounded-[4px] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors flex items-center justify-between font-mono text-[11px]"
            >
              <div className="flex flex-col truncate">
                <span className="truncate text-[var(--text-primary)] font-medium">release-manifest.json</span>
                <span className="text-[10px] text-[var(--text-tertiary)] font-sans">4:5 规格发布清单</span>
              </div>
              <span className="text-[10px] text-[var(--text-secondary)] font-bold ml-1 shrink-0 px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-normal)]">
                就绪
              </span>
            </button>

            <button
              type="button"
              onClick={() => onShowToast(`已归档 ${activeEpisode.completedFrames} 帧 4:5 高清成片切片包`)}
              className="w-full text-left p-2 rounded-[4px] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors flex items-center justify-between font-mono text-[11px]"
            >
              <div className="flex flex-col truncate">
                <span className="truncate text-[var(--text-primary)] font-medium">4:5 原画切片包</span>
                <span className="text-[10px] text-[var(--text-tertiary)] font-sans">标准 1080×1350 竖版</span>
              </div>
              <span className="text-[10px] text-[var(--text-primary)] font-bold ml-1 shrink-0 px-1.5 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-normal)]">
                {activeEpisode.completedFrames}帧
              </span>
            </button>
          </div>
        </div>

        {/* 2. 生产规则与账本 */}
        <div>
          <div className="flex items-center justify-between text-[var(--text-tertiary)] pb-1.5 border-b border-[var(--border-subtle)] text-[11px] font-mono">
            <span className="text-[var(--text-primary)] font-semibold">生产规则与账本</span>
            <button
              type="button"
              onClick={() => onShowToast('已添加自定义配置映射')}
              className="p-1 hover:text-[var(--text-primary)] rounded hover:bg-[var(--bg-hover)] cursor-pointer"
              title="添加来源映射"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="mt-2 space-y-1.5">
            {specFiles.map((file) => (
              <button
                key={file.name}
                type="button"
                onClick={() => setActiveJson({ title: file.name, json: file.data })}
                className="w-full text-left p-2 rounded-[4px] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors font-mono text-[11px]"
              >
                <div className="flex items-center gap-1.5 text-[var(--text-primary)] font-medium">
                  <FileCode className="w-3 h-3 text-[var(--text-tertiary)] shrink-0" />
                  <span className="truncate">{file.name}</span>
                </div>
                <div className="text-[10px] text-[var(--text-tertiary)] font-sans mt-0.5 truncate">
                  {file.desc}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 底部一键打包导出 */}
      <div className="p-3 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)]">
        <button
          type="button"
          onClick={handleDownloadAll}
          className="w-full py-1.5 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] hover:opacity-90 font-semibold text-xs transition-opacity flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
        >
          <Download className="w-3.5 h-3.5" />
          <span>导出当前剧集全量资产</span>
        </button>
      </div>

      {/* 结构化 JSON 查看弹窗 */}
      {activeJson && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 backdrop-blur-xs"
          onClick={() => setActiveJson(null)}
        >
          <div
            className="bg-[var(--bg-elevated)] border border-[var(--border-normal)] rounded-[8px] max-w-lg w-full p-4 text-[var(--text-primary)] space-y-3 font-mono text-xs shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2">
              <span className="font-bold text-[var(--text-primary)]">{activeJson.title}</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="px-2 py-0.5 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors flex items-center gap-1 text-[11px] cursor-pointer"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? '已复制' : '复制 JSON'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveJson(null)}
                  className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-1.5 py-0.5 rounded-[4px] cursor-pointer"
                >
                  ✕
                </button>
              </div>
            </div>

            <pre className="max-h-80 overflow-y-auto bg-[var(--bg-app)] p-3 rounded-[6px] border border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] leading-relaxed scrollbar-thin select-all">
              {JSON.stringify(activeJson.json, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </aside>
  );
};
