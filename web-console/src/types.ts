export type ProductionStage =
  | 'IDEA_LOCKED'        // 创意锁定
  | 'STORYBOARD_LOCKED'  // 分镜锁定
  | 'VISUAL_CALIBRATED'  // 视觉校准
  | 'PRODUCTION_PASSED'  // 生产通过
  | 'PUBLISH_READY'      // 待发布
  | 'PUBLISHED'        // 已发布
  | 'DATA_REVIEWED';   // 数据复盘

export interface RuntimeRequest {
  imageModel: string;          // 'gpt-image-2'
  quality: 'high' | 'standard';// 'high'
  aspectRatio: string;         // '4:5 1080×1350'
  batchMode: string;           // '5 帧逻辑批次'
  maxConcurrentImages: number; // 3
  executionLayer: string;      // 'StoryOS Engine'
  sourceBadge: '未接真实投影' | '示例数据';
  safetyThreshold?: string;
  negativePrompt?: string;
  notes?: string;
  resolution?: string;
}

export interface BatchItem {
  id: string;
  frameIndex: number;
  prompt: string;
  seed: number;
  status: 'rendering' | 'ready' | 'qa_passed' | 'qa_warning' | 'needs_reroll';
  progress: number;
  renderTime: string;
  imageUrl: string;
  consistencyScore: number;
  driftWarning?: string;
}

export interface BatchQueue {
  batchId: string;
  batchNumber: number;
  batchName: string;
  targetFrames: string;
  totalImages: number;
  createdAt: string;
  status: 'processing' | 'ready_for_review' | 'completed';
  items: BatchItem[];
}

export interface FrameReviewResult {
  frameId: string;
  frameIndex: number;
  timestamp: string;
  imageUrl: string;
  shotType: string;
  facialScore: number;
  lightConsistency: number;
  anatomyScore: number;
  verdict: 'PASS' | 'WARN' | 'FAIL';
  issueTags: string[];
  reviewer: string;
  comment: string;
}

export interface Episode {
  id: string;
  code: string;
  title: string;
  synopsis: string;
  logline: string;
  genre: string;
  targetAudience: string;
  totalFrames: number;
  completedFrames: number;
  currentStage: ProductionStage;
  stageProgressPercent: number;
  coverImage: string;
  updatedAt: string;
  runtimeRequest: RuntimeRequest;
  currentBatch: BatchQueue;
  frameReviews: FrameReviewResult[];
}

export type NavigationTab =
  | 'overview'           // 总览
  | 'production_monitor' // 生产监控 (核心总控台)
  | 'episodes'           // 剧集管理
  | 'assets'             // 素材资产
  | 'agents'             // Agent 管理
  | 'analytics'          // 数据看板
  | 'exceptions'         // 异常中心
  | 'settings'           // 系统管理
  | 'workbench'          // 创作工作台 (分镜质检与调度台)
  | 'visual_lock'        // 视觉锁定
  | 'batch_gen'          // 批量出图
  | 'frame_qa'           // 逐帧审核
  | 'publish_center'     // 发布中心
  | 'logs';              // 运行记录

// ================= StoryOS 生产监控台 V1.0 核心模型 =================
export type StoryRunStage =
  | 'CREATE'
  | 'STORY_LOCK'
  | 'STORYBOARD'
  | 'CHARACTER_CONTRACT'
  | 'VISUAL_LOCK'
  | 'PRODUCTION'
  | 'REVIEW'
  | 'PUBLISH'
  | 'COMPLETED';

export type StoryRunStatus =
  | 'RUNNING'
  | 'WAITING'
  | 'RETRYING'
  | 'BLOCKED'
  | 'FAILED'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'PENDING';

export type FrameStatus =
  | 'PASSED'
  | 'GENERATING'
  | 'QUEUED'
  | 'RETRYING'
  | 'BLOCKED'
  | 'NOT_STARTED';

export interface FrameReferenceItem {
  name: string;
  url?: string;
  type?: 'character' | 'scene' | 'style' | 'pose';
}

export interface FrameDetailItem {
  frameNo: number;
  frameCode: string;
  status: FrameStatus;
  thumbnail?: string;
  duration?: string;
  attempt: string; // e.g. "1 / 1", "2 / 3"
  currentSubAction?: string; // e.g. "IMAGE_GENERATION", "COMPILE_PROMPT", "RESOLVE_REFERENCE", "DENOISING"
  lastError?: string;
  failureStage?: string; // e.g. "provider_download", "inference_gateway"
  failedAt?: string;
  completedAt?: string;
  nextRetryInSeconds?: number;
  provider?: string;
  modelName?: string;
  references?: string[];
  referenceItems?: FrameReferenceItem[];
  prompt?: string;
  negativePrompt?: string;
  artifactUrl?: string;
  artifactName?: string;
  artifactSize?: string;
  traceId?: string;
  recentEvents?: { time: string; text: string; type?: 'error' | 'schedule' | 'start' | 'success' }[];
}

export interface PipelineStageDetail {
  key: StoryRunStage;
  label: string;
  status: 'completed' | 'running' | 'warning' | 'pending';
  startTime?: string;
  endTime?: string;
  timeCost?: string;
  attempt?: string;
  inputArtifacts?: string[];
  outputArtifacts?: string[];
  traceId?: string;
  error?: string;
  description?: string;
}

export interface RunArtifactItem {
  id: string;
  name: string;
  stage: StoryRunStage;
  fileType: 'json' | 'image' | 'archive' | 'markdown';
  size: string;
  updatedAt: string;
  downloadUrl?: string;
  previewSnippet?: string;
}

export interface RunLogItem {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  component: string;
  message: string;
  traceId?: string;
}

export interface RunEventItem {
  id: string;
  timestamp: string;
  stage: string;
  eventName: string;
  status: 'success' | 'warn' | 'error' | 'info';
  detail: string;
  durationMs?: number;
}

export interface StoryRunItem {
  id: string;
  storyName: string;
  runId: string;
  currentStage: StoryRunStage;
  stageLabel: string;
  status: StoryRunStatus;
  waitingReason?: string; // e.g. "等待模型", "Queue #7", "依赖就绪中"
  progressPercent: number; // 综合加权总进度
  completedFrames: number;
  totalFrames: number;
  currentAction: string; // e.g. "生成 Frame14", "内容审核", "Reference 校验"
  createdAt: string;
  duration: string;
  lastHeartbeatAgo: string; // e.g. "3 秒前"
  heartbeatSeconds: number;
  exceptionSummary?: string; // e.g. "Network Error", "等待模型"
  exceptionType?: 'manual' | 'auto_retry' | 'none';
  storyDescription?: string;
  coverImage?: string;
  frames: FrameDetailItem[];
  pipelineStages: PipelineStageDetail[];
  events?: RunEventItem[];
  artifacts?: RunArtifactItem[];
  logs?: RunLogItem[];
  runtimeEnv?: {
    workerId: string;
    gpuNode: string;
    modelProvider: string;
    imageResolution: string;
    aspectRatio: string;
    heartbeatInterval: string;
    activeConcurrency: string;
  };
}
