import React, { useState } from 'react';
import { Plus, ChevronDown, ArrowUp, ShieldCheck, ShieldAlert, Sparkles } from 'lucide-react';

interface CommandDockProps {
  onSendMessage: (text: string) => void;
  isLoading?: boolean;
}

export const CommandDock: React.FC<CommandDockProps> = ({
  onSendMessage,
  isLoading = false,
}) => {
  const [inputText, setInputText] = useState('');
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gpt-image-2 (high)');
  const [selectedAspect, setSelectedAspect] = useState('4:5');
  const [strictGate, setStrictGate] = useState(true);
  const [showPresets, setShowPresets] = useState(false);

  const presets = [
    '生成接下来 5 帧雨夜长廊探索镜头，保持主角林澈 4:5 肖像基准与冷调光影',
    '调度局部重绘，修复 Frame #18 窗玻璃重影瑕疵并同步入库',
    '锁定当前分镜景别轴线，推进至第 5 逻辑批次 (Frame #21 - #25)',
    '执行 4:5 1080×1350 全量合规预检，准备发布归档',
  ];

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isLoading) return;
    onSendMessage(inputText.trim());
    setInputText('');
    setShowPresets(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const toggleGate = () => {
    setStrictGate(prev => !prev);
  };

  return (
    <div className="absolute bottom-4 left-0 right-0 z-30 flex justify-center px-6 pointer-events-none">
      <div className="w-full max-w-2xl pointer-events-auto relative">
        {/* 预设指令快捷抽屉（点击 + 号展开） */}
        {showPresets && (
          <div className="mb-2 bg-[#0c0c0e] border border-[#27272a] rounded-xl p-2 shadow-2xl text-xs space-y-1">
            <div className="px-2 py-1 text-[11px] font-mono text-zinc-400 border-b border-[#1f1f23] flex items-center justify-between">
              <span>快捷故事生产指令模版</span>
              <button
                type="button"
                onClick={() => setShowPresets(false)}
                className="hover:text-white cursor-pointer"
              >
                ✕
              </button>
            </div>
            {presets.map((preset, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setInputText(preset);
                  setShowPresets(false);
                }}
                className="w-full text-left px-2.5 py-1.5 rounded-lg text-zinc-300 hover:text-white hover:bg-[#18181b] transition-colors cursor-pointer"
              >
                • {preset}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="bg-[#0a0a0c] border border-[#27272a] rounded-xl shadow-2xl p-2.5 flex flex-col focus-within:border-white transition-colors"
        >
          {/* 输入框 - 纯黑底白字 */}
          <div className="px-1.5 pt-0.5 pb-1">
            <textarea
              id="storyos-prompt-input"
              rows={2}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入剧本故事台词、分镜景别微调，或调度批次出图指令..."
              className="w-full bg-transparent text-[13px] text-white placeholder-zinc-500 focus:outline-hidden resize-none font-sans leading-relaxed"
            />
          </div>

          {/* 底部控制栏（纯黑底白字高对比） */}
          <div className="flex items-center justify-between text-xs pt-1.5 border-t border-[#1f1f23]">
            {/* 左侧：+号 与 门禁模式切换 */}
            <div className="flex items-center gap-2 text-zinc-400">
              <button
                type="button"
                onClick={() => setShowPresets(!showPresets)}
                className={`p-1 rounded transition-colors cursor-pointer ${
                  showPresets ? 'bg-white text-black' : 'hover:text-white hover:bg-[#18181b]'
                }`}
                title="选择生产预设或参考"
              >
                <Plus className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={toggleGate}
                className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 bg-[#141416] hover:bg-[#1f1f23] border border-[#27272a] rounded text-zinc-300 hover:text-white transition-colors cursor-pointer"
                title="点击切换门禁模式"
              >
                {strictGate ? (
                  <>
                    <ShieldCheck className="w-3 h-3 text-white" />
                    <span>StoryOS 严格门禁</span>
                  </>
                ) : (
                  <>
                    <ShieldAlert className="w-3 h-3 text-zinc-400" />
                    <span>宽松调试模式</span>
                  </>
                )}
              </button>
            </div>

            {/* 右侧：模型规格、快捷填入与发送 */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                  className="flex items-center gap-1 text-[11px] font-mono text-zinc-300 hover:text-white bg-[#141416] border border-[#27272a] px-2 py-0.5 rounded transition-colors cursor-pointer"
                >
                  <span>{selectedModel} · {selectedAspect}</span>
                  <ChevronDown className="w-3 h-3 text-zinc-400" />
                </button>

                {modelDropdownOpen && (
                  <div className="absolute right-0 bottom-full mb-1.5 w-56 bg-[#0c0c0e] border border-[#27272a] rounded-lg shadow-2xl p-1 z-50 text-xs font-mono">
                    <div className="px-2 py-1 text-[10px] text-zinc-400 uppercase border-b border-[#1f1f23]">
                      选择生图引擎与画幅
                    </div>
                    {[
                      { model: 'gpt-image-2 (high)', aspect: '4:5' },
                      { model: 'gpt-image-2 (std)', aspect: '4:5' },
                      { model: 'flux-pro (cinematic)', aspect: '4:5' },
                      { model: 'storyos-custom', aspect: '4:5' },
                    ].map((item, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setSelectedModel(item.model);
                          setSelectedAspect(item.aspect);
                          setModelDropdownOpen(false);
                        }}
                        className={`w-full text-left px-2 py-1.5 rounded transition-colors cursor-pointer ${
                          selectedModel === item.model
                            ? 'bg-white text-black font-semibold'
                            : 'text-zinc-300 hover:text-white hover:bg-[#18181b]'
                        }`}
                      >
                        {item.model} · {item.aspect}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={() => {
                  setInputText('快速批量生成第 5 批次分镜，保持林澈面容一致性');
                }}
                className="p-1 text-zinc-400 hover:text-white transition-colors cursor-pointer"
                title="快速录入指令"
              >
                <Sparkles className="w-3.5 h-3.5" />
              </button>

              <button
                type="submit"
                disabled={!inputText.trim() || isLoading}
                className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${
                  inputText.trim() && !isLoading
                    ? 'bg-white text-black hover:bg-zinc-200 cursor-pointer shadow-xs'
                    : 'bg-[#18181b] text-zinc-600 cursor-not-allowed'
                }`}
                title="发送生产指令 (Enter)"
              >
                <ArrowUp className="w-3.5 h-3.5 stroke-[2.5]" />
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
