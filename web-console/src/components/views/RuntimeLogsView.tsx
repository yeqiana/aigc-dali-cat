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
    <div id="runtime-logs-view" className="space-y-4 text-zinc-300 font-sans select-none">
      {/* 头部区 - 纯黑底白字 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#0a0a0c] p-4 rounded-xl border border-[#222226]">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Terminal className="w-4 h-4 text-white" />
              <span>StoryOS 生产运行记录与日志审计 (Production Audit)</span>
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-black font-bold">
              实时审计已启用
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            StoryOS 图像调度轨迹、gpt-image-2 (high) 出图队列流转与逐帧质检流水审计
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopyLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#141416] border border-[#27272a] hover:bg-[#1a1a1e] hover:text-white text-xs font-mono text-zinc-300 transition-colors cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-white" /> : <Download className="w-3.5 h-3.5" />}
            <span>{copied ? '已复制日志' : '导出日志'}</span>
          </button>
          <button
            type="button"
            onClick={handleClear}
            className="p-1.5 rounded-lg bg-[#141416] border border-[#27272a] hover:bg-[#1a1a1e] hover:text-white text-zinc-400 transition-colors cursor-pointer"
            title="清空日志"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 终端日志容器（纯黑底白字） */}
      <div className="bg-[#000000] rounded-xl border border-[#222226] text-zinc-200 font-mono text-xs overflow-hidden shadow-2xl">
        {/* Terminal 顶栏 */}
        <div className="p-3 bg-[#0a0a0c] border-b border-[#222226] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
              <div className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            </div>
            <span className="text-[11px] text-zinc-400 ml-2">stdout / storyos_pipeline.log</span>
          </div>

          <div className="flex items-center gap-1.5">
            {['ALL', 'INFO', 'SUCCESS', 'WARN'].map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setFilterLevel(lvl)}
                className={`px-2 py-0.5 rounded text-[10px] transition-colors cursor-pointer font-bold ${
                  filterLevel === lvl
                    ? 'bg-white text-black shadow-xs'
                    : 'bg-[#141416] text-zinc-400 hover:text-white border border-[#27272a]'
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
            <div className="py-8 text-center text-zinc-600 text-xs">暂无审计日志</div>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-3 py-1.5 border-b border-[#18181b] text-xs">
                <span className="text-zinc-500 text-[11px] shrink-0">{log.time}</span>
                <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold shrink-0 ${
                  log.level === 'SUCCESS'
                    ? 'bg-white text-black'
                    : log.level === 'WARN'
                    ? 'bg-black text-white border border-white'
                    : 'bg-[#18181b] text-zinc-300 border border-[#2e2e33]'
                }`}>
                  {log.level}
                </span>
                <span className="text-white shrink-0 font-semibold">[{log.module}]</span>
                <span className="text-zinc-300 leading-relaxed select-text">{log.message}</span>
              </div>
            ))
          )}

          <div className="pt-3 text-zinc-500 text-[11px] flex items-center gap-2 animate-pulse">
            <span>&gt; StoryOS 引擎待命中: gpt-image-2 (high), 4:5 1080×1350, 5-frame batch, concurrency 3...</span>
          </div>
        </div>
      </div>
    </div>
  );
};
