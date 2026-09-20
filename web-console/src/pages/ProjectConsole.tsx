import { useEffect, useState } from 'react';
import { AlertTriangle, Boxes } from 'lucide-react';
import { projectApi } from '../api/project';
import type { ProjectContext } from '../types/project';

export default function ProjectConsole() {
  const [projects, setProjects] = useState<ProjectContext[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    projectApi.list()
      .then((rows) => setProjects(Array.isArray(rows) ? rows : []))
      .catch((cause) => setError(cause instanceof Error ? cause.message : 'Project 列表加载失败'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6">
      <div className="max-w-5xl mx-auto space-y-4">
        <header className="pb-3 border-b border-[var(--border-subtle)]">
          <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Platform / Projects</div>
          <h1 className="mt-1 text-xl font-semibold">Project Console</h1>
          <p className="mt-1 text-xs text-[var(--text-tertiary)]">只读查看 Platform Project Context。</p>
        </header>
        {error && <div className="storyos-surface px-3 py-2 flex items-start gap-2 text-xs text-[var(--danger)] border-[var(--danger)]"><AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /><span>{error}</span></div>}
        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <div className="flex items-center gap-2"><Boxes className="w-3.5 h-3.5 text-[var(--info)]" /><h2 className="text-xs font-semibold">Projects</h2></div>
            <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{loading ? 'LOADING' : String(projects.length) + ' PROJECTS'}</span>
          </header>
          {projects.length > 0 ? (
            <div className="overflow-x-auto"><table className="w-full min-w-[620px] text-xs"><thead className="h-9 border-b border-[var(--border-subtle)] text-[var(--text-tertiary)]"><tr><th className="px-3 text-left">Project</th><th className="px-3 text-left">Status</th><th className="px-3 text-left">Project ID</th></tr></thead><tbody>{projects.map((project) => <tr key={project.projectId} className="h-11 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]"><td className="px-3 font-medium text-[var(--text-primary)]">{project.projectName}</td><td className="px-3 font-mono text-[var(--text-secondary)]">{project.status}</td><td className="px-3 font-mono text-[var(--text-tertiary)]">{project.projectId}</td></tr>)}</tbody></table></div>
          ) : <div className="px-3 py-10 text-center text-xs text-[var(--text-tertiary)]">{loading ? '正在加载 Project Context…' : '没有可用 Project Context。'}</div>}
        </section>
      </div>
    </main>
  );
}
