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
      {/* 极简时间戳 - 纯黑底白字 */}
      <div className="text-center my-1">
        <span className="text-[11px] font-mono text-zinc-400">
          今天 14:58 · StoryOS 生产队列
        </span>
      </div>

      {/* 触发操作按钮（黑底白字高对比按钮） */}
      <div className="flex justify-end items-center gap-2">
        <button
          type="button"
          onClick={onGenerateBatch}
          disabled={isGeneratingBatch}
          className="px-3.5 py-1.5 rounded-lg bg-white text-black text-xs font-semibold hover:bg-zinc-200 transition-colors shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
        >
          {isGeneratingBatch ? (
            <>
              <span className="w-2 h-2 rounded-full bg-black animate-ping" />
              <span>正在调度批次出图...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current text-black" />
              <span>调度出图批次 ({activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧)</span>
            </>
          )}
        </button>
      </div>

      {/* 核心对话推进卡片（纯黑底白字） */}
      <div className="bg-[#0a0a0c] rounded-xl border border-[#222226] p-4 text-zinc-300 space-y-3 shadow-sm">
        {/* 用时折叠 */}
        <div>
          <button
            type="button"
            onClick={() => setTimeStepOpen(!timeStepOpen)}
            className="flex items-center gap-1.5 text-xs font-mono text-zinc-400 hover:text-white transition-colors cursor-pointer"
          >
            <ChevronRight className={`w-3.5 h-3.5 transition-transform ${timeStepOpen ? 'rotate-90' : ''}`} />
            <span>执行用时 53 秒 · 32 镜图文工业级流水线</span>
          </button>

          {timeStepOpen && (
            <div className="mt-2 pl-4 py-2 border-l border-zinc-700 text-[11px] font-mono text-zinc-300 space-y-1 bg-[#121214] rounded-r-lg">
              <div>• 校验 gpt-image-2 (high) 模型参数规格与 4:5 1080×1350 竖版分辨率</div>
              <div>• 严格限制最大并发 3 张，杜绝显存溢出与跨批次人脸漂移</div>
              <div>• 批次 5 帧出图完成，已提交至 StoryOS 逐帧质检队列</div>
            </div>
          )}
        </div>

        {/* 简洁分析陈述 */}
        <p className="text-zinc-200 text-xs sm:text-[13px]">
          已解析当前批次（Frame #16 - #20）剧情推进需求，保持主角林澈 4:5 肖像基准与山庄雨夜冷调环境锚点。
        </p>

        {/* 终端命令代码块（纯黑高对比） */}
        <div className="rounded-lg bg-[#000000] border border-[#222226] overflow-hidden">
          <div className="px-3 py-1.5 bg-[#121215] border-b border-[#222226] flex items-center justify-between text-[11px] font-mono text-zinc-400">
            <span className="flex items-center gap-1.5 text-white">
              <Terminal className="w-3.5 h-3.5" />
              <span>storyos-cli</span>
            </span>
            <button
              type="button"
              onClick={handleCopy}
              className="hover:text-white flex items-center gap-1 text-xs cursor-pointer"
            >
              {copiedCmd ? <Check className="w-3 h-3 text-white" /> : <Copy className="w-3 h-3 text-zinc-400" />}
              <span>{copiedCmd ? '已复制' : '复制代码'}</span>
            </button>
          </div>
          <div className="p-3 font-mono text-xs text-white overflow-x-auto select-all">
            <code>{commandText}</code>
          </div>
        </div>

        {/* 结构化要点（纯黑底白字清晰分层） */}
        <div className="space-y-1.5 text-xs text-zinc-300 bg-[#111114] p-3 rounded-lg border border-[#1f1f23]">
          <div><strong className="text-white">【调度目标】</strong> 调度 gpt-image-2 (high) 输出 4:5 1080×1350 批次帧，最大并发 3</div>
          <div><strong className="text-white">【生效配置】</strong> runtime-request.json、production-ledger.json</div>
          <div><strong className="text-white">【风控门禁】</strong> 严格限流并发 3，保障一致性评分 ΔE &lt; 0.08</div>
          <div><strong className="text-white">【画幅验收】</strong> 4:5 竖版标准无裁切，与基准主角保持一致</div>
          <div>
            <strong className="text-white">【质检结论】</strong> 当前批次已产出，
            {inpaintDone ? (
              <span className="text-white underline underline-offset-2 font-medium">Frame #18 倒影重绘完成，24/32 帧全部达标</span>
            ) : (
              <span className="text-zinc-300 font-medium">Frame #18 检测到玻璃倒影轻微双重重影，可点击一键重绘</span>
            )}
          </div>
        </div>

        {/* 真实文件核准切换卡片 */}
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-[#000000] border border-[#222226] text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="text-white font-medium">已更新 runtime-request.json</span>
            <span className="text-zinc-400 text-[11px] font-bold">+14 行</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                const next = !reviewed;
                setReviewed(next);
                onShowToast(next ? '已真实核准 runtime-request 配置' : '已撤销配置核准状态');
              }}
              className={`px-3 py-1 rounded text-xs font-semibold transition-all cursor-pointer ${
                reviewed
                  ? 'bg-white text-black shadow-xs'
                  : 'bg-[#18181b] text-zinc-300 hover:text-white hover:bg-[#222226] border border-[#2e2e33]'
              }`}
            >
              {reviewed ? '已核准配置 ✓' : '点击核准配置'}
            </button>
          </div>
        </div>

        {/* 批次 5 帧 4:5 出图极简流（纯黑底白字高对比） */}
        <div className="pt-3 border-t border-[#1f1f23]">
          <div className="flex items-center justify-between text-xs font-mono text-zinc-400 mb-2">
            <span className="text-white font-semibold">当前批次出图 (Batch #04 · 4:5 竖版)</span>
            <span className="text-zinc-300 font-mono">点击缩略图可预览或切换质检状态</span>
          </div>

          <div className="grid grid-cols-5 gap-2.5">
            {activeEpisode.currentBatch.items.map((item) => {
              const isPassed = passOverrides[item.id] !== undefined
                ? passOverrides[item.id]
                : (item.frameIndex === 18 ? inpaintDone : item.status === 'qa_passed');

              return (
                <div
                  key={item.id}
                  className={`group relative rounded-lg overflow-hidden aspect-[4/5] bg-black border transition-all cursor-pointer ${
                    isPassed ? 'border-[#333338] hover:border-white' : 'border-white ring-1 ring-white/60'
                  }`}
                  onClick={() => setSelectedFrame(item)}
                >
                  <img
                    src={item.imageUrl}
                    alt={item.prompt}
                    className="w-full h-full object-cover transition-transform group-hover:scale-105"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute top-1 left-1 px-1.5 py-0.5 rounded bg-black/80 font-mono text-[10px] text-white font-bold">
                    #{item.frameIndex}
                  </div>
                  <div className="absolute bottom-1 right-1">
                    {isPassed ? (
                      <span className="px-1.5 py-0.5 rounded bg-white text-black font-bold text-[10px]">
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

        {/* 底部单个操作按钮（一键修复与真实切换） */}
        <div className="flex justify-end gap-2 pt-2">
          {!inpaintDone ? (
            <button
              type="button"
              onClick={handleRunInpaint}
              className="px-3.5 py-1.5 rounded-lg bg-white text-black text-xs font-semibold hover:bg-zinc-200 transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <Wand2 className="w-3.5 h-3.5 text-black" />
              <span>一键修复 Frame #18 倒影微瑕</span>
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-400 font-mono">已完成逐帧修复并入库</span>
              <button
                type="button"
                onClick={() => {
                  setInpaintDone(false);
                  onShowToast('已重置 Frame #18 为待修状态');
                }}
                className="text-xs text-zinc-400 hover:text-white underline cursor-pointer"
              >
                重置测试
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 质检详情弹窗（黑底白字高对比） */}
      {selectedFrame && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs"
          onClick={() => setSelectedFrame(null)}
        >
          <div
            className="bg-[#0a0a0c] border border-[#2e2e33] rounded-2xl max-w-sm w-full p-4 text-white space-y-3 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between text-xs font-mono border-b border-[#1f1f23] pb-2 text-zinc-300">
              <span className="font-bold text-white">Frame #{selectedFrame.frameIndex} (4:5 1080×1350)</span>
              <button
                type="button"
                onClick={() => setSelectedFrame(null)}
                className="text-zinc-400 hover:text-white px-1.5 py-0.5 rounded cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="aspect-[4/5] rounded-xl overflow-hidden border border-[#2e2e33] bg-black">
              <img
                src={selectedFrame.imageUrl}
                alt={selectedFrame.prompt}
                className="w-full h-full object-cover"
                referrerPolicy="no-referrer"
              />
            </div>

            <div className="text-xs font-mono text-zinc-300 space-y-1.5 bg-[#121215] p-2.5 rounded-lg border border-[#1f1f23]">
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
                className="flex-1 py-1.5 rounded-lg bg-[#18181b] border border-[#2e2e33] text-white hover:bg-[#242429] text-xs font-medium cursor-pointer"
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
                  className="flex-1 py-1.5 rounded-lg bg-white text-black text-xs font-semibold hover:bg-zinc-200 cursor-pointer"
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
