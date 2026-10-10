import React, { useState } from 'react';
import { ClipboardCopy, Check, ChevronDown, ChevronUp, FilePenLine, ShieldCheck } from 'lucide-react';

interface CommandDockProps { onSendMessage: (text: string) => void; isLoading?: boolean; }
export const CommandDock: React.FC<CommandDockProps> = () => {
  const [draft,setDraft] = useState('');
  const [copied,setCopied] = useState(false);
  const [expanded,setExpanded]=useState(false);
  const handleCopy = async () => {
    if(!draft.trim())return;
    try {await navigator.clipboard.writeText(draft.trim());setCopied(true);}
    catch {setCopied(false);}
  };
  return <section aria-label="生产指令草稿" className="sticky bottom-0 z-20 w-full border-t border-[var(--border-subtle)] bg-[var(--bg-workspace)] px-4 py-2.5 text-[var(--text-primary)]">
    <div className="mx-auto w-full max-w-[1100px]">
      <div className="flex min-h-8 items-center justify-between gap-3">
        <button type="button" onClick={()=>setExpanded(v=>!v)} aria-expanded={expanded} aria-controls="storyos-command-panel" className="flex min-w-0 items-center gap-2 text-left text-[13px] font-semibold hover:text-[var(--info)]">
          <FilePenLine size={16} className="shrink-0 text-[var(--text-secondary)]"/>
          生产指令草稿
          {expanded?<ChevronDown size={15}/>:<ChevronUp size={15}/>}
          {draft.trim()&&<span className="text-[11px] font-normal text-[var(--text-tertiary)]">已填写 · 未发送</span>}
        </button>
        <span className="hidden text-[12px] text-[var(--text-tertiary)] sm:inline">仅本页草稿 · 不会触发任务</span>
      </div>
      {expanded&&<div id="storyos-command-panel" className="mt-2 space-y-2 border-t border-[var(--border-subtle)] pt-3">
        <textarea id="storyos-command-draft" aria-label="生产指令草稿内容" rows={3} value={draft} onChange={e=>{setDraft(e.target.value);setCopied(false);}}
          placeholder="记录制作意图、分镜修改建议或待执行任务…" className="min-h-[82px] w-full resize-y rounded-[6px] border border-[var(--border-normal)] bg-[var(--bg-surface)] px-3 py-2.5 text-[13px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-tertiary)] focus-visible:border-[var(--focus)]"/>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 text-[12px] text-[var(--text-tertiary)]"><ShieldCheck size={14}/>尚未连接生产写入接口，草稿仅在当前页面暂存</span>
          <button type="button" disabled={!draft.trim()} onClick={handleCopy} className="os-action os-action-primary disabled:cursor-not-allowed disabled:opacity-40">
            {copied?<Check size={14}/>:<ClipboardCopy size={14}/>} {copied?'已复制':'复制草稿'}
          </button>
        </div>
      </div>}
    </div>
  </section>;
};
