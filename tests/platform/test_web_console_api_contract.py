from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web-console"


def test_web_console_uses_one_platform_api_base_url_contract():
    env = (WEB / ".env.example").read_text(encoding="utf-8")
    client = (WEB / "src/api/client.ts").read_text(encoding="utf-8")

    assert "VITE_PLATFORM_API_URL=" in env
    assert "VITE_API_BASE_URL" not in env
    assert "VITE_RUNTIME_STREAM_URL" not in env
    assert "import.meta.env.VITE_PLATFORM_API_URL" in client
    assert "export function platformApiUrl" in client
    assert not (WEB / "src/api/streaming.ts").exists()


def test_main_console_routes_use_real_backend_backed_pages_only():
    app = (WEB / "src/App.tsx").read_text(encoding="utf-8")
    dashboard = (WEB / "src/pages/Dashboard.tsx").read_text(encoding="utf-8")
    assert "lazy(() => import('./pages/Dashboard'))" in app
    assert "lazy(() => import('./pages/Agents'))" in app
    assert "lazy(() => import('./pages/Memory'))" in app
    assert "lazy(() => import('./pages/ExecutionExplorer'))" in app
    assert "lazy(() => import('./pages/TraceExplorer'))" in app
    assert "lazy(() => import('./pages/RuntimeVisualization'))" in app
    assert "{ path: '/platform', Component: PlatformDashboard }" in app
    assert "{ path: '/agents', Component: AgentsConsole }" in app
    assert "{ path: '/memory', Component: MemoryConsole }" in app
    assert "{ path: '/executions', Component: ExecutionExplorer }" in app
    assert "{ path: '/traces', Component: TraceExplorer }" in app
    assert "{ path: '/runtime', Component: RuntimeVisualization }" in app
    assert "/projects" not in app
    assert "/plugins" not in app
    assert '/workflows' not in app
    assert "Unsupported Console Route" in app
    assert "pathname === '/' ? <ProductionConsole /> : <UnsupportedRoute />" in app
    assert "apiGet<Health>('/healthz')" in dashboard


def test_execution_and_trace_deep_links_auto_query():
    execution_page = (WEB / "src/pages/ExecutionExplorer.tsx").read_text(encoding="utf-8")
    trace_page = (WEB / "src/pages/TraceExplorer.tsx").read_text(encoding="utf-8")

    assert "URLSearchParams(window.location.search).get('execution')" in execution_page
    assert "URLSearchParams(window.location.search).get('trace')" in trace_page
    assert "if (id.trim()) void load();" in execution_page
    assert "if (id.trim()) void load();" in trace_page


def test_production_monitor_uses_real_runtime_projection_not_monitor_mock():
    monitor = (WEB / "src/components/views/ProductionMonitorView.tsx").read_text(encoding="utf-8")
    app = (WEB / "src/App.tsx").read_text(encoding="utf-8")

    assert "runtimeApi.listEpisodeStatuses" in monitor
    assert "runtimeApi.getEpisodeStatus" in monitor
    assert "MYSQL AUTHORITY · READ ONLY" in monitor
    assert "mockMonitorData" not in monitor
    assert "MOCK_STORY_RUNS" not in monitor
    assert "handleTogglePause" not in monitor
    assert "handleRetryRun" not in monitor
    assert "<ProductionMonitorView" in app


def test_production_index_and_logs_do_not_fall_back_to_demo_data():
    series = (WEB / "src/components/views/SeriesLibraryView.tsx").read_text(encoding="utf-8")
    logs = (WEB / "src/components/views/RuntimeLogsView.tsx").read_text(encoding="utf-8")
    header = (WEB / "src/components/HeaderBar.tsx").read_text(encoding="utf-8")
    demo = (WEB / "src/workbenchDemoData.ts").read_text(encoding="utf-8")
    app = (WEB / "src/App.tsx").read_text(encoding="utf-8")
    workbench = (WEB / "src/components/views/WorkbenchDemoView.tsx").read_text(encoding="utf-8")

    assert "runtimeApi.listEpisodeStatuses" in series
    assert "MYSQL AUTHORITY" in series
    assert "CAPABILITY NOT CONNECTED" in logs
    assert "SYSTEM_RUNTIME_LOGS" not in logs
    assert "LOCAL DEMO · NOT AUTHORITY" in header
    assert "MYSQL AUTHORITY · READ ONLY" in header
    assert "export const DEMO_EPISODES" in demo
    assert "SYSTEM_RUNTIME_LOGS" not in demo
    assert "workbenchDemoData" not in app
    assert "DEMO_EPISODES" not in app
    assert "WorkbenchDemoView" in app
    assert "workbenchDemoData" in workbench


def test_runtime_console_uses_only_supported_execution_and_trace_endpoints():
    client = (WEB / "src/api/client.ts").read_text(encoding="utf-8")
    execution = (WEB / "src/api/execution.ts").read_text(encoding="utf-8")
    runtime = (WEB / "src/api/runtime.ts").read_text(encoding="utf-8")
    runtime_page = (WEB / "src/pages/RuntimeVisualization.tsx").read_text(encoding="utf-8")

    assert "export const apiGet" in client
    assert "import { apiGet } from './client';" in execution
    assert "/api/v1/executions/${id}" in runtime
    assert "/api/v1/traces/${traceId}" in runtime
    assert "getTrace(nextExecution.trace_id)" in runtime_page
    assert "/api/v1/runtime/statuses?limit=${limit}&offset=${offset}" in runtime
    assert "listEpisodeStatuses(pageSize, offset)" in runtime_page
    assert "loadEpisodeStatuses(episodeStatusOffset + pageSize)" in runtime_page
    assert "Math.max(0, episodeStatusOffset - pageSize)" in runtime_page
    assert not (WEB / "src/api/monitoring.ts").exists()
    assert not (WEB / "src/api/workflow.ts").exists()
    assert not (WEB / "src/api/permission.ts").exists()
