export const statusLabels = {
  AUTO: '自动处理',
  COMPLETED: '已完成',
  COMPLETE: '已完成',
  DOWN: '不可用',
  BLOCKED: '已阻塞',
  ERROR: '错误',
  FAILED: '失败',
  HARD_STOP: '已停止',
  HOST_WAIT: '等待宿主',
  CAPABILITY_WAIT: '等待能力',
  IDEA_LOCKED: '选题已锁定',
  IDLE: '空闲',
  NEEDS_USER: '需要处理',
  PUBLISH_READY: '可发布',
  PRODUCTION_PASSED: '制作通过',
  QUEUED: '排队中',
  READY: '待执行',
  RUNNING: '运行中',
  READY_FOR_REVIEW: '待复核',
  STORYBOARD_LOCKED: '分镜已锁定',
  SUCCESS: '成功',
  UNKNOWN: '未知',
  VISUAL_CALIBRATED: '视觉已校准',
  PUBLISHED: '已发布',
  DATA_REVIEWED: '数据已复盘',
};

export function statusLabel(value) {
  if (value === undefined || value === null || value === '') return '';
  return statusLabels[value] || String(value);
}
