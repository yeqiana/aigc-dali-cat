import React, { useState } from 'react';
import {
  Terminal,
  Cpu,
  Sliders,
  Camera,
  Layers,
  Copy,
  Check,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Zap,
  HardDrive
} from 'lucide-react';
import { RuntimeRequest } from '../types';

interface RuntimeRequestCardProps {
  runtime: RuntimeRequest;
}

export const RuntimeRequestCard: React.FC<RuntimeRequestCardProps> = ({ runtime }) => {
  const [copied, setCopied] = useState(false);
  const [showArchived, setShowArchived] = useState(false);

  const handleCopyParams = () => {
    const payload = {
      imageModel: runtime.imageModel || 'gpt-image-2',
      quality: runtime.quality || 'high',
      aspectRatio: runtime.aspectRatio || '4:5 1080×1350',
      batchMode: runtime.batchMode || '5 帧逻辑批次',
      maxConcurrentImages: runtime.maxConcurrentImages || 3,
      executionLayer: runtime.executionLayer || 'StoryOS Engine',
      source: runtime.sourceBadge || '待连接工作区',
      safetyFilter: runtime.safetyThreshold || 'Level-3',
    };
    navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Primary 6 authentic runtime specifications requested by user
  const primarySpecs = [
    {
      label: '图像模型',
      value: runtime.imageModel || 'gpt-image-2',
      subtext: '核心文生图大模型',
      icon: Cpu,
      highlight: true,
    },
    {
      label: '输出质量',
      value: runtime.quality || 'high',
      subtext: '高保真电影画质档位',
      icon: Sparkles,
      badge: 'HIGH',
    },
    {
      label: '正式画幅',
      value: runtime.aspectRatio || '4:5 1080×1350',
      subtext: '1080 × 1350 竖版标准',
      icon: Camera,
    },
    {
      label: '生产方式',
      value: runtime.batchMode || '5 帧逻辑批次',
      subtext: '分镜逻辑单元连续推演',
      icon: Layers,
    },
    {
      label: '最大同时出图',
      value: `${runtime.maxConcurrentImages || 3} 张`,
      subtext: '严格并发吞吐限制',
      icon: Zap,
    },
    {
      label: '图片执行层',
      value: runtime.executionLayer || 'StoryOS Engine',
      subtext: '任务分发与上下文编排',
      icon: Terminal,
      highlight: true,
    },
  ];

  return (
    <div id="runtime-request-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-zinc-100 gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-zinc-900 text-amber-400">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide">
                Runtime 生产执行配置
              </h3>
              {/* Workspace Connection / Example Data Badge */}
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-300 font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                <span>{runtime.sourceBadge || '待连接工作区'}</span>
              </span>
            </div>
            <p className="text-[11px] text-zinc-600 mt-0.5">
              StoryOS 官方标准生产协议 · 规范对应 runtime-request.json 映射规约，未连接 GitHub 前展示标准示例参数
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyParams}
            className="flex items-center gap-1 text-[11px] font-mono text-zinc-600 hover:text-zinc-900 px-2.5 py-1 rounded bg-zinc-50 hover:bg-zinc-100 border border-zinc-200 transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? '已复制标准配置' : '复制执行配置'}</span>
          </button>
        </div>
      </div>

      {/* Main 6 Authentic StoryOS Runtime Specs */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        {primarySpecs.map((spec, idx) => {
          const Icon = spec.icon;
          return (
            <div
              key={idx}
              className={`p-3 rounded-lg border transition-all ${
                spec.highlight
                  ? 'bg-amber-50/40 border-amber-200/80 shadow-2xs'
                  : 'bg-zinc-50/70 border-zinc-200/80'
              }`}
            >
              <div className="flex items-center justify-between text-zinc-500 text-[11px] font-mono mb-1.5">
                <span className="flex items-center gap-1">
                  <Icon className={`w-3.5 h-3.5 ${spec.highlight ? 'text-amber-600' : 'text-zinc-500'}`} />
                  <span className="text-zinc-600 font-medium">{spec.label}</span>
                </span>
                {spec.badge && (
                  <span className="text-[9px] font-mono font-bold px-1 py-0.2 rounded bg-amber-100 text-amber-900 border border-amber-300">
                    {spec.badge}
                  </span>
                )}
              </div>
              <div className="font-bold text-zinc-900 text-sm tracking-tight truncate font-mono" title={spec.value}>
                {spec.value}
              </div>
              <div className="text-[10px] text-zinc-500 truncate mt-1">
                {spec.subtext}
              </div>
            </div>
          );
        })}
      </div>

      {/* Concise Rules & Safety Strip */}
      <div className="mt-3 pt-2.5 border-t border-zinc-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 text-zinc-700 font-mono text-[11px]">
          <span className="px-1.5 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-800 font-bold">
            管线调度模式
          </span>
          <span className="text-zinc-600">
            5 帧逻辑批次锁定 ｜ 最大并发出图 <strong>3 张</strong> ｜ 画面比例 <strong>4:5 (1080×1350)</strong>
          </span>
        </div>

        {/* Collapsed view for unverified / legacy infrastructure metrics */}
        <button
          onClick={() => setShowArchived(!showArchived)}
          className="flex items-center gap-1 text-[11px] text-zinc-400 hover:text-zinc-600 font-mono transition-colors"
        >
          <span>{showArchived ? '收起非正式运行字段' : '展开已折叠的历史/未经真实支持字段'}</span>
          {showArchived ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* Folded / Archived Section */}
      {showArchived && (
        <div className="mt-2.5 p-3 rounded-lg bg-zinc-50 border border-dashed border-zinc-300 text-[11px] font-mono text-zinc-600 space-y-1.5 animate-in fade-in duration-150">
          <div className="flex items-center justify-between text-zinc-500 font-bold pb-1 border-b border-zinc-200">
            <span className="flex items-center gap-1 text-amber-800">
              <HardDrive className="w-3.5 h-3.5" />
              <span>已折叠字段（因未经真实运行记录支持已剥离主展示）</span>
            </span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-200 text-zinc-600">
              FOLDED_UNVERIFIED
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 text-zinc-600">
            <div>• 图片模型: {runtime.imageModel}</div>
            <div>• 批次策略: {runtime.batchMode}</div>
            <div>• 执行层: {runtime.executionLayer}</div>
          </div>
          <p className="text-[10px] text-zinc-400 pt-1">
            说明：依据 StoryOS 生产标准规范，未经真实云端调用支持的 GPU 算力型号、显存占用及固定 Seed 均已从主控制面板移除或折叠，防止误导生产流程。
          </p>
        </div>
      )}
    </div>
  );
};
