import { useState } from 'react';
import { AlertTriangle, PlugZap, RefreshCw } from 'lucide-react';
import { pluginApi } from '../api/plugin';
import type { PluginDefinition } from '../types/plugin';

export default function PluginConsole() {
  const [plugins, setPlugins] = useState<PluginDefinition[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadPlugins() {
    if (loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await pluginApi.list();
      setPlugins(Array.isArray(result) ? result : []);
      setLoaded(true);
    } catch (cause) {
      setPlugins([]);
      setLoaded(true);
      setError(cause instanceof Error ? cause.message : 'Plugin Registry 加载失败');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6">
      <div className="max-w-5xl mx-auto space-y-4">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between pb-3 border-b border-[var(--border-subtle)]">
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">Platform / Extensions</div>
            <h1 className="mt-1 text-xl font-semibold">Plugin Console</h1>
            <p className="mt-1 text-xs text-[var(--text-tertiary)]">查看已注册 Plugin Definition；本页不创建不存在的 Marketplace 状态。</p>
          </div>
          <button type="button" onClick={loadPlugins} disabled={loading} className="h-8 px-3 rounded-[var(--radius-md)] bg-[var(--primary)] text-white text-xs font-medium flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed">
            <RefreshCw className={loading ? 'w-3.5 h-3.5 animate-spin' : 'w-3.5 h-3.5'} />
            <span>{loading ? '加载中…' : loaded ? '刷新 Registry' : '加载 Registry'}</span>
          </button>
        </header>
        {error && <div className="storyos-surface px-3 py-2 flex items-start gap-2 text-xs text-[var(--danger)] border-[var(--danger)]"><AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /><span>{error}</span></div>}
        <section className="storyos-surface overflow-hidden">
          <header className="h-10 px-3 border-b border-[var(--border-subtle)] flex items-center justify-between">
            <div className="flex items-center gap-2"><PlugZap className="w-3.5 h-3.5 text-[var(--info)]" /><h2 className="text-xs font-semibold">Plugin Registry</h2></div>
            <span className="text-[10px] font-mono text-[var(--text-tertiary)]">{loaded ? String(plugins.length) + ' PLUGINS' : 'NOT LOADED'}</span>
          </header>
          {plugins.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-xs">
                <thead className="h-9 border-b border-[var(--border-subtle)] text-[var(--text-tertiary)] font-medium"><tr><th className="px-3 text-left">Plugin</th><th className="px-3 text-left">Type</th><th className="px-3 text-left">Version</th><th className="px-3 text-left">Status</th><th className="px-3 text-left">Plugin ID</th></tr></thead>
                <tbody>
                  {plugins.map((plugin) => (
                    <tr key={plugin.pluginId} className="h-11 border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
                      <td className="px-3 font-medium text-[var(--text-primary)]">{plugin.name}</td>
                      <td className="px-3 text-[var(--text-secondary)]">{plugin.type}</td>
                      <td className="px-3 font-mono text-[var(--text-secondary)]">{plugin.version || '-'}</td>
                      <td className="px-3 font-mono text-[var(--text-primary)]">{plugin.status}</td>
                      <td className="px-3 font-mono text-[var(--text-tertiary)]">{plugin.pluginId}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <div className="px-3 py-10 text-center text-xs text-[var(--text-tertiary)]">{loaded ? 'Registry 当前没有返回 Plugin Definition。' : '加载 Registry 后显示真实 Plugin Definition。'}</div>}
        </section>
      </div>
    </main>
  );
}
