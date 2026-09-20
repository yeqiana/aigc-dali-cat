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
            <span>{copied ? '已复制日志' : '导出日志'}</span>
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="storyos-control h-9 w-9 flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--danger)] transition-colors cursor-pointer"
            title="清空日志"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 终端日志容器：工程日志保持深色代码面，外围工作台仍遵守浅色系统。 */}
      <div className="bg-[var(--text-primary)] rounded-[var(--radius-lg)] border border-[var(--border-strong)] text-slate-200 font-mono text-xs overflow-hidden shadow-[var(--shadow-sm)]">
        {/* Terminal 顶栏 */}
        <div className="p-3 bg-slate-950/35 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
              <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
              <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
            </div>
            <span className="text-[11px] text-slate-400 ml-2">stdout / storyos_pipeline.log</span>
          </div>

          <div className="flex items-center gap-1.5">
            {['ALL', 'INFO', 'SUCCESS', 'WARN'].map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setFilterLevel(lvl)}
                className={`px-2 py-1 rounded-[var(--radius-sm)] text-[10px] transition-colors cursor-pointer font-semibold border ${
                  filterLevel === lvl
                    ? 'bg-white text-slate-950 border-white'
                    : 'bg-white/5 text-slate-400 hover:text-white border-white/10 hover:bg-white/10'
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
            <div className="py-8 text-center text-slate-500 text-xs">暂无审计日志</div>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-3 py-1.5 border-b border-white/5 text-xs">
                <span className="text-slate-500 text-[11px] shrink-0">{log.time}</span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 ${
                  log.level === 'SUCCESS'
                    ? 'bg-emerald-400/15 text-emerald-300 border border-emerald-400/20'
                    : log.level === 'WARN'
                    ? 'bg-amber-400/15 text-amber-300 border border-amber-400/20'
                    : 'bg-white/5 text-slate-300 border border-white/10'
                }`}>
                  {log.level}
                </span>
                <span className="text-slate-100 shrink-0 font-semibold">[{log.module}]</span>
                <span className="text-slate-300 leading-relaxed select-text">{log.message}</span>
              </div>
            ))
          )}

          <div className="pt-3 text-slate-500 text-[11px] flex items-center gap-2 animate-pulse">
            <span>&gt; StoryOS 引擎待命中: gpt-image-2 (high), 4:5 1080×1350, 5-frame batch, concurrency 3...</span>
          </div>
        </div>
      </div>
    </div>
  );
};
