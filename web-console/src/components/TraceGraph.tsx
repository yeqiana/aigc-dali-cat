type TraceNode = {
  id: string;
  type: string;
};

export default function TraceGraph({ nodes = [] }: { nodes?: TraceNode[] }) {
  return (
    <section className="storyos-surface overflow-hidden">
      <header className="h-9 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
        <h3 className="text-[12px] font-semibold text-[var(--text-primary)]">Trace / Event</h3>
        <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{nodes.length} NODES</span>
      </header>
      {nodes.length === 0 ? (
        <div className="px-3 py-8 text-center text-[11px] text-[var(--text-tertiary)]">
          暂无 Trace 证据。
        </div>
      ) : (
        <div className="divide-y divide-[var(--border-subtle)]">
          {nodes.map((node, index) => (
            <div key={node.id} className="min-h-10 px-3 py-2 flex items-center gap-3 hover:bg-[var(--bg-hover)]">
              <span className="w-5 text-right text-[10px] font-mono text-[var(--text-disabled)]">
                {String(index + 1).padStart(2, '0')}
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--info)] shrink-0" />
              <span className="text-[11px] font-medium text-[var(--text-secondary)] min-w-20">{node.type}</span>
              <code className="min-w-0 truncate text-[11px] text-[var(--text-tertiary)]">{node.id}</code>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
