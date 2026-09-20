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
      // 黑白层级色彩：100%纯白，进行中灰白，已排期深灰
      fillColor: isDone ? '#ffffff' : (isInProgress ? '#a1a1aa' : (completedInBatch > 0 ? '#71717a' : '#27272a')),
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
    onShowToast('已导出当前剧集 4:5 资产清单与生产账本');
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#0a0a0c] border border-[#2e2e33] p-2 rounded-lg text-xs font-mono text-white shadow-2xl z-50">
          <div className="font-bold flex items-center justify-between gap-2 border-b border-[#1f1f23] pb-1 mb-1">
            <span className="text-white">{data.fullName}</span>
            <span className="text-[10px] text-zinc-400">{data.range}</span>
          </div>
          <div className="text-[11px] text-zinc-300 space-y-0.5">
            <div className="flex justify-between gap-3">
              <span className="text-zinc-400">状态:</span>
              <span className="text-white font-medium">{data.status}</span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-zinc-400">已产帧数:</span>
              <span className="text-white font-bold">{data.completed} / {data.total} 帧</span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-zinc-400">批次完成率:</span>
              <span className="text-white font-mono">{data.rate}%</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <aside className="w-64 sm:w-72 shrink-0 bg-[#000000] border-l border-[#1f1f23] flex flex-col h-full text-xs font-sans select-none text-zinc-300">
      <div className="p-3 space-y-4 overflow-y-auto scrollbar-none flex-1">
        {/* 0. 生产进度热力一览图 (Recharts) */}
        <div>
          <div className="flex items-center justify-between text-zinc-400 pb-1.5 border-b border-[#1f1f23] text-[11px] font-mono">
            <span className="text-white font-semibold flex items-center gap-1.5">
              <Flame className="w-3.5 h-3.5 text-white" />
              <span>生产进度热力一览</span>
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#141416] border border-[#27272a] text-white">
              {activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧 ({completionPercent}%)
            </span>
          </div>

          <div className="mt-2.5 p-2 rounded-xl bg-[#0a0a0c] border border-[#222226] space-y-2">
            {/* Recharts 批次热力柱状图 */}
            <div className="h-28 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={batchHeatData}
                  margin={{ top: 8, right: 4, left: -22, bottom: 0 }}
                >
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#71717a', fontSize: 10, fontFamily: 'monospace' }}
                    axisLine={{ stroke: '#222226' }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 5]}
                    ticks={[0, 2, 5]}
                    tick={{ fill: '#52525b', fontSize: 9, fontFamily: 'monospace' }}
                    axisLine={{ stroke: '#222226' }}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: '#141417' }} />
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
            <div className="pt-1.5 border-t border-[#1a1a1e]">
              <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 mb-1.5">
                <span>逐帧实施热力分布</span>
                <span className="text-zinc-500">共 {activeEpisode.totalFrames} 帧</span>
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
                          ? 'bg-white'
                          : isCurrentBatch
                          ? 'bg-zinc-600 animate-pulse'
                          : 'bg-[#18181b] border border-[#27272a]'
                      }`}
                    />
                  );
                })}
              </div>

              {/* 热力图例 */}
              <div className="flex items-center justify-between pt-2 text-[10px] font-mono text-zinc-400">
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-[2px] bg-white inline-block" />
                  <span>已交付</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-[2px] bg-zinc-600 inline-block" />
                  <span>出图中</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-2 h-2 rounded-[2px] bg-[#18181b] border border-[#27272a] inline-block" />
                  <span>未排期</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 1. 交付与成片切片 */}
        <div>
          <div className="flex items-center justify-between text-zinc-400 pb-1.5 border-b border-[#1f1f23] text-[11px] font-mono">
            <span className="text-white font-semibold">成片切片包</span>
            <button
              type="button"
              onClick={() => onShowToast('已新建切片配置')}
              className="p-1 hover:text-white rounded hover:bg-[#18181b] cursor-pointer"
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
              className="w-full text-left p-2 rounded-lg bg-[#0e0e11] hover:bg-[#18181b] border border-[#222226] cursor-pointer text-zinc-300 hover:text-white transition-colors flex items-center justify-between font-mono text-[11px]"
            >
              <div className="flex flex-col truncate">
                <span className="truncate text-white font-medium">release-manifest.json</span>
                <span className="text-[10px] text-zinc-400 font-sans">4:5 规格发布清单</span>
              </div>
              <span className="text-[10px] text-zinc-300 font-bold ml-1 shrink-0 px-1.5 py-0.5 rounded bg-black border border-[#27272a]">
                就绪
              </span>
            </button>

            <button
              type="button"
              onClick={() => onShowToast(`已归档 ${activeEpisode.completedFrames} 帧 4:5 高清成片切片包`)}
              className="w-full text-left p-2 rounded-lg bg-[#0e0e11] hover:bg-[#18181b] border border-[#222226] cursor-pointer text-zinc-300 hover:text-white transition-colors flex items-center justify-between font-mono text-[11px]"
            >
              <div className="flex flex-col truncate">
                <span className="truncate text-white font-medium">4:5 原画切片包</span>
                <span className="text-[10px] text-zinc-400 font-sans">标准 1080×1350 竖版</span>
              </div>
              <span className="text-[10px] text-white font-bold ml-1 shrink-0 px-1.5 py-0.5 rounded bg-white text-black">
                {activeEpisode.completedFrames}帧
              </span>
            </button>
          </div>
        </div>

        {/* 2. 来源与工作区账本（纯黑底白字） */}
        <div>
          <div className="flex items-center justify-between text-zinc-400 pb-1.5 border-b border-[#1f1f23] text-[11px] font-mono">
            <span className="text-white font-semibold">生产规则与账本</span>
            <button
              type="button"
              onClick={() => onShowToast('已添加自定义配置映射')}
              className="p-1 hover:text-white rounded hover:bg-[#18181b] cursor-pointer"
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
                className="w-full text-left p-2 rounded-lg bg-[#0e0e11] hover:bg-[#18181b] border border-[#222226] cursor-pointer text-zinc-300 hover:text-white transition-colors font-mono text-[11px]"
              >
                <div className="flex items-center gap-1.5 text-white font-medium">
                  <FileCode className="w-3 h-3 text-zinc-400 shrink-0" />
                  <span className="truncate">{file.name}</span>
                </div>
                <div className="text-[10px] text-zinc-400 font-sans mt-0.5 truncate">
                  {file.desc}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 底部一键打包导出 */}
      <div className="p-3 border-t border-[#1f1f23] bg-[#050507]">
        <button
          type="button"
          onClick={handleDownloadAll}
          className="w-full py-1.5 rounded-lg bg-white text-black hover:bg-zinc-200 font-semibold text-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
        >
          <Download className="w-3.5 h-3.5 text-black" />
          <span>导出当前剧集全量资产</span>
        </button>
      </div>

      {/* 纯黑底白字 JSON 查看弹窗 */}
      {activeJson && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs"
          onClick={() => setActiveJson(null)}
        >
          <div
            className="bg-[#0a0a0c] border border-[#2e2e33] rounded-2xl max-w-lg w-full p-4 text-white space-y-3 font-mono text-xs shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#1f1f23] pb-2">
              <span className="text-white font-bold">{activeJson.title}</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="px-2 py-0.5 rounded bg-[#18181b] border border-[#27272a] hover:bg-white hover:text-black transition-colors flex items-center gap-1 text-[11px] cursor-pointer"
                >
                  {copied ? <Check className="w-3 h-3 text-white" /> : <Copy className="w-3 h-3" />}
                  <span>{copied ? '已复制' : '复制 JSON'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveJson(null)}
                  className="text-zinc-400 hover:text-white px-1.5 py-0.5 rounded cursor-pointer"
                >
                  ✕
                </button>
              </div>
            </div>

            <pre className="max-h-80 overflow-y-auto bg-black p-3 rounded-xl border border-[#1f1f23] text-[11px] text-zinc-300 leading-relaxed scrollbar-thin select-all">
              {JSON.stringify(activeJson.json, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </aside>
  );
};
