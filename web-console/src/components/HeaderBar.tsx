import React, { useState } from 'react';
import { Check, Share2 } from 'lucide-react';
import type { NavigationTab } from '../types';

interface HeaderBarProps {
  currentTab: NavigationTab;
}

const SECTION_META: Record<NavigationTab, { title: string; badge: string; tone: 'success' | 'warning' | 'neutral' }> = {
  production_monitor: { title: 'Production Monitor', badge: 'MYSQL AUTHORITY · READ ONLY', tone: 'success' },
  episodes: { title: 'Episode Index', badge: 'MYSQL AUTHORITY · READ ONLY', tone: 'success' },
  logs: { title: 'Runtime Logs', badge: 'CAPABILITY NOT CONNECTED', tone: 'warning' },
  settings: { title: 'Settings', badge: 'LOCAL CONFIG VIEW', tone: 'neutral' },
  workbench: { title: 'Workbench Demo', badge: 'LOCAL DEMO · NOT AUTHORITY', tone: 'warning' },
};

export const HeaderBar: React.FC<HeaderBarProps> = ({ currentTab }) => {
  const [shared, setShared] = useState(false);
  const meta = SECTION_META[currentTab];

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setShared(true);
      window.setTimeout(() => setShared(false), 1500);
    } catch {
      setShared(false);
    }
  };

  const dotClass = meta.tone === 'success'
    ? 'bg-[var(--success)]'
    : meta.tone === 'warning'
      ? 'bg-[var(--warning)]'
      : 'bg-[var(--text-tertiary)]';

  return (
    <header className="h-[var(--header-height)] px-4 border-b border-[var(--border-normal)] bg-[var(--bg-workspace)] text-[var(--text-secondary)] flex items-center justify-between shrink-0 select-none z-20 text-xs">
      <div className="flex items-center gap-2 min-w-0">
        <span className="font-semibold text-[var(--text-primary)]">{meta.title}</span>
        <span className={`storyos-status storyos-status--${meta.tone} font-mono`}>
          <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} />
          {meta.badge}
        </span>
      </div>
      <button type="button" onClick={handleShare} aria-label="复制当前页面链接" className="storyos-control h-8 px-2.5 flex items-center gap-1.5 text-xs font-mono">
        {shared ? <Check className="w-3.5 h-3.5 text-[var(--success)]" /> : <Share2 className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />}
        <span>{shared ? '已复制' : '分享'}</span>
      </button>
    </header>
  );
};
