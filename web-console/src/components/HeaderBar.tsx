import React, { useState } from 'react';
import {
  ChevronDown,
  Share2,
  PanelRight,
  Check,
  Sparkles
} from 'lucide-react';
import { Episode } from '../types';

interface HeaderBarProps {
  activeEpisode: Episode;
  allEpisodes: Episode[];
  onSelectEpisode: (episode: Episode) => void;
  onToggleContextPanel?: () => void;
  contextPanelOpen?: boolean;
  onConnectWorkspace?: () => void;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({
  activeEpisode,
  allEpisodes,
  onSelectEpisode,
  onToggleContextPanel,
  contextPanelOpen = true,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [shared, setShared] = useState(false);

  const handleShare = () => {
    setShared(true);
    setTimeout(() => setShared(false), 1500);
  };

  const progressPercent = Math.round((activeEpisode.completedFrames / activeEpisode.totalFrames) * 100);

  return (
    <header className="h-[48px] px-4 border-b border-[#232830] bg-[#0B0D10] text-[#A7AFBA] flex items-center justify-between shrink-0 select-none z-20 text-xs">
      {/* 左侧：标题与下拉 */}
      <div className="flex items-center gap-2">
        <div className="relative">
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-1.5 font-medium text-[#F1F3F5] hover:text-white transition-colors px-2 py-1 rounded-[4px] hover:bg-[#171B21] border border-transparent hover:border-[#232830] cursor-pointer"
          >
            <span className="font-mono text-[#737D8A] font-semibold">{activeEpisode.code}</span>
            <span className="font-semibold text-[#F1F3F5]">{activeEpisode.title}</span>
            <ChevronDown className={`w-3.5 h-3.5 text-[#737D8A] transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {dropdownOpen && (
            <div className="absolute left-0 top-full mt-1 w-64 bg-[#13161B] border border-[#232830] rounded-[6px] shadow-2xl p-1 z-50 text-xs">
              <div className="px-2 py-1 text-[10px] font-mono text-[#737D8A] uppercase border-b border-[#232830] mb-1">
                切换当前剧目
              </div>
              {allEpisodes.map((ep) => (
                <button
                  key={ep.id}
                  type="button"
                  onClick={() => {
                    onSelectEpisode(ep);
                    setDropdownOpen(false);
                  }}
                  className={`w-full text-left px-2 py-1.5 rounded-[4px] transition-colors flex items-center justify-between cursor-pointer ${
                    ep.id === activeEpisode.id ? 'bg-[#171B21] text-[#F1F3F5] font-semibold border border-[#2D333D]' : 'text-[#A7AFBA] hover:text-[#F1F3F5] hover:bg-[#171B21]'
                  }`}
                >
                  <span className="truncate">{ep.code} {ep.title}</span>
                  <span className={`text-[10px] font-mono shrink-0 ml-2 ${ep.id === activeEpisode.id ? 'text-[#58A6FF]' : 'text-[#737D8A]'}`}>
                    {ep.completedFrames}/{ep.totalFrames} 帧
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        <span className="text-[11px] font-mono text-[#737D8A] flex items-center gap-1.5 ml-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[#58A6FF]" />
          <span>{activeEpisode.completedFrames}/{activeEpisode.totalFrames} 帧 ({progressPercent}%)</span>
        </span>
      </div>

      {/* 右侧：操作按钮（精密工控风格） */}
      <div className="flex items-center gap-2 text-[#A7AFBA]">
        <button
          type="button"
          onClick={handleShare}
          className="flex items-center gap-1.5 h-[28px] px-2.5 rounded-[4px] bg-[#13161B] border border-[#232830] hover:bg-[#171B21] hover:text-[#F1F3F5] hover:border-[#2D333D] transition-colors text-xs cursor-pointer font-mono"
          title="分享剧目链接"
        >
          {shared ? <Check className="w-3.5 h-3.5 text-[#3FB950]" /> : <Share2 className="w-3.5 h-3.5 text-[#737D8A]" />}
          <span>{shared ? '已复制' : '分享剧目'}</span>
        </button>

        {onToggleContextPanel && (
          <button
            type="button"
            onClick={onToggleContextPanel}
            className={`h-[28px] px-2.5 rounded-[4px] border transition-colors flex items-center gap-1.5 text-xs cursor-pointer font-mono ${
              contextPanelOpen
                ? 'bg-[#171B21] text-[#F1F3F5] font-semibold border-[#2D333D]'
                : 'bg-[#13161B] text-[#737D8A] border-[#232830] hover:text-[#F1F3F5] hover:bg-[#171B21]'
            }`}
            title="展开/收起右侧面板"
          >
            <PanelRight className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">右侧面板</span>
          </button>
        )}
      </div>
    </header>
  );
};
