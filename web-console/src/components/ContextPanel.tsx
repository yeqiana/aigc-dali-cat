import React, { useState } from 'react';
import { Plus, Copy, Check, FileCode, Download, Flame } from 'lucide-react';
import { Episode } from '../types';

interface ContextPanelProps {
  activeEpisode: Episode;
  onShowToast: (msg: string) => void;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({
  activeEpisode,
  onShowToast,
}) => {
  const [activeJson, setActiveJson] = useState<{ title: string; json: unknown } | null>(null);
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
      fillColor: isDone
        ? 'var(--primary)'
        : (isInProgress ? 'var(--info)' : 'var(--border-strong)'),
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

  return (
    <aside className="storyos-drawer w-[var(--drawer-width)] max-w-[38vw] shrink-0 flex flex-col h-full text-xs font-sans select-none text-[var(--text-secondary)]">
      <div className="p-3 space-y-4 overflow-y-auto scrollbar-none flex-1">
        {/* 0. 生产进度热力一览图：轻量 CSS 批次柱，不引入图表运行时。 */}
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
            <div className="h-28 w-full flex items-end gap-1.5 px-1 pt-1">
              {batchHeatData.map((entry) => (
                <div
                  key={entry.batchKey}
                  className="flex-1 min-w-0 h-full flex flex-col justify-end gap-1 cursor-help"
                  title={`${entry.fullName} ${entry.range} · ${entry.status} · ${entry.completed}/${entry.total} 帧 · ${entry.rate}%`}
                >
                  <div className="text-[9px] font-mono text-[var(--text-tertiary)] text-center tabular-nums">
                    {entry.completed}/{entry.total}
                  </div>
                  <div className="relative h-20 rounded-[2px] bg-[var(--bg-muted)] border border-[var(--border-subtle)] overflow-hidden">
                    <div
                      className="absolute inset-x-0 bottom-0 rounded-[2px]"
                      style={{
                        height: `${Math.max(entry.rate, entry.completed > 0 ? 8 : 0)}%`,
                        backgroundColor: entry.fillColor,
                      }}
                    />
                  </div>
                  <div className="text-[9px] font-mono text-[var(--text-tertiary)] text-center truncate">
                    {entry.name}
                  </div>
                </div>
              ))}
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
            role="dialog"
            aria-modal="true"
            aria-label={`${activeJson.title} JSON 预览`}
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
