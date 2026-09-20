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
    <div id="runtime-request-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)] gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide">
                Runtime 生产执行配置
              </h3>
              {/* Workspace Connection / Example Data Badge */}
              <span className="storyos-status storyos-status--warning font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)] animate-pulse" />
                <span>{runtime.sourceBadge || '待连接工作区'}</span>
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
              StoryOS 官方标准生产协议 · 规范对应 runtime-request.json 映射规约，未连接 GitHub 前展示标准示例参数
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyParams}
            className="storyos-control h-9 flex items-center gap-1 px-2.5 text-[11px] font-mono transition-colors"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[var(--success)]" /> : <Copy className="w-3.5 h-3.5" />}
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
              className={`p-3 rounded-[var(--radius-md)] border transition-all ${
                spec.highlight
                  ? 'bg-[var(--primary-soft)] border-[var(--border-normal)] shadow-[var(--shadow-xs)]'
                  : 'bg-[var(--bg-subtle)] border-[var(--border-normal)]'
              }`}
            >
              <div className="flex items-center justify-between text-[var(--text-tertiary)] text-[11px] font-mono mb-1.5">
                <span className="flex items-center gap-1">
                  <Icon className={`w-3.5 h-3.5 ${spec.highlight ? 'text-[var(--primary)]' : 'text-[var(--text-tertiary)]'}`} />
                  <span className="text-[var(--text-secondary)] font-medium">{spec.label}</span>
                </span>
                {spec.badge && (
                  <span className="storyos-status storyos-status--info font-mono">
                    {spec.badge}
                  </span>
                )}
              </div>
              <div className="font-semibold text-[var(--text-primary)] text-sm tracking-tight truncate font-mono" title={spec.value}>
                {spec.value}
              </div>
              <div className="text-[10px] text-[var(--text-tertiary)] truncate mt-1">
                {spec.subtext}
              </div>
            </div>
          );
        })}
      </div>

      {/* Concise Rules & Safety Strip */}
      <div className="mt-3 pt-2.5 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 text-[var(--text-secondary)] font-mono text-[11px]">
          <span className="storyos-status storyos-status--neutral font-mono">
            管线调度模式
          </span>
          <span className="text-[var(--text-tertiary)]">
            5 帧逻辑批次锁定 ｜ 最大并发出图 <strong>3 张</strong> ｜ 画面比例 <strong>4:5 (1080×1350)</strong>
          </span>
        </div>

        {/* Collapsed view for unverified / legacy infrastructure metrics */}
        <button
          onClick={() => setShowArchived(!showArchived)}
          className="flex items-center gap-1 text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] font-mono transition-colors"
        >
          <span>{showArchived ? '收起非正式运行字段' : '展开已折叠的历史/未经真实支持字段'}</span>
          {showArchived ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {/* Folded / Archived Section */}
      {showArchived && (
        <div className="mt-2.5 p-3 rounded-[var(--radius-md)] bg-[var(--bg-subtle)] border border-dashed border-[var(--border-strong)] text-[11px] font-mono text-[var(--text-secondary)] space-y-1.5 animate-in fade-in duration-150">
          <div className="flex items-center justify-between text-[var(--text-tertiary)] font-semibold pb-1 border-b border-[var(--border-subtle)]">
            <span className="flex items-center gap-1 text-[var(--warning)]">
              <HardDrive className="w-3.5 h-3.5" />
              <span>已折叠字段（因未经真实运行记录支持已剥离主展示）</span>
            </span>
            <span className="storyos-status storyos-status--neutral font-mono">
              FOLDED_UNVERIFIED
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1 text-[var(--text-secondary)]">
            <div>• 实验底模: {runtime.modelName || 'StoryDiffusion (已弃用/未挂载)'}</div>
            <div>• 适配器: {runtime.baseLoRA || 'LoRA/ControlNet (未挂载)'}</div>
            <div>• 物理计算节点: {runtime.renderCluster || 'GPU型号/VRAM (未经真实记录)'}</div>
          </div>
          <p className="text-[10px] text-[var(--text-tertiary)] pt-1">
            说明：依据 StoryOS 生产标准规范，未经真实云端调用支持的 GPU 算力型号、显存占用及固定 Seed 均已从主控制面板移除或折叠，防止误导生产流程。
          </p>
        </div>
      )}
    </div>
  );
};
