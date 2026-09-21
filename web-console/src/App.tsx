import React, { lazy, Suspense, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { HeaderBar } from './components/HeaderBar';
import { ProductionMonitorView } from './components/views/ProductionMonitorView';
import type { NavigationTab } from './types';

const PlatformDashboard = lazy(() => import('./pages/Dashboard'));
const AgentsConsole = lazy(() => import('./pages/Agents'));
const MemoryConsole = lazy(() => import('./pages/Memory'));
const ExecutionExplorer = lazy(() => import('./pages/ExecutionExplorer'));
const TraceExplorer = lazy(() => import('./pages/TraceExplorer'));
const RuntimeVisualization = lazy(() => import('./pages/RuntimeVisualization'));
const SeriesLibraryView = lazy(() => import('./components/views/SeriesLibraryView').then((module) => ({ default: module.SeriesLibraryView })));
const RuntimeLogsView = lazy(() => import('./components/views/RuntimeLogsView').then((module) => ({ default: module.RuntimeLogsView })));
const SettingsView = lazy(() => import('./components/views/SettingsView').then((module) => ({ default: module.SettingsView })));
const WorkbenchDemoView = lazy(() => import('./components/views/WorkbenchDemoView').then((module) => ({ default: module.WorkbenchDemoView })));

const BACKEND_ROUTE_CONTRACT = [
  { path: '/platform', Component: PlatformDashboard },
  { path: '/agents', Component: AgentsConsole },
  { path: '/memory', Component: MemoryConsole },
  { path: '/executions', Component: ExecutionExplorer },
  { path: '/traces', Component: TraceExplorer },
  { path: '/runtime', Component: RuntimeVisualization },
] as const;

function renderBackendRoute(): React.ReactNode | null {
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/';
  const route = BACKEND_ROUTE_CONTRACT.find((item) => item.path === pathname);
  if (!route) return null;
  const Component = route.Component;
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-tertiary)] flex items-center justify-center text-xs font-mono">
          Loading Platform Console…
        </div>
      }
    >
      <Component />
    </Suspense>
  );
}

function UnsupportedRoute() {
  return (
    <main className="storyos-shell min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] p-4 lg:p-6 flex items-center justify-center">
      <section className="storyos-surface w-full max-w-lg p-5">
        <div className="text-[11px] font-mono uppercase tracking-wider text-[var(--text-tertiary)]">StoryOS / Route</div>
        <h1 className="mt-1 text-lg font-semibold">Unsupported Console Route</h1>
        <p className="mt-2 text-xs leading-5 text-[var(--text-secondary)]">
          当前路径没有已接入的 StoryOS Console 能力。未配置的 Platform capability 不会回退成假页面。
        </p>
        <div className="mt-4 flex items-center gap-2">
          <a href="/" className="storyos-control h-8 px-3 inline-flex items-center text-xs">Production Console</a>
          <a href="/platform" className="h-8 px-3 rounded-[var(--radius-md)] bg-[var(--primary)] text-white inline-flex items-center text-xs font-medium">Platform Console</a>
        </div>
      </section>
    </main>
  );
}

function ConsoleSectionFallback({ label }: { label: string }) {
  return (
    <div className="storyos-surface min-h-24 flex items-center justify-center text-[11px] font-mono text-[var(--text-tertiary)]">
      Loading {label}…
    </div>
  );
}

function ProductionConsole() {
  const [currentTab, setCurrentTab] = useState<NavigationTab>('production_monitor');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (message: string) => {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 2500);
  };

  return (
    <div id="storyos-workspace-root" className="storyos-shell flex h-screen w-screen overflow-hidden font-sans antialiased select-text">
      <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />

      <div className="storyos-workspace flex-1 flex flex-col h-screen overflow-hidden relative min-w-0">
        <HeaderBar currentTab={currentTab} />

        <main className="flex-1 overflow-y-auto px-4 lg:px-5 py-4 relative bg-[var(--bg-app)]">
          {toastMessage && (
            <div className="fixed top-12 right-6 z-50 storyos-elevated text-[var(--text-primary)] px-3.5 py-1.5 text-xs font-medium flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--info)]" />
              <span>{toastMessage}</span>
            </div>
          )}

          {currentTab === 'production_monitor' && (
            <ProductionMonitorView onShowToast={showToast} />
          )}

          {currentTab === 'episodes' && (
            <Suspense fallback={<ConsoleSectionFallback label="Episodes" />}>
              <div className="max-w-5xl mx-auto">
                <SeriesLibraryView />
              </div>
            </Suspense>
          )}

          {currentTab === 'logs' && (
            <Suspense fallback={<ConsoleSectionFallback label="Runtime Logs" />}>
              <div className="max-w-5xl mx-auto">
                <RuntimeLogsView />
              </div>
            </Suspense>
          )}

          {currentTab === 'settings' && (
            <Suspense fallback={<ConsoleSectionFallback label="Settings" />}>
              <div className="max-w-4xl mx-auto">
                <SettingsView />
              </div>
            </Suspense>
          )}

          {currentTab === 'workbench' && (
            <Suspense fallback={<ConsoleSectionFallback label="Workbench Demo" />}>
              <WorkbenchDemoView onShowToast={showToast} />
            </Suspense>
          )}
        </main>
      </div>
    </div>
  );
}

export default function App() {
  const backendPage = renderBackendRoute();
  if (backendPage) return backendPage;
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/';
  return pathname === '/' ? <ProductionConsole /> : <UnsupportedRoute />;
}
