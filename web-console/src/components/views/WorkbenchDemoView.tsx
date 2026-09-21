import React, { useState } from 'react';
import { PanelRight, ShieldAlert } from 'lucide-react';
import { ActivityStream } from '../ActivityStream';
import { CommandDock } from '../CommandDock';
import { ContextPanel } from '../ContextPanel';
import { ProductionStagePanel } from '../ProductionStagePanel';
import { StatusFlowBanner } from '../StatusFlowBanner';
import { DEMO_EPISODES } from '../../workbenchDemoData';
import type { BatchItem, Episode } from '../../types';

interface WorkbenchDemoViewProps {
  onShowToast: (message: string) => void;
}

export const WorkbenchDemoView: React.FC<WorkbenchDemoViewProps> = ({ onShowToast }) => {
  const [episodes, setEpisodes] = useState<Episode[]>(DEMO_EPISODES);
  const [activeEpisode, setActiveEpisode] = useState<Episode>(DEMO_EPISODES[0]);
  const [isGeneratingBatch, setIsGeneratingBatch] = useState(false);
  const [contextPanelOpen, setContextPanelOpen] = useState(false);

  const handleQuickGenerateNextBatch = () => {
    setIsGeneratingBatch(true);
    window.setTimeout(() => {
      setIsGeneratingBatch(false);
      const nextCompleted = Math.min(activeEpisode.totalFrames, activeEpisode.completedFrames + 5);
      const newItems: BatchItem[] = [21, 22, 23, 24, 25].map((idx) => ({
        id: `b5-f${idx}`,
        frameIndex: idx,
        prompt: `4:5 电影级镜头，主角林澈推开古宅偏殿木门，冷光穿透雨幕 (Frame #${idx})`,
        imageUrl: 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=700&auto=format&fit=crop&q=80',
        status: 'qa_passed',
        qaScore: 0.98,
        progress: 100,
        consistencyScore: 0.98,
        renderTime: '11.8s',
        seed: 4892010 + idx,
      }));
      const updated: Episode = {
        ...activeEpisode,
        completedFrames: nextCompleted,
        currentStage: nextCompleted >= activeEpisode.totalFrames ? 'PUBLISH_READY' : 'PRODUCTION_PASSED',
        currentBatch: {
          batchId: 'BATCH_05',
          batchName: '第 5 批次 (Frame #21 - #25)',
          status: 'completed',
          items: newItems,
        },
        updatedAt: '刚刚',
      };
      setActiveEpisode(updated);
      setEpisodes((prev) => prev.map((episode) => episode.id === updated.id ? updated : episode));
      onShowToast(`Local Demo 已更新到 ${nextCompleted}/${activeEpisode.totalFrames} 帧 · 未写入生产 Authority`);
    }, 1200);
  };

  const handleCommandSubmit = (commandText: string) => {
    onShowToast(`Local Demo 指令已应用：“${commandText.slice(0, 16)}...” · 未写入 Runtime/Authority`);
    if (commandText.length <= 5) return;
    const newEpisode: Episode = {
      ...activeEpisode,
      id: `demo-${Date.now()}`,
      code: `DEMO-${episodes.length + 1}`,
      title: commandText.length > 14 ? `${commandText.slice(0, 14)}...` : commandText,
      synopsis: commandText,
      completedFrames: 0,
      totalFrames: 32,
      currentStage: 'IDEA_LOCKED',
      updatedAt: '刚刚',
    };
    setEpisodes((prev) => [newEpisode, ...prev]);
    setActiveEpisode(newEpisode);
  };

  const handleReviewAction = (frameId: string, action: 'pass' | 'inpaint' | 'reject') => {
    onShowToast(`Frame #${frameId} Local Demo action=${action.toUpperCase()} · 未写入 Review Authority`);
  };

  return (
    <div className="relative flex min-h-full gap-4 pb-24">
      <div className="min-w-0 flex-1 space-y-3">
        <section className="storyos-surface min-h-10 px-3 py-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <ShieldAlert className="h-4 w-4 shrink-0 text-[var(--warning)]" />
            <div className="min-w-0">
              <div className="text-xs font-semibold text-[var(--text-primary)]">Workbench Local Demo</div>
              <div className="text-[10px] font-mono text-[var(--text-tertiary)]">FRONTEND_DEMO_NON_AUTHORITY · 不写 MySQL / Redis / Runtime</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={activeEpisode.id}
              onChange={(event) => {
                const selected = episodes.find((episode) => episode.id === event.target.value);
                if (selected) setActiveEpisode(selected);
              }}
              className="storyos-control h-8 max-w-[280px] px-2 text-xs font-mono"
              aria-label="选择本地 Demo Episode"
            >
              {episodes.map((episode) => (
                <option key={episode.id} value={episode.id}>{episode.code} · {episode.title}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => setContextPanelOpen((open) => !open)}
              className={`storyos-control h-8 px-2.5 inline-flex items-center gap-1.5 text-[11px] font-mono ${contextPanelOpen ? 'text-[var(--primary-hover)]' : ''}`}
            >
              <PanelRight className="h-3.5 w-3.5" />
              CONTEXT
            </button>
          </div>
        </section>

        <div className="grid min-h-full grid-cols-1 xl:grid-cols-[minmax(360px,38%)_minmax(0,62%)] gap-4">
          <section aria-label="Demo Operator Console" className="min-w-0">
            <StatusFlowBanner
              currentStage={activeEpisode.currentStage}
              completedFrames={activeEpisode.completedFrames}
              totalFrames={activeEpisode.totalFrames}
            />
            <ActivityStream
              activeEpisode={activeEpisode}
              onGenerateBatch={handleQuickGenerateNextBatch}
              isGeneratingBatch={isGeneratingBatch}
              onReviewAction={handleReviewAction}
              onShowToast={onShowToast}
            />
          </section>
          <ProductionStagePanel
            activeEpisode={activeEpisode}
            isGeneratingBatch={isGeneratingBatch}
            onSelectFrame={(frame) => onShowToast(`Local Demo Frame #${frame.frameIndex} · ${frame.status}`)}
          />
        </div>
      </div>

      {contextPanelOpen && (
        <ContextPanel
          activeEpisode={activeEpisode}
          onShowToast={onShowToast}
        />
      )}

      <CommandDock
        onSendMessage={handleCommandSubmit}
        isLoading={isGeneratingBatch}
      />
    </div>
  );
};
