import React, { useState } from 'react';
import { Plus, Copy, Check, FileCode, Download, Flame } from 'lucide-react';
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
      // 使用统一 UI token，避免热力图形成第二套颜色体系。
      fillColor: isDone
        ? 'var(--primary)'
        : (isInProgress ? 'var(--info)' : (completedInBatch > 0 ? 'var(--text-subtle)' : 'var(--border-strong)')),
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
      desc: '批次出图账本与种子',
      data: {
        batchId: activeEpisode.currentBatch.batchId,
        batchName: activeEpisode.currentBatch.batchName,
        frames: [16, 17, 18, 19, 20],
        model: 'gpt-image-2 (high)',
        aspectRatio: '4:5',
      }
    },
    {
      name: 'frame-reviews.json',
      desc: '逐帧质检与一致性分',
      data: activeEpisode.frameReviews
    },
  ];

  const handleCopy = () => {
    if (!activeJson) return;
    navigator.clipboard.writeText(JSON.stringify(activeJson.json, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
    onShowToast('JSON 配置已复制至剪贴板');
  };

  const handleDownloadAll = () => {
    const previewManifest = {
      authority: 'FRONTEND_DEMO_NON_AUTHORITY',
      episode: activeEpisode.code,
      currentStage: activeEpisode.currentStage,
      completedFrames: activeEpisode.completedFrames,
      totalFrames: activeEpisode.totalFrames,
      runtimeRequest: activeEpisode.runtimeRequest,
      note: 'Local Web Console preview only. This file does not advance StoryOS state.',
    };
    const blob = new Blob([JSON.stringify(previewManifest, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${activeEpisode.code}-web-console-preview.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    onShowToast('已下载本地 preview JSON · 非生产 Authority/Artifact');
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="storyos-elevated p-2 text-xs font-mono text-[var(--text-primary)] z-50">
          <div className="font-bold flex items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-1 mb-1">
            <span className="text-[var(--text-primary)]">{data.fullName}</span>
            <span className="text-[10px] text-[var(--text-tertiary)]">{data.range}</span>
          </div>
          <div className="text-[11px] text-[var(--text-secondary)] space-y-0.5">
            <div className="flex justify-between gap-3">
              <span className="text-[var(--text-tertiary)]">状态:</span>
              <span className="text-[var(--text-primary)] font-medium">{data.status}</span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-[var(--text-tertiary)]">已产帧数:</span>
              <span className="text-[var(--text-primary)] font-bold">{data.completed} / {data.total} 帧</span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-[var(--text-tertiary)]">批次完成率:</span>
              <span className="text-[var(--primary)] font-mono">{data.rate}%</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <aside className="storyos-drawer w-[var(--drawer-width)] max-w-[38vw] shrink-0 flex flex-col h-full text-xs font-sans select-none text-[var(--text-secondary)]">
      <div className="p-3 space-y-4 overflow-y-auto scrollbar-none flex-1">
        {/* 0. 生产进度热力一览图 (Recharts) */}
        <div>
          <div className="flex items-center justify-between text-[var(--text-tertiary)] pb-1.5 border-b border-[var(--border-subtle)] text-[11px] font-mono">
            <span className="text-[var(--text-primary)] font-semibold flex items-center gap-1.5">
              <Flame className="w-3.5 h-3.5 text-[var(--primary)]" />
              <span>生产进度热力一览</span>
            </span>
            <span className="storyos-status storyos-status--info font-mono">
              {activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧 ({completionPercent}%)
            </span>
          </div>

          <div className="mt-2.5 p-2 rounded-[var(--radius-md)] bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
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
                    axisLine={{ stroke: 'var(--border-normal)' }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 5]}
                    ticks={[0, 2, 5]}
                    tick={{ fill: 'var(--text-subtle)', fontSize: 9, fontFamily: 'monospace' }}
                    axisLine={{ stroke: 'var(--border-normal)' }}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: 'var(--bg-muted)' }} />
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
                <span className="text-[var(--text-subtle)]">共 {activeEpisode.totalFrames} 帧</span>
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
                          ? 'bg-[var(--primary)]'
                          : isCurrentBatch
                          ? 'bg-[var(--info)]'
                          : 'bg-[var(--bg-muted)] border border-[var(--border-normal)]'
                      }`}
                    />
                  );
                })}
              </div>

              {/* 热力图例 */}
              <div className="flex items-center justify-between pt-2 text-[10px] font-mono text-[var(--text-tertiary)]">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-[2px] bg-[var(--primary)] inline-block" />
                  <span>已交付</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-[2px] bg-[var(--info)] inline-block" />
                  <span>出图中</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-[2px] bg-[var(--bg-muted)] border border-[var(--border-normal)] inline-block" />
                  <span>未排期</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 1. 交付与成片切片 */}
        <div>
          <div className="flex items-center justify-between text-[var(--text-tertiary)] pb-1.5 border-b border-[var(--border-subtle)] text-[11px] font-mono">
            <span className="text-[var(--text-primary)] font-semibold">成片切片包</span>
            <button
              type="button"
              disabled
              aria-label="新增切片规则暂不可用"
              className="p-1 text-[var(--text-disabled)] rounded-[var(--radius-sm)] cursor-not-allowed"
              title="未接入写 API，前端禁止新增切片规则"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="mt-2 space-y-1.5">
            <button
              type="button"
              onClick={() => setActiveJson({
                title: 'release-manifest.preview.json',
                json: {
                  authority: 'FRONTEND_DEMO_NON_AUTHORITY',
                  status: 'PREVIEW_ONLY',
                  episode: activeEpisode.code,
                  aspectRatio: '4:5 1080×1350',
                  completedFrames: activeEpisode.completedFrames,
                  totalFrames: activeEpisode.totalFrames,
                  qaGate: 'DEMO_ONLY'
                }
              })}
              className="w-full text-left p-2 rounded-[var(--radius-md)] bg-[var(--bg-surface)] hover:bg-[var(--bg-subtle)] border border-[var(--border-normal)] cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors flex items-center justify-between font-mono text-[11px]"
            >
              <div className="flex flex-col truncate">
                <span className="truncate text-[var(--text-primary)] font-medium">release-manifest.preview.json</span>
                <span className="text-[10px] text-[var(--text-tertiary)] font-sans">前端预览 · 非发布 Authority</span>
              </div>
              <span className="storyos-status storyos-status--neutral ml-1 shrink-0 font-mono">
                PREVIEW
              </span>
            </button>

            <button
              type="button"
              onClick={() => onShowToast(`前端示例：当前显示 ${activeEpisode.completedFrames} 帧，不代表已归档生产资产`)}
              className="w-full text-left p-2 rounded-[var(--radius-md)] bg-[var(--bg-surface)] hover:bg-[var(--bg-subtle)] border border-[var(--border-normal)] cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors flex items-center justify-between font-mono text-[11px]"
            >
              <div className="flex flex-col truncate">
                <span className="truncate text-[var(--text-primary)] font-medium">4:5 原画切片预览</span>
                <span className="text-[10px] text-[var(--text-tertiary)] font-sans">示例计数 · 未验证 Artifact</span>
              </div>
              <span className="storyos-status storyos-status--success ml-1 shrink-0 font-mono">
                {activeEpisode.completedFrames}帧
              </span>
            </button>
          </div>
        </div>

        {/* 2. 来源与工作区账本 */}
        <div>
          <div className="flex items-center justify-between text-[var(--text-tertiary)] pb-1.5 border-b border-[var(--border-subtle)] text-[11px] font-mono">
            <span className="text-[var(--text-primary)] font-semibold">生产规则与账本</span>
            <button
              type="button"
              disabled
              aria-label="添加来源映射暂不可用"
              className="p-1 text-[var(--text-disabled)] rounded-[var(--radius-sm)] cursor-not-allowed"
              title="未接入写 API，前端禁止添加来源映射"
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
                className="w-full text-left p-2 rounded-[var(--radius-md)] bg-[var(--bg-surface)] hover:bg-[var(--bg-subtle)] border border-[var(--border-normal)] cursor-pointer text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors font-mono text-[11px]"
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

      {/* 底部本地 preview 导出：真实下载文件，但不冒充生产 Artifact。 */}
      <div className="p-3 border-t border-[var(--border-normal)] bg-[var(--bg-surface)]">
        <button
          type="button"
          onClick={handleDownloadAll}
          className="w-full h-9 rounded-[var(--radius-md)] bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] font-semibold text-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
        >
          <Download className="w-3.5 h-3.5 text-white" />
          <span>下载本地 Preview JSON</span>
        </button>
      </div>

      {/* JSON 查看弹窗：壳层沿用工作台，代码区保持高对比。 */}
      {activeJson && (
        <div
          className="storyos-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={() => setActiveJson(null)}
        >
          <div
            className="storyos-elevated rounded-[var(--radius-lg)] max-w-lg w-full p-4 text-[var(--text-primary)] space-y-3 font-mono text-xs"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-2">
              <span className="text-[var(--text-primary)] font-bold">{activeJson.title}</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="px-2 py-1 rounded-[var(--radius-sm)] bg-[var(--bg-surface)] border border-[var(--border-normal)] hover:bg-[var(--bg-subtle)] transition-colors flex items-center gap-1 text-[11px] cursor-pointer"
                >
                  {copied ? <Check className="w-3 h-3 text-[var(--success)]" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? '已复制' : '复制 JSON'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveJson(null)}
                  aria-label="关闭 JSON 预览"
                  className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-1.5 py-0.5 rounded cursor-pointer"
                >
                  ✕
                </button>
              </div>
            </div>

            <pre className="max-h-80 overflow-y-auto bg-[var(--text-primary)] p-3 rounded-[var(--radius-md)] border border-[var(--border-strong)] text-[11px] text-slate-200 leading-relaxed scrollbar-thin select-all">
              {JSON.stringify(activeJson.json, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </aside>
  );
};
