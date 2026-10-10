import React, { useState } from 'react';
import { ArrowRight, Clapperboard, Plus, Search } from 'lucide-react';
import { Episode } from '../../types';

interface Props { episodes: Episode[]; activeEpisode: Episode; onSelectEpisode: (episode: Episode) => void; onGoToWorkbench: () => void; onNewStoryClick: () => void; }
const STAGES: Record<string,string> = { IDEA_LOCK:'创意锁定',STORYBOARD_LOCK:'分镜锁定',VISUAL_CALIBRATE:'视觉校准',PROD_APPROVED:'生产审核',READY_TO_PUBLISH:'待发布',PUBLISHED:'已发布',POST_MORTEM:'数据复盘' };
export const SeriesLibraryView: React.FC<Props> = ({episodes,activeEpisode,onSelectEpisode,onGoToWorkbench,onNewStoryClick}) => {
  const [query,setQuery] = useState('');
  const [stage,setStage] = useState('ALL');
  const filtered = episodes.filter(ep => (stage === 'ALL' || ep.currentStage === stage) && `${ep.title} ${ep.code} ${ep.genre}`.toLowerCase().includes(query.toLowerCase()));
  return <section id="series-library-view" className="space-y-5 text-[var(--text-primary)]">
    <header className="flex items-start justify-between gap-3">
      <div><p className="mb-1 text-[12px] text-[var(--text-tertiary)]">StoryOS / Library</p><h1 className="text-[20px] font-semibold">作品与项目</h1><p className="mt-2 text-[12px] text-[var(--text-secondary)]">{episodes.length} 部作品 · 打开作品继续制作、审核或查看证据</p></div>
      <button type="button" onClick={onNewStoryClick} className="flex items-center gap-2 px-3 h-9 rounded-[5px] bg-[var(--text-primary)] text-[var(--bg-app)] text-[12px] font-semibold"><Plus size={15}/> 新建故事</button>
    </header>
    <div className="flex flex-wrap gap-2 border-b border-[var(--border-subtle)] pb-4">
      <label className="relative flex-1 min-w-[210px]"><Search size={15} className="absolute top-2.5 left-3 text-[var(--text-tertiary)]"/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="搜索故事标题、编号或类型" className="w-full h-9 pl-9 pr-3 bg-[var(--bg-surface)] border border-[var(--border-normal)] rounded-[5px] text-[12px] outline-[#58A6FF] placeholder:text-[var(--text-tertiary)]" /></label>
      <select value={stage} onChange={e=>setStage(e.target.value)} aria-label="筛选生产阶段" className="h-9 px-3 bg-[var(--bg-surface)] border border-[var(--border-normal)] rounded-[5px] text-[12px]">
        <option value="ALL">全部阶段</option>{Object.entries(STAGES).map(([v,l])=><option key={v} value={v}>{l}</option>)}
      </select>
    </div>
    <div className="border-y border-[var(--border-subtle)] divide-y divide-[var(--border-subtle)]">
      {filtered.length === 0 && <div className="p-12 text-center text-[13px] text-[var(--text-tertiary)]">没有符合条件的作品。可以修改筛选或新建故事。</div>}
      {filtered.map(ep => {
        const progress=ep.totalFrames?Math.min(100,Math.round(ep.completedFrames/ep.totalFrames*100)):0;
        return <button key={ep.id} type="button" onClick={() => {onSelectEpisode(ep);onGoToWorkbench();}} className={`group w-full flex items-center gap-4 px-3 py-3 text-left hover:bg-[var(--bg-hover)] ${activeEpisode.id===ep.id?'bg-[var(--bg-surface)]':''}`}>
          <div className="h-16 w-12 shrink-0 rounded-[4px] bg-[var(--bg-elevated)] overflow-hidden">{ep.coverImage?<img src={ep.coverImage} alt="" loading="lazy" className="h-full w-full object-cover"/>:<Clapperboard size={19} className="m-auto mt-5 text-[var(--text-tertiary)]"/>}</div>
          <div className="flex-1 min-w-0"><div className="truncate text-[13px] font-semibold">{ep.title}</div><p className="mt-1 text-[12px] text-[var(--text-secondary)] truncate">{ep.genre} · {STAGES[ep.currentStage] || ep.currentStage}</p><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">{ep.code} · 更新于 {ep.updatedAt}</p></div>
          <div className="w-28 hidden sm:block shrink-0"><p className="text-[12px] text-right tabular-nums">{ep.completedFrames}/{ep.totalFrames} 帧</p><div className="mt-2 bg-[var(--border-normal)] h-1 rounded"><div className="bg-[#58A6FF] h-full rounded" style={{width:`${progress}%`}}/></div></div>
          <ArrowRight size={16} className="shrink-0 text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)]" />
        </button>;
      })}
    </div>
    <p className="text-[11px] text-[var(--text-tertiary)]">进度来源为工作区投影；执行状态与审核结果须以权威 Runtime 和证据文件为准。</p>
  </section>;
};
