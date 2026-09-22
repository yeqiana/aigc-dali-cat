export const progressStages = [
  { code: 'IDEA_LOCKED', label: '选题锁定' },
  { code: 'STORYBOARD_LOCKED', label: '分镜锁定' },
  { code: 'VISUAL_CALIBRATED', label: '视觉校准' },
  { code: 'PRODUCTION_PASSED', label: '制作通过' },
  { code: 'PUBLISH_READY', label: '可发布' },
  { code: 'PUBLISHED', label: '已发布' },
  { code: 'DATA_REVIEWED', label: '数据复盘' },
];

export function stageIndex(stage) {
  const index = progressStages.findIndex((item) => item.code === stage);
  return index;
}

export function stageLabel(stage) {
  return progressStages.find((item) => item.code === stage)?.label || stage || '未知';
}
