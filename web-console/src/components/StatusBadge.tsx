import React from 'react';
import { StoryRunStatus } from '../types';

interface StatusBadgeProps {
  status: StoryRunStatus;
  label?: string;
}

const STATUS_META: Record<
  StoryRunStatus,
  { tone: 'running' | 'success' | 'warning' | 'danger' | 'neutral'; label: string }
> = {
  RUNNING: { tone: 'running', label: 'Running' },
  WAITING: { tone: 'warning', label: 'Waiting' },
  RETRYING: { tone: 'warning', label: 'Retrying' },
  BLOCKED: { tone: 'danger', label: 'Blocked · 需人工' },
  FAILED: { tone: 'danger', label: 'Failed' },
  COMPLETED: { tone: 'success', label: 'Completed' },
  CANCELLED: { tone: 'neutral', label: 'Cancelled' },
  PENDING: { tone: 'neutral', label: 'Not Started' },
};

const toneColor: Record<StatusBadgeProps['status'], string> = {
  RUNNING: 'var(--primary)',
  WAITING: 'var(--warning)',
  RETRYING: 'var(--warning)',
  BLOCKED: 'var(--danger)',
  FAILED: 'var(--danger)',
  COMPLETED: 'var(--success)',
  CANCELLED: 'var(--text-tertiary)',
  PENDING: 'var(--text-tertiary)',
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
}) => {
  const meta = STATUS_META[status];

  return (
    <span
      className={`storyos-status storyos-status--${meta.tone} font-mono`}
      aria-label={`状态：${label || meta.label}`}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ backgroundColor: toneColor[status] }}
      />
      <span>{label || meta.label}</span>
    </span>
  );
};
