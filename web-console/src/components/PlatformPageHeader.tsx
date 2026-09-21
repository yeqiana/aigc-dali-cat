import type { ReactNode } from 'react';

interface PlatformPageHeaderProps {
  section: string;
  title: string;
  description: string;
  actions?: ReactNode;
}

export function PlatformPageHeader({
  section,
  title,
  description,
  actions,
}: PlatformPageHeaderProps) {
  return (
    <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between pb-3 border-b border-[var(--border-subtle)]">
      <div className="min-w-0">
        <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Platform / {section}</div>
        <h1 className="mt-1 text-xl font-semibold">{title}</h1>
        <p className="mt-1 text-xs text-[var(--text-tertiary)]">{description}</p>
      </div>
      <div className="flex flex-wrap items-center gap-2 shrink-0">
        {actions}
        <a href="/platform" className="storyos-control h-8 px-2.5 inline-flex items-center text-[11px]">Platform Console</a>
        <a href="/" className="storyos-control h-8 px-2.5 inline-flex items-center text-[11px]">Production</a>
      </div>
    </header>
  );
}
