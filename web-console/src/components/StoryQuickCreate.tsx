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
      <div className="bg-gradient-to-r from-zinc-900 via-neutral-900 to-zinc-950 rounded-xl p-5 border border-zinc-800 text-white shadow-md relative overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 right-0 w-96 h-full bg-amber-500/5 blur-3xl pointer-events-none" />

        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/30">
                <Sparkles className="w-4 h-4" />
              </span>
              <div>
                <h2 className="text-sm font-bold tracking-wide text-zinc-100 flex items-center gap-2">
                  <span>一句话创建新故事</span>
                  <span className="text-[10px] font-mono font-normal px-2 py-0.5 rounded bg-zinc-800 text-amber-300 border border-zinc-700">
                    Story-to-Pipeline 自动引擎
                  </span>
                </h2>
                <p className="text-xs text-zinc-400">输入一行高概念梗概，Story OS 自动推演世界观、32分镜节拍、人物合同与4张视觉锚点</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5 text-[11px] font-mono text-zinc-400">
              <Cpu className="w-3.5 h-3.5 text-amber-400" />
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
                className="w-full h-12 pl-4 pr-10 rounded-lg bg-zinc-950/90 border border-zinc-700 focus:border-amber-400/80 focus:ring-1 focus:ring-amber-400/40 text-sm text-zinc-100 placeholder:text-zinc-500 outline-none transition-all font-sans"
              />
              {prompt && (
                <button
                  onClick={() => setPrompt('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-xs"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            <button
              id="auto-generate-plan-btn"
              onClick={handleStartGeneration}
              disabled={isGenerating || !prompt.trim()}
              className="h-12 px-6 rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-zinc-950 font-bold text-xs tracking-wide flex items-center justify-center gap-2 shadow-lg shadow-amber-500/20 transition-all shrink-0 cursor-pointer disabled:opacity-50"
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
          <div className="flex flex-wrap items-center gap-2 mt-3 pt-2.5 border-t border-zinc-800/80">
            <span className="text-[11px] text-zinc-400 flex items-center gap-1 font-mono">
              <Lightbulb className="w-3 h-3 text-amber-400" />
              <span>经典高概念示例：</span>
            </span>
            {INSPIRATION_PROMPTS.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => setPrompt(sample)}
                className="text-[11px] px-2.5 py-1 rounded bg-zinc-800/90 hover:bg-zinc-700/80 text-zinc-300 hover:text-white border border-zinc-700/60 transition-colors text-left truncate max-w-xs md:max-w-md"
              >
                {sample}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Plan Generation Breakdown Modal */}
      {showPlanModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl max-w-2xl w-full text-zinc-100 shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-950">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
                  <Film className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">Story OS 智能工业化故事解析</h3>
                  <p className="text-[11px] font-mono text-zinc-400">Agent Multi-Stage Orchestration Pipeline</p>
                </div>
              </div>
              <button
                onClick={() => setShowPlanModal(false)}
                className="text-zinc-400 hover:text-white p-1 rounded-md hover:bg-zinc-800"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body: Progressive Steps */}
            <div className="p-6 space-y-4">
              <div className="p-3 bg-zinc-950 rounded-lg border border-zinc-800 text-xs text-zinc-300">
                <span className="text-amber-400 font-mono font-semibold">Prompt: </span>
                <span>“{prompt}”</span>
              </div>

              {/* Steps Progress */}
              <div className="space-y-3 font-mono text-xs">
                {/* Step 1 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 1 ? 'bg-zinc-800/80 border-amber-500/40' : 'bg-zinc-900/40 border-zinc-800 opacity-40'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 1 ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : generationStep === 1 ? (
                      <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-zinc-600" />
                    )}
                  </div>
                  <div>
                    <div className="font-bold text-zinc-200">阶段一：创意锁定与世界观锚定 (Narrative Core)</div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">
                      锁定核心戏剧假定（“预言照机制”），设定 32 镜头总画幅，中式悬疑冷色调基准
                    </div>
                  </div>
                </div>

                {/* Step 2 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 2 ? 'bg-zinc-800/80 border-amber-500/40' : 'bg-zinc-900/40 border-zinc-800 opacity-40'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 2 ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : generationStep === 2 ? (
                      <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-zinc-600" />
                    )}
                  </div>
                  <div>
                    <div className="font-bold text-zinc-200">阶段二：分镜节拍器编排 (Director Beat Sheet)</div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">
                      拆解四幕起承转合：日常建立 (01-04) → 异常初显 (05-12) → 危机爆发 (13-22) → 反转终局 (23-32)
                    </div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 3 ? 'bg-zinc-800/80 border-amber-500/40' : 'bg-zinc-900/40 border-zinc-800 opacity-40'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 3 ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : generationStep === 3 ? (
                      <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-zinc-600" />
                    )}
                  </div>
                  <div>
                    <div className="font-bold text-zinc-200">阶段三：人物合同与一致性锚点 (Character Consistency Contracts)</div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">
                      提取林澈 (EMB-8821B)、沈轻语 (EMB-9043C)、周放 (EMB-7732A) 脸模特征与负向穿戴规则
                    </div>
                  </div>
                </div>

                {/* Step 4 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 4 ? 'bg-zinc-800/80 border-amber-500/40' : 'bg-zinc-900/40 border-zinc-800 opacity-40'
                }`}>
                  <div className="mt-0.5">
                    {generationStep > 4 ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : generationStep === 4 ? (
                      <RefreshCw className="w-4 h-4 text-amber-400 animate-spin" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-zinc-600" />
                    )}
                  </div>
                  <div>
                    <div className="font-bold text-zinc-200">阶段四：4 张 Visual Lock 视觉基准锁死 (Keyframe Anchors)</div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">
                      完成主角面容基准、温泉旅馆废墟大堂、拍立得底片特写、雨夜长廊 4 张母版（4:5 标准竖版画幅）
                    </div>
                  </div>
                </div>

                {/* Step 5 */}
                <div className={`p-3 rounded-lg border flex items-start gap-3 transition-all ${
                  generationStep >= 5 ? 'bg-zinc-800/80 border-emerald-500/40' : 'bg-zinc-900/40 border-zinc-800 opacity-40'
                }`}>
                  <div className="mt-0.5">
                    {generationStep === 5 ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-zinc-600" />
                    )}
                  </div>
                  <div>
                    <div className="font-bold text-emerald-300">阶段五：方案装配就绪，批次渲染就绪</div>
                    <div className="text-[11px] text-zinc-400 mt-0.5">
                      StoryOS 图片执行引擎已就绪，准备下发首批 5 帧逻辑批次出图队列（最大同时出图 3 张）
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-zinc-950 border-t border-zinc-800 flex items-center justify-between">
              <span className="text-[11px] text-zinc-500 font-mono">
                {generationStep === 5 ? '✓ 生产方案全流程锁定完毕' : '智能体协同分析推演中...'}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowPlanModal(false)}
                  className="px-3.5 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-300"
                >
                  关闭
                </button>
                <button
                  onClick={handleApplyToWorkbench}
                  disabled={generationStep < 5}
                  className="px-4 py-1.5 rounded bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs flex items-center gap-1.5 disabled:opacity-40"
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
