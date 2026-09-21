import React, { useState } from 'react';
import {
  Terminal,
  Copy,
  Check,
  Play,
  ChevronRight,
  Layers,
  CheckCircle2,
  AlertCircle,
  Wand2,
  Eye
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
    onShowToast('Frame #18 已更新前端示例 Inpaint 状态 · 未写入 Review Authority');
  };

  const toggleFramePass = (frame: BatchItem) => {
    const currentStatus = passOverrides[frame.id] !== undefined
      ? passOverrides[frame.id]
      : (frame.status === 'qa_passed' || (frame.frameIndex === 18 && inpaintDone));
    const nextStatus = !currentStatus;
    setPassOverrides(prev => ({ ...prev, [frame.id]: nextStatus }));
    onShowToast(`Frame #${frame.frameIndex} 前端示例状态: ${nextStatus ? 'PASS' : 'WARN'} · 未写入 Review Authority`);
  };

  return (
    <div className="space-y-4 text-[13px] leading-relaxed select-text font-sans pb-32">
      {/* 轻量时间戳 */}
      <div className="text-center my-1">
        <span className="text-[11px] font-mono text-[var(--text-tertiary)]">
          今天 14:58 · StoryOS 生产队列
        </span>
      </div>

      {/* 主要生产动作 */}
      <div className="flex justify-end items-center gap-2">
        <button
          type="button"
          onClick={onGenerateBatch}
          disabled={isGeneratingBatch}
          className="h-9 px-3.5 rounded-[var(--radius-md)] bg-[var(--primary)] text-white text-xs font-semibold hover:bg-[var(--primary-hover)] transition-colors flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          {isGeneratingBatch ? (
            <>
              <span className="w-2 h-2 rounded-full bg-white" />
              <span>正在调度批次出图...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current text-white" />
              <span>调度出图批次 ({activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧)</span>
            </>
          )}
        </button>
      </div>

      {/* Operator Console 主消息面 */}
      <div className="storyos-surface p-4 text-[var(--text-secondary)] space-y-3">
        {/* 用时折叠 */}
        <div>
          <button
            type="button"
            onClick={() => setTimeStepOpen(!timeStepOpen)}
            className="flex items-center gap-1.5 text-xs font-mono text-[var(--text-tertiary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
          >
            <ChevronRight className={`w-3.5 h-3.5 transition-transform ${timeStepOpen ? 'rotate-90' : ''}`} />
            <span>执行用时 53 秒 · 32 镜图文工业级流水线</span>
          </button>

          {timeStepOpen && (
            <div className="mt-2 pl-4 py-2 border-l border-[var(--border-strong)] text-[11px] font-mono text-[var(--text-secondary)] space-y-1 bg-[var(--bg-subtle)] rounded-r-[var(--radius-md)]">
              <div>• 校验 gpt-image-2 (high) 模型参数规格与 4:5 1080×1350 竖版分辨率</div>
              <div>• 严格限制最大并发 3 张，杜绝显存溢出与跨批次人脸漂移</div>
              <div>• 批次 5 帧出图完成，已提交至 StoryOS 逐帧质检队列</div>
            </div>
          )}
        </div>

        {/* 简洁分析陈述 */}
        <p className="text-[var(--text-primary)] text-xs sm:text-[13px]">
          已解析当前批次（Frame #16 - #20）剧情推进需求，保持主角林澈 4:5 肖像基准与山庄雨夜冷调环境锚点。
        </p>

        {/* 终端命令代码块（纯黑高对比） */}
        <div className="rounded-[var(--radius-md)] bg-[var(--bg-app)] border border-[var(--border-normal)] overflow-hidden">
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
              {copiedCmd ? <Check className="w-3 h-3 text-[var(--text-primary)]" /> : <Copy className="w-3 h-3 text-[var(--text-tertiary)]" />}
              <span>{copiedCmd ? '已复制' : '复制代码'}</span>
            </button>
          </div>
          <div className="p-3 font-mono text-xs text-[var(--text-primary)] overflow-x-auto select-all">
            <code>{commandText}</code>
          </div>
        </div>

        {/* 结构化要点 */}
        <div className="space-y-1.5 text-xs text-[var(--text-secondary)] bg-[var(--bg-subtle)] p-3 rounded-[var(--radius-md)] border border-[var(--border-subtle)]">
          <div><strong className="text-[var(--text-primary)]">【调度目标】</strong> 调度 gpt-image-2 (high) 输出 4:5 1080×1350 批次帧，最大并发 3</div>
          <div><strong className="text-[var(--text-primary)]">【生效配置】</strong> runtime-request.json、production-ledger.json</div>
          <div><strong className="text-[var(--text-primary)]">【风控门禁】</strong> 严格限流并发 3，保障一致性评分 ΔE &lt; 0.08</div>
          <div><strong className="text-[var(--text-primary)]">【画幅验收】</strong> 4:5 竖版标准无裁切，与基准主角保持一致</div>
          <div>
            <strong className="text-[var(--text-primary)]">【质检结论】</strong> 当前批次已产出，
            {inpaintDone ? (
              <span className="text-[var(--success)] font-medium">Frame #18 前端示例标记为已修复 · 非生产审核结论</span>
            ) : (
              <span className="text-[var(--warning)] font-medium">Frame #18 检测到玻璃倒影轻微双重重影，可点击一键重绘</span>
            )}
          </div>
        </div>

        {/* 前端示例核准切换卡片；不写入 runtime-request Authority。 */}
        <div className="flex items-center justify-between p-2.5 rounded-[var(--radius-md)] bg-[var(--bg-subtle)] border border-[var(--border-subtle)] text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-[var(--text-primary)] font-medium">runtime-request 示例配置</span>
            <span className="text-[var(--text-tertiary)] text-[11px] font-bold">UI DEMO</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const next = !reviewed;
                setReviewed(next);
                onShowToast(next ? '已标记前端示例配置为已核准 · 未写入 Runtime Authority' : '已撤销前端示例核准标记');
              }}
              className={`px-3 py-1 rounded text-xs font-semibold transition-colors cursor-pointer ${
                reviewed
                  ? 'bg-[var(--success-soft)] text-[var(--success)] border border-[color-mix(in_srgb,var(--success)_20%,var(--border-normal))]'
                  : 'bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-muted)] border border-[var(--border-normal)]'
              }`}
            >
              {reviewed ? '示例已核准 ✓' : '标记示例核准'}
            </button>
          </div>
        </div>

        {/* 批次 5 帧 Artifact 流 */}
        <div className="pt-3 border-t border-[var(--border-subtle)]">
          <div className="flex items-center justify-between text-xs font-mono text-[var(--text-tertiary)] mb-2">
            <span className="text-[var(--text-primary)] font-semibold">当前批次出图 (Batch #04 · 4:5 竖版)</span>
            <span className="text-[var(--text-secondary)] font-mono">点击缩略图可预览或切换质检状态</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
            {activeEpisode.currentBatch.items.map((item) => {
              const isPassed = passOverrides[item.id] !== undefined
                ? passOverrides[item.id]
                : (item.frameIndex === 18 ? inpaintDone : item.status === 'qa_passed');

              return (
                <div
                  key={item.id}
                  className={`group relative rounded-[var(--radius-md)] overflow-hidden aspect-[4/5] bg-black border transition-colors cursor-pointer ${
                    isPassed ? 'border-[var(--border-normal)] hover:border-[var(--border-strong)]' : 'border-[var(--warning)]'
                  }`}
                  onClick={() => setSelectedFrame(item)}
                >
                  <img
                    src={item.imageUrl}
                    alt={item.prompt}
                    className="w-full h-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-black/80 font-mono text-[10px] text-white font-bold">
                    #{item.frameIndex}
                  </div>
                  <div className="absolute bottom-1 right-1">
                    {isPassed ? (
                      <span className="px-1.5 py-0.5 rounded bg-black/80 text-[var(--success)] border border-[var(--success)] font-bold text-[10px]">
                        PASS
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 rounded bg-black text-white border border-white font-bold text-[10px]">
                        待修
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* 底部前端示例操作；不代表真实 Inpaint/Review 已执行。 */}
        <div className="flex justify-end gap-2 pt-2">
          {!inpaintDone ? (
            <button
              type="button"
              onClick={handleRunInpaint}
              className="h-9 px-3.5 rounded-[var(--radius-md)] bg-[var(--primary)] text-white text-xs font-semibold hover:bg-[var(--primary-hover)] transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Wand2 className="w-3.5 h-3.5 text-white" />
              <span>模拟 Frame #18 Inpaint 状态</span>
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-[var(--text-tertiary)] font-mono">前端示例已标记修复 · 未入库</span>
              <button
                type="button"
                onClick={() => {
                  setInpaintDone(false);
                  onShowToast('已重置 Frame #18 为待修状态');
                }}
                className="text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] cursor-pointer"
              >
                重置测试
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 质检详情弹窗：工作台浅色壳层，图片本体保留深色背景。 */}
      {selectedFrame && (
        <div
          className="storyos-overlay fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedFrame(null)}
        >
          <div
            className="storyos-elevated rounded-[var(--radius-lg)] max-w-sm w-full p-4 text-[var(--text-primary)] space-y-3"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label={`Frame #${selectedFrame.frameIndex} 前端示例质检详情`}
          >
            <div className="flex items-center justify-between text-xs font-mono border-b border-[var(--border-subtle)] pb-2 text-[var(--text-secondary)]">
              <span className="font-semibold text-[var(--text-primary)]">Frame #{selectedFrame.frameIndex} (4:5 1080×1350)</span>
              <button
                type="button"
                onClick={() => setSelectedFrame(null)}
                className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-1.5 py-0.5 rounded cursor-pointer"
                aria-label="关闭帧质检详情"
              >
                ✕
              </button>
            </div>

            <div className="aspect-[4/5] rounded-[var(--radius-md)] overflow-hidden border border-[var(--border-normal)] bg-black">
              <img
                src={selectedFrame.imageUrl}
                alt={selectedFrame.prompt}
                className="w-full h-full object-cover"
                referrerPolicy="no-referrer"
              />
            </div>

            <div className="text-xs font-mono text-[var(--text-secondary)] space-y-1.5 bg-[var(--bg-subtle)] p-2.5 rounded-[var(--radius-md)] border border-[var(--border-subtle)]">
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
                className="flex-1 h-9 rounded-[var(--radius-md)] bg-[var(--bg-surface)] border border-[var(--border-normal)] text-[var(--text-secondary)] hover:bg-[var(--bg-muted)] hover:text-[var(--text-primary)] text-xs font-medium cursor-pointer"
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
                  className="flex-1 h-9 rounded-[var(--radius-md)] bg-[var(--primary)] text-white text-xs font-semibold hover:bg-[var(--primary-hover)] cursor-pointer"
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
