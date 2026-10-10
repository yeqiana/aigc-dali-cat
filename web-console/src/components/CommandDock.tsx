import React, { useState } from 'react';
import { ClipboardCopy, Check, ShieldCheck } from 'lucide-react';

interface CommandDockProps { onSendMessage: (text: string) => void; isLoading?: boolean; }
export const CommandDock: React.FC<CommandDockProps> = () => {
  const [draft,setDraft] = useState('');
  const [copied,setCopied] = useState(false);
  const handleCopy = async () => {
    if(!draft.trim())return;
    try {await navigator.clipboard.writeText(draft.trim());setCopied(true);}
    catch {setCopied(false);}
  };
  return <div className="sticky bottom-0 z-20 w-full border-t border-[var(--border-subtle)] bg-[var(--bg-app)]/95 px-4 py-3">
    <div className="mx-auto max-w-3xl">
      <label htmlFor="storyos-command-draft" className="block mb-2 text-[12px] font-medium text-[var(--text-secondary)]">生产指令草稿</label>
      <div className="border border-[var(--border-normal)] rounded-[6px] bg-[var(--bg-surface)] px-3 pt-2 pb-2 focus-within:border-[#58A6FF]">
        <textarea id="storyos-command-draft" rows={2} value={draft} onChange={e=>{setDraft(e.target.value);setCopied(false);}}
          placeholder="记录制作意图、分镜修改建议或待执行任务…" className="w-full bg-transparent resize-none text-[13px] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none"/>
        <div className="border-t border-[var(--border-subtle)] pt-2 flex items-center justify-between gap-3">
          <span className="flex items-center gap-1.5 text-[11px] text-[var(--text-tertiary)]"><ShieldCheck size={13}/>未连接生产写入接口 · 草稿只保留在当前页面</span>
          <button type="button" disabled={!draft.trim()} onClick={handleCopy} className="flex h-8 items-center gap-1.5 rounded-[5px] bg-[var(--text-primary)] px-3 text-[12px] font-semibold text-[var(--bg-app)] disabled:opacity-40 disabled:cursor-not-allowed">
            {copied?<Check size={14}/>:<ClipboardCopy size={14}/>} {copied?'已复制':'复制草稿'}
          </button>
        </div>
      </div>
    </div>
  </div>;
};
