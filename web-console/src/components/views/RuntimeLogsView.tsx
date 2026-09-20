import React, { useState } from 'react';
import {
  Terminal,
  Trash2,
  Download,
  Check
} from 'lucide-react';
import { SYSTEM_RUNTIME_LOGS } from '../../mockData';

export const RuntimeLogsView: React.FC = () => {
  const [logs, setLogs] = useState(SYSTEM_RUNTIME_LOGS);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [copied, setCopied] = useState(false);

  const filteredLogs = filterLevel === 'ALL'
    ? logs
    : logs.filter(l => l.level === filterLevel);

  const handleClear = () => {
    setLogs([]);
  };

  const handleCopyLogs = () => {
    const text = logs.map(l => `[${l.time}] [${l.level}] [${l.module}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div id="runtime-logs-view" className="space-y-4 text-[var(--text-secondary)] font-sans select-none">
      {/* 头部区 */}
      <div className="storyos-surface flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[var(--primary)]" />
              <span>StoryOS 生产运行记录与日志审计 (Production Audit)</span>
            </h2>
            <span className="storyos-status storyos-status--success font-mono">
              实时审计已启用
            </span>
          </div>
          <p className="text-xs text-[var(--text-tertiary)] mt-1">
            StoryOS 图像调度轨迹、gpt-image-2 (high) 出图队列流转与逐帧质检流水审计
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopyLogs}
            className="storyos-control h-9 flex items-center gap-1.5 px-3 text-xs font-mono transition-colors cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[var(--success)]" /> : <Download className="w-3.5 h-3.5" />}
            <span>{copied ? '已复制日志' : '复制日志'}</span>
          </button>
          <button
            type="button"
            onClick={handleClear}
            aria-label="清空前端日志视图"
            className="storyos-control h-9 w-9 flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--danger)] transition-colors cursor-pointer"
            title="清空日志"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 终端日志容器：与 StoryOS Neutral Dark 工作区统一，保留代码面语义。 */}
      <div className="bg-[var(--bg-app)] rounded-[var(--radius-md)] border border-[var(--border-normal)] text-[var(--text-secondary)] font-mono text-xs overflow-hidden">
        {/* Terminal 顶栏 */}
        <div className="p-3 bg-[var(--bg-workspace)] border-b border-[var(--border-subtle)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-[var(--text-disabled)]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[var(--text-disabled)]" />
              <div className="w-2.5 h-2.5 rounded-full bg-[var(--text-disabled)]" />
            </div>
            <span className="text-[11px] text-[var(--text-tertiary)] ml-2">stdout / storyos_pipeline.log</span>
          </div>

          <div className="flex items-center gap-1.5">
            {['ALL', 'INFO', 'SUCCESS', 'WARN'].map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setFilterLevel(lvl)}
                className={`px-2 py-1 rounded-[var(--radius-sm)] text-[10px] transition-colors cursor-pointer font-semibold border ${
                  filterLevel === lvl
                    ? 'bg-[var(--bg-selected)] text-[var(--text-primary)] border-[var(--border-strong)]'
                    : 'bg-[var(--bg-surface)] text-[var(--text-tertiary)] hover:text-[var(--text-primary)] border-[var(--border-subtle)] hover:bg-[var(--bg-hover)]'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {/* 日志流水 */}
        <div className="p-4 space-y-2 max-h-[500px] overflow-y-auto font-mono scrollbar-thin">
          {filteredLogs.length === 0 ? (
            <div className="py-8 text-center text-[var(--text-tertiary)] text-xs">暂无审计日志</div>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-3 py-1.5 border-b border-[var(--border-subtle)] text-xs">
                <span className="text-[var(--text-tertiary)] text-[11px] shrink-0">{log.time}</span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 ${
                  log.level === 'SUCCESS'
                    ? 'bg-[var(--success-soft)] text-[var(--success)] border border-[var(--success)]/25'
                    : log.level === 'WARN'
                    ? 'bg-[var(--warning-soft)] text-[var(--warning)] border border-[var(--warning)]/25'
                    : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'
                }`}>
                  {log.level}
                </span>
                <span className="text-[var(--text-primary)] shrink-0 font-semibold">[{log.module}]</span>
                <span className="text-[var(--text-secondary)] leading-relaxed select-text">{log.message}</span>
              </div>
            ))
          )}

          <div className="pt-3 text-[var(--text-tertiary)] text-[11px] flex items-center gap-2">
            <span>&gt; StoryOS 引擎待命中: gpt-image-2 (high), 4:5 1080×1350, 5-frame batch, concurrency 3...</span>
          </div>
        </div>
      </div>
    </div>
  );
};
