import React, { useState } from 'react';
import {
  Terminal,
  Copy,
  Check,
  Play,
  ChevronRight,
  Wand2
} from 'lucide-react';
import { Episode, BatchItem } from '../types';

interface ActivityStreamProps {
  activeEpisode: Episode;
  onGenerateBatch: () => void;
  isGeneratingBatch: boolean;
  onReviewAction: (frameId: string, action: 'pass' | 'inpaint' | 'reject') => void;
  onShowToast: (msg: string) => void;
}

export const ActivityStream: React.FC<ActivityStreamProps> = ({
  activeEpisode,
  onGenerateBatch,
  isGeneratingBatch,
  onReviewAction,
  onShowToast,
}) => {
  const [timeStepOpen, setTimeStepOpen] = useState(false);
  const [copiedCmd, setCopiedCmd] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  const [inpaintDone, setInpaintDone] = useState(false);
  const [selectedFrame, setSelectedFrame] = useState<BatchItem | null>(null);
  const [passOverrides, setPassOverrides] = useState<Record<string, boolean>>({});

  const commandText = `storyos run --model gpt-image-2 --quality high --aspect 4:5 --batch 5 --concurrency 3`;

  const handleCopy = () => {
    navigator.clipboard.writeText(commandText);
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 1500);
    onShowToast('终端指令已复制至剪贴板');
  };

  const handleRunInpaint = () => {
    setInpaintDone(true);
    onReviewAction('b4-f18', 'inpaint');
    onShowToast('Frame #18 倒影瑕疵已执行 Inpaint 修复，质检通过');
  };

  const toggleFramePass = (frame: BatchItem) => {
    const currentStatus = passOverrides[frame.id] !== undefined
      ? passOverrides[frame.id]
      : (frame.status === 'qa_passed' || (frame.frameIndex === 18 && inpaintDone));
    const nextStatus = !currentStatus;
    setPassOverrides(prev => ({ ...prev, [frame.id]: nextStatus }));
    onShowToast(`Frame #${frame.frameIndex} 状态已真实切换为: ${nextStatus ? '通过 (PASS)' : '标记待修 (WARN)'}`);
  };

  return (
    <div className="space-y-4 text-[13px] leading-relaxed select-text font-sans pb-32">
      {/* 极简时间戳 */}
      <div className="text-center my-1">
        <span className="text-[11px] font-mono text-[var(--text-tertiary)]">
          今天 14:58
        </span>
      </div>

      {/* 触发操作按钮 */}
      <div className="flex justify-end items-center gap-2">
        <button
          type="button"
          onClick={onGenerateBatch}
          disabled={isGeneratingBatch}
          className="px-3 py-1.5 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] text-xs font-semibold hover:opacity-90 transition-opacity shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          {isGeneratingBatch ? (
            <>
              <span className="w-2 h-2 rounded-full bg-current animate-ping" />
              <span>正在出图...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>调度批次 ({activeEpisode.completedFrames}/{activeEpisode.totalFrames})</span>
            </>
          )}
        </button>
      </div>

      {/* 核心对话推进卡片 */}
      <div className="bg-[var(--bg-surface)] rounded-[8px] border border-[var(--border-subtle)] p-3 text-[var(--text-secondary)] space-y-2.5 shadow-xs">
        {/* 用时折叠 */}
        <div>
          <button
            type="button"
            onClick={() => setTimeStepOpen(!timeStepOpen)}
            className="flex items-center gap-1.5 text-xs font-mono text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
          >
            <ChevronRight className={`w-3.5 h-3.5 transition-transform ${timeStepOpen ? 'rotate-90' : ''}`} />
            <span>用时 53s · 32 帧流水线</span>
          </button>

          {timeStepOpen && (
            <div className="mt-2 pl-4 py-2 border-l border-[var(--border-normal)] text-[11px] font-mono text-[var(--text-secondary)] space-y-1 bg-[var(--bg-elevated)] rounded-r-[6px]">
              <div>• 校验 gpt-image-2 与 4:5 1080×1350 分辨率</div>
              <div>• 限制并发 3，保障人脸一致性</div>
              <div>• 批次 5 帧出图完成，已提交质检</div>
            </div>
          )}
        </div>

        {/* 简洁分析陈述 */}
        <p className="text-[var(--text-primary)] text-xs sm:text-[13px]">
          已解析当前批次（Frame #16 - #20）需求，保持主角肖像与冷调环境锚点。
        </p>

        {/* 终端命令代码块 */}
        <div className="rounded-[6px] bg-[var(--bg-app)] border border-[var(--border-subtle)] overflow-hidden">
          <div className="px-3 py-1.5 bg-[var(--bg-workspace)] border-b border-[var(--border-subtle)] flex items-center justify-between text-[11px] font-mono text-[var(--text-tertiary)]">
            <span className="flex items-center gap-1.5 text-[var(--text-primary)]">
              <Terminal className="w-3.5 h-3.5" />
              <span>storyos-cli</span>
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="hover:text-[var(--text-primary)] flex items-center gap-1 text-xs cursor-pointer"
            >
              {copiedCmd ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-[var(--text-tertiary)]" />}
              <span>{copiedCmd ? '已复制' : '复制代码'}</span>
            </button>
          </div>
          <div className="p-3 font-mono text-xs text-[var(--text-primary)] overflow-x-auto select-all">
            <code>{commandText}</code>
          </div>
        </div>

        {/* 调度与质检状态条 */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-[var(--text-tertiary)] bg-[var(--bg-elevated)] px-3 py-2 rounded-[6px] border border-[var(--border-subtle)] font-mono whitespace-nowrap">
          <span>模型: <strong className="text-[var(--text-primary)]">gpt-image-2 (high)</strong></span>
          <span>·</span>
          <span>画幅: <strong className="text-[var(--text-primary)]">4:5 1080×1350</strong></span>
          <span>·</span>
          <span>并发: <strong className="text-[var(--text-primary)]">3</strong></span>
          <span>·</span>
          <span>
            质检:{' '}
            {inpaintDone ? (
              <strong className="text-emerald-400 font-medium">24/32 帧全部达标</strong>
            ) : (
              <strong className="text-amber-400 font-medium">Frame #18 待修复</strong>
            )}
          </span>
        </div>

        {/* 真实文件核准切换卡片 */}
        <div className="flex items-center justify-between p-2.5 rounded-[6px] bg-[var(--bg-app)] border border-[var(--border-subtle)] text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-[var(--text-primary)] font-medium">已更新 runtime-request.json</span>
            <span className="text-emerald-400 text-[11px] font-bold">+14 行</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const next = !reviewed;
                setReviewed(next);
                onShowToast(next ? '已真实核准 runtime-request 配置' : '已撤销配置核准状态');
              }}
              className={`px-3 py-1 rounded-[4px] text-xs font-semibold transition-all cursor-pointer ${
                reviewed
                  ? 'bg-[var(--text-primary)] text-[var(--bg-app)] shadow-xs'
                  : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-[var(--border-normal)]'
              }`}
            >
              {reviewed ? '已核准配置 ✓' : '点击核准配置'}
            </button>
          </div>
        </div>

        {/* 批次 5 帧 4:5 出图极简流 */}
        <div className="pt-3 border-t border-[var(--border-subtle)]">
          <div className="flex items-center justify-between text-xs font-mono text-[var(--text-tertiary)] mb-2">
            <span className="text-[var(--text-primary)] font-semibold">出图批次 (Batch #04)</span>
            <span className="text-[var(--text-tertiary)] font-mono text-[11px]">4:5 1080×1350</span>
          </div>

          <div className="grid grid-cols-5 gap-2.5">
            {activeEpisode.currentBatch.items.map((item) => {
              const isPassed = passOverrides[item.id] !== undefined
                ? passOverrides[item.id]
                : (item.frameIndex === 18 ? inpaintDone : item.status === 'qa_passed');

              return (
                <div
                  key={item.id}
                  className={`group relative rounded-[6px] overflow-hidden aspect-[4/5] bg-[var(--bg-app)] border transition-all cursor-pointer ${
                    isPassed ? 'border-[var(--border-subtle)] hover:border-[#58A6FF]' : 'border-amber-400 ring-1 ring-amber-400/60'
                  }`}
                  onClick={() => setSelectedFrame(item)}
                >
                  <img
                    src={item.imageUrl}
                    alt={item.prompt}
                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-black/75 font-mono text-[10px] text-white font-bold backdrop-blur-xs">
                    #{item.frameIndex}
                  </div>
                  <div className="absolute bottom-1 right-1">
                    {isPassed ? (
                      <span className="px-1.5 py-0.5 rounded bg-emerald-500 text-white font-bold text-[10px]">
                        PASS
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded bg-amber-500 text-black font-bold text-[10px]">
                        待修
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 底部单个操作按钮 */}
        <div className="flex justify-end gap-2 pt-2">
          {!inpaintDone ? (
            <button
              type="button"
              onClick={handleRunInpaint}
              className="px-3.5 py-1.5 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] text-xs font-semibold hover:opacity-90 transition-opacity flex items-center gap-1.5 cursor-pointer shadow-xs"
            >
              <Wand2 className="w-3.5 h-3.5" />
              <span>一键修复 Frame #18 倒影微瑕</span>
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-emerald-400 font-mono">已完成逐帧修复并入库</span>
              <button
                type="button"
                onClick={() => {
                  setInpaintDone(false);
                  onShowToast('已重置 Frame #18 为待修状态');
                }}
                className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] underline cursor-pointer"
              >
                重置测试
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 质检详情弹窗 */}
      {selectedFrame && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4 backdrop-blur-xs"
          onClick={() => setSelectedFrame(null)}
        >
          <div
            className="bg-[var(--bg-elevated)] border border-[var(--border-normal)] rounded-[8px] max-w-sm w-full p-4 text-[var(--text-primary)] space-y-3 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between text-xs font-mono border-b border-[var(--border-subtle)] pb-2 text-[var(--text-secondary)]">
              <span className="font-bold text-[var(--text-primary)]">Frame #{selectedFrame.frameIndex} (4:5 1080×1350)</span>
              <button
                type="button"
                onClick={() => setSelectedFrame(null)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-1.5 py-0.5 rounded-[4px] cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="aspect-[4/5] rounded-[6px] overflow-hidden border border-[var(--border-subtle)] bg-[var(--bg-app)]">
              <img
                src={selectedFrame.imageUrl}
                alt={selectedFrame.prompt}
                className="w-full h-full object-cover"
                referrerPolicy="no-referrer"
              />
            </div>

            <div className="text-xs font-mono text-[var(--text-secondary)] space-y-1.5 bg-[var(--bg-surface)] p-2.5 rounded-[6px] border border-[var(--border-subtle)]">
              <div>• 提示词: {selectedFrame.prompt}</div>
              <div>• 规格: gpt-image-2 (high) · 4:5 竖版</div>
              <div>• 渲染用时: {selectedFrame.renderTime} · 种子: {selectedFrame.seed}</div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              <button
                type="button"
                onClick={() => {
                  toggleFramePass(selectedFrame);
                  setSelectedFrame(null);
                }}
                className="flex-1 py-1.5 rounded-[4px] bg-[var(--bg-surface)] border border-[var(--border-normal)] text-[var(--text-primary)] hover:bg-[var(--bg-hover)] text-xs font-medium cursor-pointer"
              >
                切换通过/待修状态
              </button>

              {selectedFrame.frameIndex === 18 && !inpaintDone && (
                <button
                  type="button"
                  onClick={() => {
                    handleRunInpaint();
                    setSelectedFrame(null);
                  }}
                  className="flex-1 py-1.5 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] text-xs font-semibold hover:opacity-90 cursor-pointer"
                >
                  局部重绘 (Inpaint)
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
