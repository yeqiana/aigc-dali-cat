import React from 'react';
import {
  Check,
  ChevronRight,
  GitBranch
} from 'lucide-react';
import { Episode, ProductionStage } from '../../types';

interface ProductionPipelineViewProps {
  activeEpisode: Episode;
  onStageChange: (stage: ProductionStage) => void;
  onGoToWorkbench: () => void;
  onShowToast?: (msg: string) => void;
}

interface SimpleStageMeta {
  id: ProductionStage;
  stepNo: string;
  name: string;
  desc: string;
  gateRule: string;
  deliverable: string;
  agent: string;
}

const PIPELINE_STAGES: SimpleStageMeta[] = [
  {
    id: 'IDEA_LOCK',
    stepNo: '01',
    name: '创意锁定',
    desc: '剧本核心冲突、悬念节拍与立项参数冻结',
    gateRule: '核心冲突明确，主要角色 ≤ 3 人',
    deliverable: '剧情立项卡 · 节拍大纲',
    agent: 'ConceptAnchorAgent',
  },
  {
    id: 'STORYBOARD_LOCK',
    stepNo: '02',
    name: '分镜锁定',
    desc: '4:5 竖版景别轴线、提示词与机位镜头冻结',
    gateRule: '4:5 竖版构图无裁切，20-32 帧镜头',
    deliverable: '结构化分镜列表 (Storyboard Beats)',
    agent: 'StoryboardDirectorAgent',
  },
  {
    id: 'VISUAL_CALIBRATE',
    stepNo: '03',
    name: '视觉校准',
    desc: '主角面容 FaceID、光影基调与场景锚定',
    gateRule: '主角面容一致性 ≥98.0%，色温偏差 <5%',
    deliverable: '主角面容锚点图 · 场景基准图',
    agent: 'VisualCalibratorAgent',
  },
  {
    id: 'PROD_APPROVED',
    stepNo: '04',
    name: '生产通过',
    desc: '5 帧逻辑批次并行出图与逐帧质检拦截',
    gateRule: '综合一致性 ≥95.0%，无肢体畸变',
    deliverable: '全量批次帧 · 逐帧质检卡',
    agent: 'BatchScheduler + CriticAgent',
  },
  {
    id: 'READY_TO_PUBLISH',
    stepNo: '05',
    name: '待发布',
    desc: '4:5 1080×1350 规格合规终审与清单签署',
    gateRule: '1080×1350 标定通过，Preflight 全绿',
    deliverable: 'release-manifest.json 终审清单',
    agent: 'PreflightReviewAgent',
  },
  {
    id: 'PUBLISHED',
    stepNo: '06',
    name: '已发布',
    desc: '短剧渠道矩阵自动化打包与全网分发上线',
    gateRule: '分发接口校验成功，母盘哈希一致',
    deliverable: '标准短剧渠道包 · 预告物料',
    agent: 'DistributionAgent',
  },
  {
    id: 'POST_MORTEM',
    stepNo: '07',
    name: '数据复盘',
    desc: '前 3 秒完播率、跳出点归因与参数优化回路',
    gateRule: '复盘数据归因完毕，写入经验库',
    deliverable: '剧集生产效能归因报告',
    agent: 'DataAuditorAgent',
  },
];

export const ProductionPipelineView: React.FC<ProductionPipelineViewProps> = ({
  activeEpisode,
  onStageChange,
  onGoToWorkbench,
  onShowToast,
}) => {
  const currentIndex = PIPELINE_STAGES.findIndex((s) => s.id === activeEpisode.currentStage);
  const safeCurrentIndex = currentIndex >= 0 ? currentIndex : 3;

  const handleSetStage = (stageId: ProductionStage, stageName: string) => {
    onStageChange(stageId);
    if (onShowToast) {
      onShowToast(`当前作品已切换至阶段: ${stageName}`);
    }
  };

  return (
    <div id="production-pipeline-view" className="space-y-3 font-sans antialiased text-[var(--text-secondary)] select-none">
      {/* 极简顶栏 */}
      <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-emerald-400" />
          <h1 className="text-sm font-semibold text-[var(--text-primary)] tracking-tight">主要流程</h1>
          <span className="text-[11px] font-mono text-[var(--text-tertiary)]">
            当前作品: 《{activeEpisode.title}》
          </span>
        </div>

        <button
          type="button"
          onClick={onGoToWorkbench}
          className="h-[28px] px-2.5 rounded-[4px] bg-[var(--text-primary)] text-[var(--bg-app)] hover:opacity-90 text-xs font-semibold flex items-center gap-1 transition-opacity cursor-pointer shadow-xs"
        >
          <span>前往工作台</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 极简 7 大阶段流程列表（去堆砌、单行清晰扫描） */}
      <div className="rounded-[6px] border border-[var(--border-normal)] bg-[var(--bg-surface)] divide-y divide-[var(--border-subtle)] overflow-hidden shadow-xs">
        {PIPELINE_STAGES.map((stage, idx) => {
          const isPassed = idx < safeCurrentIndex;
          const isCurrent = idx === safeCurrentIndex;

          return (
            <div
              key={stage.id}
              className={`p-3 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                isCurrent
                  ? 'bg-[var(--bg-selected)]'
                  : 'hover:bg-[var(--bg-hover)]'
              }`}
            >
              {/* 阶段基本信息 */}
              <div className="flex items-center gap-3 min-w-0">
                <span className={`w-6 h-6 rounded-[4px] font-mono text-xs font-semibold flex items-center justify-center shrink-0 ${
                  isCurrent
                    ? 'bg-[#58A6FF] text-white font-bold shadow-xs'
                    : isPassed
                    ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                    : 'bg-[var(--bg-elevated)] text-[var(--text-tertiary)] border border-[var(--border-subtle)]'
                }`}>
                  {isPassed ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : stage.stepNo}
                </span>

                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-semibold ${isCurrent ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}>
                      {stage.name}
                    </span>
                    <span className="text-[11px] text-[var(--text-tertiary)] truncate max-w-xs hidden md:inline">
                      {stage.desc}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-x-3 text-[11px] font-mono mt-0.5 text-[var(--text-tertiary)]">
                    <span>门禁: {stage.gateRule}</span>
                    <span>·</span>
                    <span>交付: {stage.deliverable}</span>
                  </div>
                </div>
              </div>

              {/* 状态与切换操作 */}
              <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                {isCurrent ? (
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-[4px] bg-blue-500/15 text-[#58A6FF] border border-blue-500/30 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#58A6FF] animate-pulse" />
                    <span>进行中</span>
                  </span>
                ) : isPassed ? (
                  <span className="text-[11px] font-mono text-emerald-400 font-medium">已完成</span>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleSetStage(stage.id, stage.name)}
                    className="text-[11px] font-mono text-[var(--text-tertiary)] hover:text-[var(--text-primary)] px-2 py-0.5 rounded-[4px] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] transition-colors cursor-pointer"
                  >
                    设为当前
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
