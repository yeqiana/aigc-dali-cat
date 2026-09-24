import React, { useState } from 'react';
import {
  BarChart3,
  TrendingUp,
  Eye,
  Share2,
  Heart,
  Clock,
  Flame,
  ChevronRight,
  Info
} from 'lucide-react';
import { PerformanceData } from '../types';

interface PerformanceMetricsCardProps {
  performance: Record<'6h' | '24h' | '48h' | '7d', PerformanceData>;
  isPublished: boolean;
}

export const PerformanceMetricsCard: React.FC<PerformanceMetricsCardProps> = ({
  performance,
  isPublished,
}) => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'6h' | '24h' | '48h' | '7d'>('6h');

  const currentData = performance[selectedTimeframe];
  const timeframes: Array<'6h' | '24h' | '48h' | '7d'> = ['6h', '24h', '48h', '7d'];

  // Calculate SVG sparkline coordinates
  const points = currentData.trendData || [];
  const maxVal = Math.max(...points.map(p => p.value), 10);
  const minVal = Math.min(...points.map(p => p.value), 0);
  const range = maxVal - minVal || 1;

  const svgPoints = points.map((p, index) => {
    const x = (index / (points.length - 1 || 1)) * 300;
    const y = 60 - ((p.value - minVal) / range) * 50;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div id="performance-metrics-card" className="bg-white rounded-xl border border-zinc-200 p-4 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-zinc-100 gap-2">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-zinc-900 text-amber-400">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-zinc-900 uppercase tracking-wide flex items-center gap-2">
              <span>6h / 24h / 48h / 7d 数据复盘与受众归因</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold border bg-amber-50 text-amber-800 border-amber-300">
                {isPublished ? '示例数据 · 历史归档映射' : '示例数据 · 待连接工作区'}
              </span>
            </h3>
            <p className="text-[11px] text-zinc-600">
              {isPublished
                ? '全网分发多端实收播放、跳出率节拍与长尾破圈热力（已发布剧集实测回流）'
                : '注意：当前剧集生产中尚未发布，以下指标为算法大盘模拟演示数据，严禁伪造已发布事实'}
            </p>
          </div>
        </div>

        {/* Timeframe Selector Tabs */}
        <div className="flex items-center bg-zinc-100 p-1 rounded-lg border border-zinc-200">
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => setSelectedTimeframe(tf)}
              className={`px-2.5 py-1 rounded text-xs font-mono font-bold transition-all ${
                selectedTimeframe === tf
                  ? 'bg-white text-zinc-900 shadow-xs border border-zinc-200/80'
                  : 'text-zinc-500 hover:text-zinc-800'
              }`}
            >
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Honest unreleased notice if in production */}
      {!isPublished && (
        <div className="mb-3 p-2.5 rounded-lg bg-zinc-50 border border-zinc-200 text-[11px] font-mono text-zinc-600 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span>
              <strong>数据来源说明：</strong>本卡片为同题材基线预测（<strong>模拟演示数据</strong>）。当前剧集处于生产中未发布，不伪造全网投放与播放量事实。
            </span>
          </div>
          <span className="text-[10px] text-zinc-500 shrink-0 font-bold">UNPUBLISHED_SIMULATION</span>
        </div>
      )}

      {/* Main KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 mb-3">
        {/* Metric 1: Completion Rate */}
        <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-200/80">
          <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono mb-1">
            <span className="flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
              <span>全剧完播率</span>
            </span>
            <span className="text-emerald-700 font-bold">{currentData.completionDelta}</span>
          </div>
          <div className="text-xl font-bold font-mono text-zinc-900 tracking-tight">
            {currentData.completionRate}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5 font-mono">行业平均 64.2%</div>
        </div>

        {/* Metric 2: Views */}
        <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-200/80">
          <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono mb-1">
            <span className="flex items-center gap-1">
              <Eye className="w-3.5 h-3.5 text-blue-600" />
              <span>播放展现量</span>
            </span>
            <span className="text-blue-700 font-bold">{currentData.viewsDelta}</span>
          </div>
          <div className="text-xl font-bold font-mono text-zinc-900 tracking-tight">
            {currentData.views}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5 font-mono">冷启动强推池</div>
        </div>

        {/* Metric 3: Share Velocity */}
        <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-200/80">
          <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono mb-1">
            <span className="flex items-center gap-1">
              <Share2 className="w-3.5 h-3.5 text-amber-600" />
              <span>破圈分享流速</span>
            </span>
            <span className="text-amber-700 font-bold">高</span>
          </div>
          <div className="text-xl font-bold font-mono text-zinc-900 tracking-tight">
            {currentData.shareVelocity}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5 font-mono">二创引发系数 4.2x</div>
        </div>

        {/* Metric 4: Virality Index */}
        <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-200/80">
          <div className="flex items-center justify-between text-zinc-500 text-[10px] font-mono mb-1">
            <span className="flex items-center gap-1">
              <Flame className="w-3.5 h-3.5 text-rose-600" />
              <span>热度爆发指数</span>
            </span>
            <span className="text-rose-700 font-bold">S级</span>
          </div>
          <div className="text-xl font-bold font-mono text-zinc-900 tracking-tight">
            {currentData.viralityIndex}
          </div>
          <div className="text-[10px] text-zinc-500 mt-0.5 font-mono">推荐权重分 94.6</div>
        </div>
      </div>

      {/* Sparkline & Audience Insight Bar */}
      <div className="p-3 rounded-lg bg-zinc-50 border border-zinc-200/80 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Trend line */}
        <div className="w-full md:w-1/2">
          <div className="text-[10px] font-mono uppercase text-zinc-500 mb-1 flex items-center justify-between">
            <span>流速爬坡趋势 ({selectedTimeframe.toUpperCase()})</span>
            <span className="text-zinc-600 font-bold">
              {points.length > 0 ? `${points[points.length - 1].time}: ${points[points.length - 1].value}k` : ''}
            </span>
          </div>
          <div className="w-full h-14 bg-white rounded border border-zinc-200 p-1">
            <svg viewBox="0 0 300 65" className="w-full h-full overflow-visible">
              <polyline
                fill="none"
                stroke="#f59e0b"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={svgPoints}
              />
            </svg>
          </div>
        </div>

        {/* Retention Spikes & Sentiment */}
        <div className="w-full md:w-1/2 space-y-1.5 text-xs">
          <div className="flex items-center justify-between p-1.5 rounded bg-white border border-zinc-200 text-[11px]">
            <span className="text-zinc-500">留存停留峰值:</span>
            <span className="font-bold text-emerald-700 font-mono">{currentData.retentionSpikeBeat}</span>
          </div>
          <div className="flex items-center justify-between p-1.5 rounded bg-white border border-zinc-200 text-[11px]">
            <span className="text-zinc-500">读者舆情回响:</span>
            <span className="font-semibold text-zinc-800 truncate max-w-[200px]" title={currentData.audienceSentiment}>
              {currentData.audienceSentiment}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
