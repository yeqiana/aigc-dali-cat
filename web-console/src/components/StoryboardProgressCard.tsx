import React, { useState } from 'react';
import {
  Film,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronRight,
  Maximize2,
  Video,
  Eye
} from 'lucide-react';
import { StoryboardBeat } from '../types';

interface StoryboardProgressCardProps {
  beats: StoryboardBeat[];
  totalFrames: number;
  completedFrames: number;
}

export const StoryboardProgressCard: React.FC<StoryboardProgressCardProps> = ({
  beats,
  totalFrames,
  completedFrames,
}) => {
  const [selectedAct, setSelectedAct] = useState<string>('ALL');

  const actStats = [
    { label: '第一幕：建立日常', frames: '4/4 帧', status: 'completed' },
    { label: '第二幕：异常初显', frames: '8/8 帧', status: 'completed' },
    { label: '第三幕：危机爆发', frames: '10/12 帧', status: 'in_progress' },
    { label: '终局：反转回响', frames: '2/8 帧', status: 'queued' },
  ];

  const filteredBeats = selectedAct === 'ALL'
    ? beats
    : beats.filter(b => b.act === selectedAct);

  return (
    <div id="storyboard-progress-card" className="storyos-surface p-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-[var(--border-subtle)] gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-[var(--radius-sm)] bg-[var(--primary-soft)] text-[var(--primary)]">
            <Film className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] tracking-wide">
                分镜进度与四幕节拍表 (Storyboard & Beats)
              </h3>
              <span className="storyos-status storyos-status--neutral font-mono">
                模拟演示数据 · 生产中
              </span>
              <span className="storyos-status storyos-status--info font-mono">
                {completedFrames} / {totalFrames} 帧
              </span>
            </div>
            <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">景别轴线、机位运动方式与戏剧台词节拍映射（正式画幅 4:5 1080×1350）</p>
          </div>
        </div>

        {/* Global Progress Bar */}
        <div className="flex items-center gap-2.5 min-w-[200px]">
          <div className="w-full bg-[var(--bg-muted)] h-2 rounded-full overflow-hidden border border-[var(--border-subtle)]">
            <div
              className="bg-[var(--primary)] h-full rounded-full transition-[width] duration-500"
              style={{ width: `${Math.round((completedFrames / totalFrames) * 100)}%` }}
            />
          </div>
          <span className="text-xs font-mono font-semibold text-[var(--text-primary)] shrink-0">
            {Math.round((completedFrames / totalFrames) * 100)}%
          </span>
        </div>
      </div>

      {/* Act Progression Pills */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        {actStats.map((act, i) => (
          <button
            key={i}
            onClick={() => setSelectedAct(selectedAct === act.label ? 'ALL' : act.label)}
            className={`p-2 rounded-[var(--radius-md)] border text-left text-xs transition-colors ${
              selectedAct === act.label
                ? 'bg-[var(--primary-soft)] border-[var(--primary)] font-semibold'
                : 'bg-[var(--bg-subtle)] border-[var(--border-normal)] hover:bg-[var(--bg-muted)]'
            }`}
          >
            <div className="flex items-center justify-between text-[10px] font-mono text-[var(--text-tertiary)] mb-0.5">
              <span>幕 {i + 1}</span>
              <span className={act.status === 'completed' ? 'text-[var(--success)] font-semibold' : 'text-[var(--warning)]'}>
                {act.frames}
              </span>
            </div>
            <div className="text-xs font-medium text-[var(--text-primary)] truncate">{act.label}</div>
          </button>
        ))}
      </div>

      {/* Beats List */}
      <div className="space-y-2">
        {filteredBeats.map((beat) => (
          <div
            key={beat.id}
            className="p-2.5 rounded-[var(--radius-md)] border border-[var(--border-normal)] bg-[var(--bg-subtle)] hover:bg-[var(--bg-muted)] flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
          >
            <div className="flex items-center gap-3">
              {beat.thumbnailUrl ? (
                <img
                  src={beat.thumbnailUrl}
                  alt={beat.sceneName}
                  className="w-14 h-9 rounded-[var(--radius-sm)] object-cover border border-[var(--border-normal)] shrink-0 aspect-[21/9]"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-14 h-9 rounded-[var(--radius-sm)] bg-[var(--bg-muted)] flex items-center justify-center text-[var(--text-subtle)] shrink-0">
                  <Video className="w-4 h-4" />
                </div>
              )}

              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-semibold text-[var(--text-primary)] bg-[var(--bg-muted)] px-1.5 py-0.5 rounded-[var(--radius-xs)] text-[10px]">
                    BEAT #{beat.beatIndex < 10 ? `0${beat.beatIndex}` : beat.beatIndex}
                  </span>
                  <h4 className="font-semibold text-[var(--text-primary)] text-xs">{beat.sceneName}</h4>
                  <span className="text-[10px] text-[var(--text-tertiary)] font-mono hidden sm:inline">
                    [{beat.shotType}]
                  </span>
                </div>
                <p className="text-[11px] text-[var(--text-secondary)] mt-0.5 line-clamp-1">{beat.narration}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-[11px] font-mono shrink-0 self-end md:self-auto">
              <span className="text-[var(--text-tertiary)] hidden lg:inline">{beat.lighting}</span>
              <span className={`px-2 py-0.5 rounded font-bold ${
                beat.status === 'approved'
                  ? 'bg-[var(--success-soft)] text-[var(--success)]'
                  : beat.status === 'in_review'
                  ? 'bg-[var(--warning-soft)] text-[var(--warning)]'
                  : 'bg-[var(--bg-muted)] text-[var(--text-secondary)]'
              }`}>
                {beat.status === 'approved' ? '✓ 终审通过' : beat.status === 'in_review' ? '逐帧审核中' : '渲染中'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
