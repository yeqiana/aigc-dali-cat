export function responseItems(body) {
  if (Array.isArray(body)) return body;
  return Array.isArray(body?.items) ? body.items : [];
}

export function formatListMeta(count, total, hasMore) {
  return hasMore ? `已载入 ${count} / 共 ${total} 条` : `${count} 条记录`;
}

export function formatDateTime(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString('zh-CN', { hour12: false }).replaceAll('/', '-');
}

export function normalizeRuntimeRow(row) {
  const progress = row.image_progress || {};
  const totalFrames = Number(progress.expected_frames || 0);
  const completedFrames = Number(progress.accepted_frames || 0);
  return {
    id: row.episode_ref || row.episode_id || row.episode || row.title,
    code: row.episode_ref || row.episode_id || '-',
    title: row.title || row.episode || row.episode_ref || '未命名剧集',
    currentStage: row.production_stage || row.source_states?.episode_stage || 'UNKNOWN',
    executionStatus: row.execution_status || 'UNKNOWN',
    currentAction: row.current_action || row.next_step || '-',
    completedFrames,
    totalFrames,
    updatedAt: formatDateTime(row.updated_at || row.observed_at),
    source: row.state_source || row.projection_level || '平台运行时',
  };
}

export function runtimeTone(status) {
  if (['COMPLETE', 'PUBLISH_READY', 'PUBLISHED', 'COMPLETED'].includes(status)) return 'success';
  if (['BLOCKED', 'HARD_STOP', 'ERROR', 'NEEDS_USER'].includes(status)) return 'danger';
  if (['RUNNING', 'READY', 'PRODUCTION_PASSED'].includes(status)) return 'info';
  if (['HOST_WAIT', 'CAPABILITY_WAIT', 'STORYBOARD_LOCKED'].includes(status)) return 'warning';
  return 'neutral';
}
