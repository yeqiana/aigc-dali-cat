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
      <div className="w-full max-w-[760px] pointer-events-auto relative">
        {/* 预设指令快捷抽屉（点击 + 号展开） */}
        {showPresets && (
          <div className="storyos-elevated mb-2 p-2 text-xs space-y-1">
            <div className="px-2 py-1 text-[11px] font-mono text-[var(--text-tertiary)] border-b border-[var(--border-subtle)] flex items-center justify-between">
              <span>快捷故事生产指令模版</span>
              <button
                type="button"
                onClick={() => setShowPresets(false)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer"
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
                className="w-full text-left px-2.5 py-1.5 rounded-[var(--radius-sm)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
              >
                • {preset}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="bg-[var(--bg-elevated)] border border-[var(--border-normal)] rounded-[var(--radius-lg)] shadow-[var(--shadow-floating)] p-2.5 flex flex-col focus-within:border-[var(--focus)] transition-colors"
        >
          {/* 输入区 */}
          <div className="px-1.5 pt-0.5 pb-1">
            <textarea
              id="storyos-prompt-input"
              rows={2}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入剧本故事台词、分镜景别微调，或调度批次出图指令..."
              className="w-full bg-transparent text-[13px] text-[var(--text-primary)] placeholder:text-[var(--text-disabled)] focus:outline-none resize-none font-sans leading-relaxed"
            />
          </div>

          {/* 底部控制栏 */}
          <div className="flex items-center justify-between text-xs pt-1.5 border-t border-[var(--border-subtle)]">
            {/* 左侧：+号 与 门禁模式切换 */}
            <div className="flex items-center gap-2 text-[var(--text-tertiary)]">
              <button
                type="button"
                onClick={() => setShowPresets(!showPresets)}
                className={`p-1 rounded transition-colors cursor-pointer ${
                  showPresets
                    ? 'bg-[var(--primary-soft)] text-[var(--primary)]'
                    : 'hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)]'
                }`}
                title="选择生产预设或参考"
              >
                <Plus className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={toggleGate}
                className="flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] border border-[var(--border-normal)] rounded-[var(--radius-sm)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
                title="点击切换门禁模式"
              >
                {strictGate ? (
                  <>
                    <ShieldCheck className="w-3 h-3 text-[var(--primary)]" />
                    <span>StoryOS 严格门禁</span>
                  </>
                ) : (
                  <>
                    <ShieldAlert className="w-3 h-3 text-[var(--text-tertiary)]" />
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
                  className="flex items-center gap-1 text-[11px] font-mono text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--bg-surface)] border border-[var(--border-normal)] px-2 py-0.5 rounded-[var(--radius-sm)] transition-colors cursor-pointer"
                >
                  <span>{selectedModel} · {selectedAspect}</span>
                  <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)]" />
                </button>

                {modelDropdownOpen && (
                  <div className="storyos-elevated absolute right-0 bottom-full mb-1.5 w-56 p-1 z-50 text-xs font-mono">
                    <div className="px-2 py-1 text-[10px] text-[var(--text-tertiary)] uppercase border-b border-[var(--border-subtle)]">
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
                            ? 'bg-[var(--primary-soft)] text-[var(--primary-hover)] font-semibold'
                            : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-subtle)]'
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
                className="p-1 text-[var(--text-tertiary)] hover:text-[var(--primary)] transition-colors cursor-pointer"
                title="快速录入指令"
              >
                <Sparkles className="w-3.5 h-3.5" />
              </button>

              <button
                type="submit"
                disabled={!inputText.trim() || isLoading}
                className={`w-7 h-7 rounded-[var(--radius-sm)] flex items-center justify-center transition-colors ${
                  inputText.trim() && !isLoading
                    ? 'bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] cursor-pointer'
                    : 'bg-[var(--bg-muted)] text-[var(--text-disabled)] cursor-not-allowed'
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
