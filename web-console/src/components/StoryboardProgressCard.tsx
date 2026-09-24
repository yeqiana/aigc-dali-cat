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
    <div id="storyboard-progress-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-zinc-100 gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-zinc-900 text-amber-400">
            <Film className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide">
                分镜进度与四幕节拍表 (Storyboard & Beats)
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-700 font-semibold border border-zinc-300">
                模拟演示数据 · 生产中
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-800 font-bold border border-zinc-200">
                {completedFrames} / {totalFrames} 帧
              </span>
            </div>
            <p className="text-[11px] text-zinc-600 mt-0.5">景别轴线、机位运动方式与戏剧台词节拍映射（正式画幅 4:5 1080×1350）</p>
          </div>
        </div>

        {/* Global Progress Bar */}
        <div className="flex items-center gap-2.5 min-w-[200px]">
          <div className="w-full bg-zinc-100 h-2 rounded-full overflow-hidden border border-zinc-200">
            <div
              className="bg-amber-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${Math.round((completedFrames / totalFrames) * 100)}%` }}
            />
          </div>
          <span className="text-xs font-mono font-bold text-zinc-900 shrink-0">
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
            className={`p-2 rounded-lg border text-left text-xs transition-all ${
              selectedAct === act.label
                ? 'bg-amber-50 border-amber-400 font-semibold'
                : 'bg-zinc-50 border-zinc-200 hover:bg-zinc-100'
            }`}
          >
            <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 mb-0.5">
              <span>幕 {i + 1}</span>
              <span className={act.status === 'completed' ? 'text-emerald-600 font-bold' : 'text-amber-600'}>
                {act.frames}
              </span>
            </div>
            <div className="text-xs font-medium text-zinc-800 truncate">{act.label}</div>
          </button>
        ))}
      </div>

      {/* Beats List */}
      <div className="space-y-2">
        {filteredBeats.map((beat) => (
          <div
            key={beat.id}
            className="p-2.5 rounded-lg border border-zinc-200/90 bg-zinc-50/50 hover:bg-zinc-50 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
          >
            <div className="flex items-center gap-3">
              {beat.thumbnailUrl ? (
                <img
                  src={beat.thumbnailUrl}
                  alt={beat.sceneName}
                  className="w-14 h-9 rounded object-cover border border-zinc-300 shrink-0 aspect-[21/9]"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-14 h-9 rounded bg-zinc-200 flex items-center justify-center text-zinc-400 shrink-0">
                  <Video className="w-4 h-4" />
                </div>
              )}

              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-zinc-900 bg-zinc-200 px-1.5 py-0.2 rounded text-[10px]">
                    BEAT #{beat.beatIndex < 10 ? `0${beat.beatIndex}` : beat.beatIndex}
                  </span>
                  <h4 className="font-bold text-zinc-900 text-xs">{beat.sceneName}</h4>
                  <span className="text-[10px] text-zinc-600 font-mono hidden sm:inline">
                    [{beat.shotType}]
                  </span>
                </div>
                <p className="text-[11px] text-zinc-600 mt-0.5 line-clamp-1">{beat.narration}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-[11px] font-mono shrink-0 self-end md:self-auto">
              <span className="text-zinc-600 hidden lg:inline">{beat.lighting}</span>
              <span className={`px-2 py-0.5 rounded font-bold ${
                beat.status === 'approved'
                  ? 'bg-emerald-100 text-emerald-800'
                  : beat.status === 'in_review'
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-zinc-200 text-zinc-700'
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
