import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Wand2,
  Lightbulb,
  CheckCircle2,
  Layers,
  Sliders,
  Film,
  UserCheck,
  Cpu,
  X,
  RefreshCw
} from 'lucide-react';
import { INSPIRATION_PROMPTS } from '../mockData';
import { Episode } from '../types';

interface StoryQuickCreateProps {
  onStoryGenerated: (newStoryPrompt: string) => void;
  activeEpisode: Episode;
}

export const StoryQuickCreate: React.FC<StoryQuickCreateProps> = ({
  onStoryGenerated,
  activeEpisode,
}) => {
  const [prompt, setPrompt] = useState(
    '几个大学生夜里误入废弃温泉镇，手机相册里开始出现明天的照片'
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStep, setGenerationStep] = useState(0);
  const [showPlanModal, setShowPlanModal] = useState(false);

  const handleStartGeneration = () => {
    if (!prompt.trim()) return;
    setIsGenerating(true);
    setShowPlanModal(true);
    setGenerationStep(1);

    // Progressive generation steps simulation
    setTimeout(() => setGenerationStep(2), 700);
    setTimeout(() => setGenerationStep(3), 1500);
    setTimeout(() => setGenerationStep(4), 2200);
    setTimeout(() => {
      setGenerationStep(5);
      setIsGenerating(false);
    }, 2800);
  };

  const handleApplyToWorkbench = () => {
    setShowPlanModal(false);
    onStoryGenerated(prompt);
  };

  return (
    <div id="story-quick-create-section" className="mb-6">
      <div className="storyos-surface p-5 relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
                <Sparkles className="w-4 h-4" />
              </span>
              <div>
                <h2 className="text-sm font-semibold tracking-wide text-[var(--text-primary)] flex items-center gap-2">
                  <span>一句话创建新故事</span>
                  <span className="storyos-status storyos-status--info font-mono">
                    Story-to-Pipeline 自动引擎
                  </span>
                </h2>
                <p className="text-xs text-[var(--text-tertiary)]">输入一行高概念梗概，Story OS 自动推演世界观、32分镜节拍、人物合同与4张视觉锚点</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5 text-[11px] font-mono text-[var(--text-tertiary)]">
              <Cpu className="w-3.5 h-3.5 text-[var(--primary)]" />
              <span>gpt-image-2 (high) • 4:5 (1080×1350)</span>
            </div>
          </div>

          {/* Main Input Box & Action Button */}
          <div className="flex flex-col md:flex-row gap-2.5">
            <div className="relative flex-1">
              <input
                id="quick-story-input"
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="例如：几个大学生夜里误入废弃温泉镇，手机相册里开始出现明天的照片..."
                className="storyos-control w-full h-12 pl-4 pr-10 text-sm placeholder:text-[var(--text-subtle)] outline-none focus:border-[var(--focus)] focus:ring-3 focus:ring-[rgba(22,119,255,.10)] font-sans"
              />
              {prompt && (
                <button
                  onClick={() => setPrompt('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-subtle)] hover:text-[var(--text-primary)] text-xs"
                  aria-label="清空故事梗概"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <button
              id="auto-generate-plan-btn"
              onClick={handleStartGeneration}
              disabled={isGenerating || !prompt.trim()}
              className="h-12 px-6 rounded-[var(--radius-md)] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white font-semibold text-xs tracking-wide flex items-center justify-center gap-2 shadow-[var(--shadow-xs)] transition-colors shrink-0 cursor-pointer disabled:opacity-50"
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>正在深度解析工业管线...</span>
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4" />
                  <span>自动生成故事方案</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>

          {/* Quick inspiration chips */}
          <div className="flex flex-wrap items-center gap-2 mt-3 pt-2.5 border-t border-[var(--border-subtle)]">
            <span className="text-[11px] text-[var(--text-tertiary)] flex items-center gap-1 font-mono">
              <Lightbulb className="w-3 h-3 text-[var(--warning)]" />
              <span>经典高概念示例：</span>
            </span>
            {INSPIRATION_PROMPTS.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => setPrompt(sample)}
                className="text-[11px] px-2.5 py-1 rounded-[var(--radius-sm)] bg-[var(--bg-subtle)] hover:bg-[var(--bg-muted)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-normal)] transition-colors text-left truncate max-w-xs md:max-w-md"
              >
                {sample}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Plan Generation Breakdown Modal */}
      {showPlanModal && (
        <div className="storyos-overlay fixed inset-0 z-50 flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="storyos-elevated rounded-[var(--radius-lg)] max-w-2xl w-full text-[var(--text-primary)] overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-surface)]">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] border border-[var(--border-normal)] flex items-center justify-center text-[var(--primary)]">
                  <Film className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[var(--text-primary)]">Story OS 智能工业化故事解析</h3>
                  <p className="text-[11px] font-mono text-[var(--text-tertiary)]">Agent Multi-Stage Orchestration Pipeline</p>
                </div>
              </div>
              <button
                onClick={() => setShowPlanModal(false)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] p-1 rounded-[var(--radius-sm)] hover:bg-[var(--bg-subtle)]"
                aria-label="关闭故事解析面板"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body: Progressive Steps */}
            <div className="p-6 space-y-4">
              <div className="p-3 bg-[var(--bg-subtle)] rounded-[var(--radius-md)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)]">
                <span className="text-[var(--primary)] font-mono font-semibold">Prompt: </span>
                <span>“{prompt}”</span>
              </div>

              {/* Steps Progress */}
              <div className="space-y-3 font-mono text-xs">
                {/* Step 1 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 1 ? 'bg-[var(--primary-soft)] border-[var(--border-normal)]' : 'bg-[var(--bg-subtle)] border-[var(--border-subtle)] opacity-50'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 1 ? (
                      <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
                    ) : generationStep === 1 ? (
                      <RefreshCw className="w-4 h-4 text-[var(--primary)] animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-[var(--border-strong)]" />
                    )}
                  </div>
                  <div>
                    <div className="font-semibold text-[var(--text-primary)]">阶段一：创意锁定与世界观锚定 (Narrative Core)</div>
                    <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                      锁定核心戏剧假定（“预言照机制”），设定 32 镜头总画幅，中式悬疑冷色调基准
                    </div>
                  </div>
                </div>

                {/* Step 2 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 2 ? 'bg-[var(--primary-soft)] border-[var(--border-normal)]' : 'bg-[var(--bg-subtle)] border-[var(--border-subtle)] opacity-50'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 2 ? (
                      <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
                    ) : generationStep === 2 ? (
                      <RefreshCw className="w-4 h-4 text-[var(--primary)] animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-[var(--border-strong)]" />
                    )}
                  </div>
                  <div>
                    <div className="font-semibold text-[var(--text-primary)]">阶段二：分镜节拍器编排 (Director Beat Sheet)</div>
                    <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                      拆解四幕起承转合：日常建立 (01-04) → 异常初显 (05-12) → 危机爆发 (13-22) → 反转终局 (23-32)
                    </div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 3 ? 'bg-[var(--primary-soft)] border-[var(--border-normal)]' : 'bg-[var(--bg-subtle)] border-[var(--border-subtle)] opacity-50'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 3 ? (
                      <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
                    ) : generationStep === 3 ? (
                      <RefreshCw className="w-4 h-4 text-[var(--primary)] animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-[var(--border-strong)]" />
                    )}
                  </div>
                  <div>
                    <div className="font-semibold text-[var(--text-primary)]">阶段三：人物合同与一致性锚点 (Character Consistency Contracts)</div>
                    <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                      提取林澈 (EMB-8821B)、沈轻语 (EMB-9043C)、周放 (EMB-7732A) 脸模特征与负向穿戴规则
                    </div>
                  </div>
                </div>

                {/* Step 4 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 4 ? 'bg-[var(--primary-soft)] border-[var(--border-normal)]' : 'bg-[var(--bg-subtle)] border-[var(--border-subtle)] opacity-50'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 4 ? (
                      <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
                    ) : generationStep === 4 ? (
                      <RefreshCw className="w-4 h-4 text-[var(--primary)] animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-[var(--border-strong)]" />
                    )}
                  </div>
                  <div>
                    <div className="font-semibold text-[var(--text-primary)]">阶段四：4 张 Visual Lock 视觉基准锁死 (Keyframe Anchors)</div>
                    <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                      完成主角面容基准、温泉旅馆废墟大堂、拍立得底片特写、雨夜长廊 4 张母版（4:5 标准竖版画幅）
                    </div>
                  </div>
                </div>

                {/* Step 5 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 5 ? 'bg-[var(--success-soft)] border-[var(--border-normal)]' : 'bg-[var(--bg-subtle)] border-[var(--border-subtle)] opacity-50'
                }`}>
                  <div className="mt-0.5">
                    {generationStep === 5 ? (
                      <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-[var(--border-strong)]" />
                    )}
                  </div>
                  <div>
                    <div className="font-semibold text-[var(--success)]">阶段五：方案装配就绪，批次渲染就绪</div>
                    <div className="text-[11px] text-[var(--text-tertiary)] mt-0.5">
                      StoryOS 图片执行引擎已就绪，准备下发首批 5 帧逻辑批次出图队列（最大同时出图 3 张）
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-[var(--bg-subtle)] border-t border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[11px] text-[var(--text-tertiary)] font-mono">
                {generationStep === 5 ? '✓ 生产方案全流程锁定完毕' : '智能体协同分析推演中...'}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowPlanModal(false)}
                  className="h-9 px-3.5 rounded-[var(--radius-md)] bg-[var(--bg-surface)] hover:bg-[var(--bg-muted)] border border-[var(--border-normal)] text-xs text-[var(--text-secondary)]"
                >
                  关闭
                </button>
                <button
                  onClick={handleApplyToWorkbench}
                  disabled={generationStep < 5}
                  className="h-9 px-4 rounded-[var(--radius-md)] bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white font-semibold text-xs flex items-center gap-1.5 disabled:opacity-40"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>装载并激活至工作台</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
