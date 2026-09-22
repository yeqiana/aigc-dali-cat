from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web-console"
SRC = WEB / "src"


def read(relative: str) -> str:
    return (WEB / relative).read_text(encoding="utf-8")


def test_web_console_uses_one_platform_api_base_url_contract():
    env = read(".env.example")
    app = read("src/config/app.js")
    http = read("src/api/http.js")

    assert "VITE_PLATFORM_API_URL=" in env
    assert "VITE_API_BASE_URL" not in env
    assert "VITE_RUNTIME_STREAM_URL" not in env
    assert "VITE_PLATFORM_API_URL" in app
    assert "baseURL: appConfig.platformApiBaseUrl" in http
    assert not (SRC / "api/streaming.js").exists()


def test_web_console_dev_and_preview_proxy_platform_api():
    config = read("vite.config.ts")
    assert "const platformProxy" in config
    assert "'http://127.0.0.1:8080'" in config
    assert config.count("proxy: platformProxy") == 2
    assert "preview:" in config


def test_main_console_routes_use_real_backend_backed_pages_only():
    router = read("src/router/index.js")
    api = read("src/api/platform.js")
    assert "ProductionMonitor" in router
    assert "Episodes" in router
    assert "RuntimeLogs" in router
    assert "PlatformConsole" in router
    assert "ExecutionExplorer" in router
    assert "TraceExplorer" in router
    assert "MemoryExplorer" in router
    assert "AgentsExplorer" in router
    assert "runtimeStatuses(limit = 20, offset = 0)" in api
    assert "/api/v1/runtime/statuses" in api
    assert "/api/v1/executions/${encodeURIComponent(id)}" in api
    assert "/api/v1/traces?" in api


def test_production_and_episode_pages_use_real_runtime_projection():
    monitor = read("src/views/storyos/ProductionMonitor.vue")
    episodes = read("src/views/storyos/Episodes.vue")
    assert "platformApi.runtimeStatuses" in monitor
    assert "platformApi.runtimeStatuses" in episodes
    assert "normalizeRuntimeRow" in monitor
    assert "normalizeRuntimeRow" in episodes
    assert "mock/episodes" not in monitor
    assert "mock/episodes" not in episodes
    assert "演示数据" not in monitor
    assert "演示数据" not in episodes
    assert "progressStages" in monitor
    assert "进度节点" in monitor
    assert not (SRC / "views/storyos/ProgressNodes.vue").exists()


def test_runtime_logs_use_real_events_and_no_demo_fallback():
    logs = read("src/views/storyos/RuntimeLogs.vue")
    assert "platformApi.events" in logs
    assert "暂无事件记录" in logs
    assert "示例" not in logs


def test_runtime_console_uses_only_supported_execution_and_trace_endpoints():
    api = read("src/api/platform.js")
    assert "/api/v1/executions/${encodeURIComponent(id)}" in api
    assert "/api/v1/traces/${encodeURIComponent(id)}" in api
    assert "/api/v1/runtime/statuses?limit=${limit}&offset=${offset}" in api
    assert "/api/v1/runtime/events?limit=${limit}&offset=${offset}" in api
    assert "encodeURIComponent(episodeId)" in api
    assert not (SRC / "api/monitoring.js").exists()
    assert not (SRC / "api/workflow.js").exists()
    assert not (SRC / "api/permission.js").exists()


def test_shared_page_components_and_single_settings_entry():
    home = read("src/layout/Home.vue")
    sidebar = read("src/components/Sidebar.vue")
    header = read("src/components/HeaderBar.vue")
    assert "PageTabs" not in home
    assert "command=\"settings\"" in sidebar
    assert "to=\"/settings\"" not in sidebar
    assert "header-actions" not in header
    assert (SRC / "components/PageHeading.vue").exists()
    assert (SRC / "components/PanelHeader.vue").exists()


def test_data_pages_use_shared_native_data_table():
    table = read("src/components/DataTable.vue")
    assert "class=\"data-table\"" in table
    assert "v-for=\"(row, rowIndex) in rows\"" in table
    for relative in (
        "src/views/storyos/ProductionMonitor.vue",
        "src/views/storyos/Episodes.vue",
        "src/views/storyos/RuntimeLogs.vue",
        "src/views/platform/RuntimeExplorer.vue",
        "src/views/platform/TraceExplorer.vue",
    ):
        page = read(relative)
        assert "<DataTable" in page
        assert "<el-table" not in page


def test_list_pages_expose_shared_filter_bar():
    bar = read("src/components/FilterBar.vue")
    assert 'class="filter-bar"' in bar
    filters = read("src/utils/filter.js")
    assert "export function distinctOptions" in filters
    assert "export function keywordMatch" in filters
    for relative in (
        "src/views/storyos/ProductionMonitor.vue",
        "src/views/storyos/Episodes.vue",
        "src/views/storyos/RuntimeLogs.vue",
        "src/views/platform/RuntimeExplorer.vue",
        "src/views/platform/TraceExplorer.vue",
        "src/views/platform/MemoryExplorer.vue",
    ):
        page = read(relative)
        assert "<FilterBar" in page
        assert "<el-select" in page
        assert ":rows=\"filteredRows\"" in page
    for relative in ("src/views/platform/ExecutionExplorer.vue", "src/views/storyos/Workbench.vue"):
        page = read(relative)
        assert "<FilterBar" not in page
