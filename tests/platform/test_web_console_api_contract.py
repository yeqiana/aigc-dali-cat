from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web-console"


def test_web_console_uses_one_platform_api_base_url_contract():
    env = (WEB / ".env.example").read_text(encoding="utf-8")
    client = (WEB / "src/api/client.ts").read_text(encoding="utf-8")
    streaming = (WEB / "src/api/streaming.ts").read_text(encoding="utf-8")

    assert "VITE_PLATFORM_API_URL=" in env
    assert "VITE_API_BASE_URL" not in env
    assert "VITE_RUNTIME_STREAM_URL" not in env
    assert "import.meta.env.VITE_PLATFORM_API_URL" in client
    assert "export function platformApiUrl" in client
    assert "platformApiUrl(`/api/v1/runtime/${executionId}/stream`)" in streaming


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
    assert "apiGet<Health>('/healthz')" in dashboard


def test_api_get_is_a_real_export_for_execution_and_monitoring_clients():
    client = (WEB / "src/api/client.ts").read_text(encoding="utf-8")
    execution = (WEB / "src/api/execution.ts").read_text(encoding="utf-8")
    monitoring = (WEB / "src/api/monitoring.ts").read_text(encoding="utf-8")

    assert "export const apiGet" in client
    assert "import { apiGet } from './client';" in execution
    assert "import { apiGet } from './client';" in monitoring
