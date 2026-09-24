import React from 'react';
import {
  GitBranch,
  Github,
  CheckCircle2,
  Clock,
  Lock,
  FileText,
  ShieldAlert,
  ExternalLink,
  RefreshCw,
  Database,
  Layers,
  Sparkles
} from 'lucide-react';
import { WorkspaceSyncStatus } from '../types';

interface WorkspaceSyncBannerProps {
  workspaceStatus?: WorkspaceSyncStatus;
  onConnectClick?: () => void;
}

export const WorkspaceSyncBanner: React.FC<WorkspaceSyncBannerProps> = ({
  workspaceStatus = {
    connected: false,
    readOnlyFiles: {
      episodeState: false,
      runtimeRequest: false,
      productionLedger: false,
      frameReviews: false,
      releaseManifest: false,
    },
  },
  onConnectClick,
}) => {
  const schemaFiles = [
    { name: 'episode-state.json', label: '阶段状态', field: '剧集当前阶段与阻断门禁' },
    { name: 'runtime-request.json', label: '运行配置', field: '模型、画幅与出图并发参数' },
    { name: 'production-ledger.json', label: '生产账本', field: '批次出图流水与资源审计' },
    { name: 'frame-reviews.json', label: '逐帧审核', field: '一致性分数与质检判定' },
    { name: 'release-manifest.json', label: '发布清册', field: '正式画幅 4:5 与分发元数据' },
  ];

  return (
    <div id="workspace-sync-banner" className="mb-5 rounded-xl border border-zinc-200 bg-white p-4 shadow-xs">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-zinc-100">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-zinc-900 text-amber-400 flex items-center justify-center shrink-0 shadow-xs">
            <Github className="w-5 h-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-xs font-bold text-zinc-900 tracking-wide">
                StoryOS 远端工程工作区状态 (GitHub Workspace)
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-300 font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                <span>待连接工作区 · 当前所有展示为示例数据</span>
              </span>
            </div>
            <p className="text-[11px] text-zinc-500 mt-0.5">
              安全架构纪律：未连接 GitHub 前所有剧集、人物、帧数、审核结果与配置均为<strong>示例数据</strong>；连接后前端<strong>只读映射</strong>文件，状态推进由 StoryOS 门禁执行。
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start lg:self-center shrink-0">
          <button
            onClick={onConnectClick}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-amber-300 text-xs font-bold transition-all shadow-xs"
          >
            <GitBranch className="w-3.5 h-3.5 text-amber-400" />
            <span>连接 GitHub 仓库</span>
          </button>
        </div>
      </div>

      {/* 5 Schema Read-only Mapping Contract Chips */}
      <div className="mt-3">
        <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider mb-2 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-amber-600" />
            <span>StoryOS 核心状态映射文件规约（连接后只读导入 · 前端禁止直接覆写）</span>
          </span>
          <span className="text-zinc-400">门禁规则: Read-Only Ingress</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          {schemaFiles.map((file, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg border border-zinc-200/80 bg-zinc-50/80 hover:bg-zinc-50 transition-all flex flex-col justify-between text-xs"
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="font-mono text-[11px] font-bold text-zinc-900 truncate" title={file.name}>
                  {file.name}
                </span>
                <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-zinc-200 text-zinc-600 font-semibold shrink-0">
                  待连接
                </span>
              </div>
              <div className="text-[10px] text-zinc-500 truncate" title={file.field}>
                {file.field}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
