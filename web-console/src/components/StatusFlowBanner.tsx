import React from 'react';
import { ArrowRight, Check } from 'lucide-react';
import { ProductionStage } from '../types';

interface StatusFlowBannerProps {
  currentStage: ProductionStage;
  onStageChange?: (stage: ProductionStage) => void;
  completedFrames?: number;
  totalFrames?: number;
  onOpenPipelineView?: () => void;
}
const STAGES: Array<{key:ProductionStage;label:string}> = [
  {key:'IDEA_LOCK',label:'创意'}, {key:'STORYBOARD_LOCK',label:'分镜'},
  {key:'VISUAL_CALIBRATE',label:'视觉'}, {key:'PROD_APPROVED',label:'生产审核'},
  {key:'READY_TO_PUBLISH',label:'待发布'}, {key:'PUBLISHED',label:'已发布'},
  {key:'POST_MORTEM',label:'复盘'}
];
export const StatusFlowBanner: React.FC<StatusFlowBannerProps> = ({currentStage,completedFrames,totalFrames,onOpenPipelineView}) => {
  const index = STAGES.findIndex(step => step.key === currentStage);
  return <section className="border-b border-[var(--border-subtle)] pb-4 text-[var(--text-primary)]">
    <div className="mb-3 flex items-center justify-between gap-3">
      <div><h2 className="text-[14px] font-semibold">生产阶段</h2><p className="mt-1 text-[11px] text-[var(--text-tertiary)]">工作区阶段投影 · 正式阶段请以 Runtime API 为准；本页不可推进门禁</p></div>
      <button type="button" onClick={onOpenPipelineView} className="flex items-center gap-1 text-[12px] text-[var(--text-secondary)] hover:text-[var(--text-primary)]">查看完整流程 <ArrowRight size={14}/></button>
    </div>
    <ol className="flex items-start gap-1 overflow-x-auto py-1">
      {STAGES.map((step,i)=><li key={step.key} className="min-w-[77px] flex-1 flex flex-col gap-2">
        <div className={`h-1.5 rounded-[3px] ${i===index?'bg-[#58A6FF]':i<index?'bg-[var(--success)]':'bg-[var(--border-normal)]'}`}/>
        <div className={`flex items-center gap-1.5 whitespace-nowrap text-[11px] ${i===index?'text-[var(--text-primary)] font-semibold':'text-[var(--text-tertiary)]'}`}>{i<index && <Check size={12} className="text-[var(--success)]"/>}{step.label}</div>
      </li>)}
    </ol>
    <p className="mt-3 text-[12px] text-[var(--text-secondary)]">{index>=0 ? `当前阶段：${STAGES[index].label}` : '当前阶段未识别'}{typeof completedFrames==='number' && typeof totalFrames==='number' ? ` · ${completedFrames}/${totalFrames} 帧（工作区快照）` : ''}</p>
  </section>;
};
