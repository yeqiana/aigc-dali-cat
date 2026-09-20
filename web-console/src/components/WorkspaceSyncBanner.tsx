import React from 'react';
import {
  Database,
  Layers,
} from 'lucide-react';
import { WorkspaceSyncStatus } from '../types';

interface WorkspaceSyncBannerProps {
  workspaceStatus?: WorkspaceSyncStatus;
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
}) => {
  const schemaFiles = [
    { name: 'episode-state.json', label: '阶段状态', field: '剧集当前阶段与阻断门禁' },
    { name: 'runtime-request.json', label: '运行配置', field: '模型、画幅与出图并发参数' },
    { name: 'production-ledger.json', label: '生产账本', field: '批次出图流水与资源审计' },
    { name: 'frame-reviews.json', label: '逐帧审核', field: '一致性分数与质检判定' },
    { name: 'release-manifest.json', label: '发布清册', field: '正式画幅 4:5 与分发元数据' },
  ];

  return (
    <div id="workspace-sync-banner" className="storyos-surface mb-5 p-4">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pb-3 border-b border-[var(--border-subtle)]">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-9 h-9 rounded-[var(--radius-md)] bg-[var(--primary-soft)] text-[var(--primary)] flex items-center justify-center shrink-0">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide">
                StoryOS Workspace Provider
              </h3>
              <span className="storyos-status storyos-status--warning font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--warning)]" />
                <span>WebCodex Provider · Episode 映射尚未接入</span>
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
              当前 Production Console 仍使用<strong>前端示例 Episode 数据</strong>；WebCodex 只提供 Workspace 访问，不拥有 Episode Authority。后续接入真实 Episode 投影后仍保持<strong>只读映射</strong>，阶段推进只由 StoryOS canonical transition 执行。
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start lg:self-center shrink-0">
          <a
            href="/platform"
            className="h-9 flex items-center gap-1.5 px-3 rounded-[var(--radius-md)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-normal)] text-[var(--text-primary)] text-xs font-semibold transition-colors"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>打开 Platform Console</span>
          </a>
        </div>
      </div>

      {/* 5 Schema Read-only Mapping Contract Chips */}
      <div className="mt-3">
        <div className="text-[10px] font-mono text-[var(--text-tertiary)] uppercase tracking-wider mb-2 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-[var(--primary)]" />
            <span>StoryOS 核心状态映射规约（真实投影接入后只读 · 前端禁止直接覆写）</span>
          </span>
          <span className="text-[var(--text-subtle)]">门禁规则: Read-Only Ingress</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2">
          {schemaFiles.map((file, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-[var(--radius-md)] border border-[var(--border-normal)] bg-[var(--bg-subtle)] hover:bg-[var(--bg-muted)] transition-colors flex flex-col justify-between text-xs"
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="font-mono text-[11px] font-semibold text-[var(--text-primary)] truncate" title={file.name}>
                  {file.name}
                </span>
                <span className="storyos-status storyos-status--neutral font-mono shrink-0">
                  示例
                </span>
              </div>
              <div className="text-[10px] text-[var(--text-tertiary)] truncate" title={file.field}>
                {file.field}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
