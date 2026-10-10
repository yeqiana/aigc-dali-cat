import React, { useMemo, useState } from 'react';
import { AlertTriangle, Check, ChevronDown, Clipboard, Download, FileJson, PanelRightClose, ShieldCheck } from 'lucide-react';
import { Episode } from '../types';

interface ContextPanelProps {
  activeEpisode: Episode;
  onClose?: () => void;
  onShowToast: (message: string) => void;
}

const stringify = (payload: unknown) => JSON.stringify(payload, null, 2);
const safeName = (name: string) => name.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').slice(0, 64);
export const ContextPanel: React.FC<ContextPanelProps> = ({ activeEpisode, onClose, onShowToast }) => {
  const [openSection, setOpenSection] = useState<'evidence' | 'review' | 'request'>('evidence');
  const [copied, setCopied] = useState(false);
  const snapshot = useMemo(() => ({
    source_kind: 'web_console_workspace_snapshot',
    description: '本地前端投影，仅包含工作区已展示的记录；不是磁盘上的原始 JSON 文件、发布放行证据或实时报表',
    episode: {
      id: activeEpisode.id,
      code: activeEpisode.code,
      title: activeEpisode.title,
      current_stage_projection: activeEpisode.currentStage,
      completed_frames_projection: activeEpisode.completedFrames,
      total_frames_projection: activeEpisode.totalFrames,
      updated_at: activeEpisode.updatedAt,
    },
    runtime_request_projection: activeEpisode.runtimeRequest,
    frame_review_projection: activeEpisode.frameReviews ?? [],
    preflight_projection: activeEpisode.preflightChecks ?? [],
  }), [activeEpisode]);
  const reviews = activeEpisode.frameReviews ?? [];
  const checks = activeEpisode.preflightChecks ?? [];
  const failed = reviews.filter(review => review.verdict === 'FAIL');
  const warnings = reviews.filter(review => review.verdict === 'WARN');
  const blockers = checks.filter(check => check.status === 'blocking');
  const pass = reviews.filter(review => review.verdict === 'PASS').length;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(stringify(snapshot));
      setCopied(true);
      onShowToast('已复制工作区证据快照，不含原始权威文件');
    } catch {
      onShowToast('复制失败，请检查剪贴板权限');
    }
  };
  const handleExport = () => {
    try {
      const blob = new Blob([stringify(snapshot)], { type: 'application/json;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = safeName(activeEpisode.code || activeEpisode.id || 'story') + '-workspace-snapshot.json';
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 0);
      onShowToast('已请求下载工作区证据快照（不是生产账本或发布清单）');
    } catch {
      onShowToast('导出失败，未生成文件');
    }
  };

  return (
    <aside aria-label="当前故事证据检视" className="hidden 2xl:flex w-[304px] shrink-0 flex-col h-full border-l border-[var(--border-subtle)] bg-[var(--bg-workspace)] text-[var(--text-secondary)]">
      <div className="flex h-[60px] shrink-0 items-center justify-between px-4 border-b border-[var(--border-subtle)]">
        <h2 className="text-[13px] font-semibold text-[var(--text-primary)]">作品检视</h2>
        <button type="button" onClick={onClose} aria-label="关闭作品检视" title="关闭作品检视" className="p-1.5 hover:bg-[var(--bg-hover)] rounded-[4px]"><PanelRightClose size={16} /></button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        <div>
          <div className="text-[14px] font-semibold text-[var(--text-primary)] break-words">{activeEpisode.title}</div>
          <div className="mt-1 text-[11px] font-mono text-[var(--text-tertiary)]">{activeEpisode.code} · 更新于 {activeEpisode.updatedAt || '未知'}</div>
          <p className="mt-3 flex gap-2 text-[11px] leading-5 text-[var(--text-tertiary)]"><ShieldCheck className="shrink-0 mt-0.5" size={14}/> 工作区只读快照。页面不能证明当前生产 Worker 在线或发布门禁通过。</p>
        </div>
        <div className="grid grid-cols-3 divide-x divide-[var(--border-subtle)] border-y border-[var(--border-subtle)] py-3 text-center">
          <div><div className="text-[17px] font-semibold tabular-nums text-[var(--text-primary)]">{activeEpisode.completedFrames}/{activeEpisode.totalFrames}</div><div className="mt-1 text-[11px] text-[var(--text-tertiary)]">帧数快照</div></div>
          <div><div className="text-[17px] font-semibold tabular-nums text-[var(--text-primary)]">{pass}/{reviews.length}</div><div className="mt-1 text-[11px] text-[var(--text-tertiary)]">审核通过</div></div>
          <div><div className={"text-[17px] font-semibold tabular-nums " + (blockers.length ? 'text-[var(--danger)]' : 'text-[var(--text-primary)]')}>{blockers.length}</div><div className="mt-1 text-[11px] text-[var(--text-tertiary)]">已记录阻塞</div></div>
        </div>
        {(failed.length > 0 || warnings.length > 0) &&
          <section className="flex items-start gap-2 border-l-2 border-[var(--warning)] pl-3 text-[12px]">
            <AlertTriangle size={16} className="shrink-0 mt-0.5 text-[var(--warning)]"/>
            <div>逐帧审核记录：<strong>{failed.length} 项失败</strong>、{warnings.length} 项警告。请查看逐帧审核详情。</div>
          </section>}
        <section>
          <h3 className="text-[12px] font-semibold text-[var(--text-primary)] mb-2">证据投影</h3>
          <div className="border border-[var(--border-normal)] rounded-[5px] overflow-hidden">
            <div className="flex border-b border-[var(--border-subtle)]">
              {([{ key: 'evidence', label: '概览' }, { key: 'review', label: '审核' }, { key: 'request', label: '规格' }] as const).map(item => (
                <button key={item.key} type="button" onClick={() => setOpenSection(item.key)}
                  aria-pressed={openSection === item.key}
                  className={"flex-1 py-2 text-[11px] " + (openSection === item.key ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] font-semibold' : 'hover:bg-[var(--bg-hover)]')}>
                  {item.label}
                </button>
              ))}
            </div>
            <dl className="p-3 space-y-2 text-[12px]">
              {openSection === 'evidence' ? <>
                <div className="flex justify-between gap-3"><dt>当前阶段</dt><dd className="text-[var(--text-primary)] text-right">{activeEpisode.currentStage}</dd></div>
                <div className="flex justify-between gap-3"><dt>已记录审核</dt><dd className="text-[var(--text-primary)]">{reviews.length}</dd></div>
                <div className="flex justify-between gap-3"><dt>预检记录</dt><dd className="text-[var(--text-primary)]">{checks.length}</dd></div>
              </> : openSection === 'review' ? <>
                <div className="flex justify-between gap-3"><dt>通过</dt><dd>{pass}</dd></div>
                <div className="flex justify-between gap-3"><dt>警告</dt><dd>{warnings.length}</dd></div>
                <div className="flex justify-between gap-3"><dt>失败</dt><dd>{failed.length}</dd></div>
                <div className="flex justify-between gap-3"><dt>门禁阻塞</dt><dd>{blockers.length}</dd></div>
              </> : <>
                <div className="flex justify-between gap-3"><dt>模型</dt><dd className="text-right">{activeEpisode.runtimeRequest.imageModel || '未指定'}</dd></div>
                <div className="flex justify-between gap-3"><dt>画幅</dt><dd className="text-right">{activeEpisode.runtimeRequest.aspectRatio || '未指定'}</dd></div>
                <div className="flex justify-between gap-3"><dt>数据来源</dt><dd className="text-right">{activeEpisode.runtimeRequest.sourceBadge}</dd></div>
              </>}
            </dl>
          </div>
        </section>
        <section>
          <h3 className="text-[12px] font-semibold text-[var(--text-primary)] mb-2">导出与复查</h3>
          <p className="text-[11px] leading-5 text-[var(--text-tertiary)] mb-3">仅导出当前浏览器可见的工作区数据，不会假造 production-ledger.json、release-manifest.json 或费用记录。</p>
          <div className="flex gap-2">
            <button type="button" onClick={handleCopy} className="h-8 flex-1 flex items-center justify-center gap-1.5 border border-[var(--border-normal)] rounded-[5px] text-[12px] hover:bg-[var(--bg-hover)]">{copied ? <Check size={14}/> : <Clipboard size={14}/>} {copied ? '已复制' : '复制 JSON'}</button>
            <button type="button" onClick={handleExport} className="h-8 flex-1 flex items-center justify-center gap-1.5 border border-[var(--border-normal)] rounded-[5px] text-[12px] hover:bg-[var(--bg-hover)]"><Download size={14}/> 下载 JSON</button>
          </div>
          <p className="mt-3 text-[11px] text-[var(--text-tertiary)] flex items-start gap-1.5"><FileJson size={14} className="shrink-0 mt-0.5"/> 输出文件带 workspace-snapshot 后缀，避免误认为权威生产资产。</p>
        </section>
      </div>
    </aside>
  );
};
