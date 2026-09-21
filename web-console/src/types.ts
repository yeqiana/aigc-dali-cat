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
  genre: string;
  totalFrames: number;
  completedFrames: number;
  currentStage: ProductionStage;
  coverImage: string;
  updatedAt: string;
  runtimeRequest: RuntimeRequest;
  currentBatch: BatchQueue;
  frameReviews: FrameReviewResult[];
}

export type NavigationTab =
  | 'production_monitor' // 生产监控 (核心总控台)
  | 'episodes'           // 剧集管理
  | 'settings'           // 系统管理
  | 'workbench'          // 创作工作台 (分镜质检与调度台)
  | 'logs';              // 运行记录
