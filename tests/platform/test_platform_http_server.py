from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
import threading
import urllib.error
import urllib.request

from platform.agent.application import AgentApplicationService
from platform.agent.runtime import AgentContext, AgentExecutionPlan, AgentRuntime, SkillExecutionStep
from platform.api.contracts import CreateAgentRequest
from platform.api.controllers import AgentApiController, ExecutionApiController, RuntimeEventApiController, RuntimeStatusApiController, TraceApiController
from platform.api.default_app import build_default_controllers
from platform.api.http_server import PlatformApiDispatcher, build_http_server
from platform.operations.experience_store import ExperienceStore, RuntimeExperience
from platform.operations.runtime_event_service import RuntimeEventApiService
from platform.operations.runtime_status_service import RuntimeStatusApiService


class FakeAgentService:
    def __init__(self) -> None:
        self.agents = {"agent-1": {"id": "agent-1", "status": "ACTIVE"}}

    def create_agent(self, request):
        row = {
            "id": request.agent_code,
            "agent_code": request.agent_code,
            "agent_name": request.agent_name,
            "agent_type": request.agent_type,
        }
        self.agents[request.agent_code] = row
        return row

    def get_agent(self, agent_id):
        return self.agents.get(agent_id)

    def list_agent_executions(self, agent_id):
        return [{"id": "exec-1", "agent_id": agent_id}]

    def get_execution(self, execution_id):
        return {"id": execution_id, "status": "SUCCESS"} if execution_id == "exec-1" else None

    def get_trace(self, trace_id):
        return {"id": trace_id, "status": "SUCCESS"} if trace_id == "trace-1" else None


def _controllers():
    service = FakeAgentService()
    return {
        "AgentApiController": AgentApiController(service),
        "ExecutionApiController": ExecutionApiController(service),
        "TraceApiController": TraceApiController(service),
    }


def test_dispatcher_maps_template_ids_to_controller_parameter_names():
    dispatcher = PlatformApiDispatcher(_controllers())
    status, payload = dispatcher.dispatch("GET", "/api/v1/agents/agent-1")
    assert status == 200
    assert payload["code"] == "OK"
    assert payload["data"]["id"] == "agent-1"

    status, payload = dispatcher.dispatch("GET", "/api/v1/executions/exec-1")
    assert status == 200
    assert payload["data"]["status"] == "SUCCESS"


def test_dispatcher_builds_request_dto_for_post_body():
    dispatcher = PlatformApiDispatcher(_controllers())
    status, payload = dispatcher.dispatch(
        "POST",
        "/api/v1/agents",
        {"agent_code": "story", "agent_name": "Story Agent", "agent_type": "STORY"},
    )
    assert status == 200
    assert payload["data"]["agent_code"] == "story"


def test_missing_controller_is_explicit_capability_failure_not_fake_success():
    dispatcher = PlatformApiDispatcher({})
    status, payload = dispatcher.dispatch("GET", "/api/v1/skills")
    assert status == 503
    assert payload["code"] == "CAPABILITY_NOT_CONFIGURED"


def test_real_loopback_http_server_serves_platform_api_envelope_and_cors():
    server = build_http_server(_controllers(), host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        request = urllib.request.Request(f"http://{host}:{port}/api/v1/agents/agent-1")
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert response.headers["Access-Control-Allow-Origin"] == "*"
            assert payload["code"] == "OK"
            assert payload["data"]["id"] == "agent-1"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_real_loopback_http_server_serializes_runtime_trace_datetimes():
    runtime = AgentRuntime()
    runtime.skill_adapter.register("trace.probe", lambda input_data, context, invoke_tool: {"ok": True})
    service = AgentApplicationService(runtime)
    AgentApiController(service).create_agent(
        CreateAgentRequest(agent_code="trace-agent", agent_name="Trace Agent", agent_type="TEST")
    )
    executed = service.execute_plan(
        AgentExecutionPlan(
            agent_code="trace-agent",
            agent_version="v1",
            context=AgentContext(task_id="trace-http-probe"),
            steps=(SkillExecutionStep(skill_code="trace.probe"),),
        )
    )

    server = build_http_server(
        {
            "ExecutionApiController": ExecutionApiController(service),
            "TraceApiController": TraceApiController(service),
        },
        host="127.0.0.1",
        port=0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urllib.request.urlopen(
            f"http://{host}:{port}/api/v1/traces/{executed['trace_id']}",
            timeout=5,
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert response.status == 200
            assert payload["data"]["trace_id"] == executed["trace_id"]
            assert payload["data"]["status"] == "SUCCESS"
            assert payload["data"]["started_at"].endswith("+00:00")
            assert payload["data"]["ended_at"].endswith("+00:00")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_default_composition_exposes_real_agent_and_memory_services():
    store = ExperienceStore()
    store.append(RuntimeExperience(
        experience_id="mem-1",
        runtime="WORK",
        agent="story-agent",
        workflow="AI_STORY_PRODUCTION",
        outcome="SUCCESS",
        pattern="high_retention_episode",
        evidence_ref="reports/example.json",
        confidence=0.95,
    ))
    dispatcher = PlatformApiDispatcher(build_default_controllers(experience_store=store))

    status, payload = dispatcher.dispatch(
        "POST",
        "/api/v1/agents",
        {"agent_code": "story-agent", "agent_name": "Story Agent", "agent_type": "STORY"},
    )
    assert status == 200
    assert payload["data"]["agent_code"] == "story-agent"

    status, payload = dispatcher.dispatch("POST", "/api/v1/memory/search", {"query": "retention"})
    assert status == 200
    assert payload["data"][0]["id"] == "mem-1"
    assert payload["data"][0]["memory_type"] == "runtime_experience"


def test_runtime_status_query_uses_safe_episode_relative_path_and_hides_host_path():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        episode = root / "episodes" / "series" / "episode"
        (episode / "meta").mkdir(parents=True)
        (episode / "meta/episode-state.json").write_text('{"current_state":"STORYBOARD_LOCKED"}', encoding="utf-8")
        service = RuntimeStatusApiService(
            repo_root=root,
            projector=lambda ep: {
                "production_stage": "STORYBOARD_LOCKED",
                "execution_status": "RUNNING",
                "episode_path": str(ep),
            },
        )
        dispatcher = PlatformApiDispatcher({"RuntimeStatusApiController": RuntimeStatusApiController(service)})

        status, payload = dispatcher.dispatch("GET", "/api/v1/runtime/status?episode=series%2Fepisode")

        assert status == 200
        assert payload["data"]["episode_ref"] == "series/episode"
        assert payload["data"]["production_stage"] == "STORYBOARD_LOCKED"
        assert "episode_path" not in payload["data"]


def test_runtime_status_rejects_episode_path_escape():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "episodes").mkdir()
        service = RuntimeStatusApiService(repo_root=root, projector=lambda ep: {})
        dispatcher = PlatformApiDispatcher({"RuntimeStatusApiController": RuntimeStatusApiController(service)})

        status, payload = dispatcher.dispatch("GET", "/api/v1/runtime/status?episode=..%2Fsecret")

        assert status == 400
        assert payload["code"] == "INVALID_REQUEST"


def test_runtime_status_allows_mysql_registered_episode_without_legacy_state_file():
    class SummaryRepository:
        def list_active_summaries(self, *, limit=50, offset=0):
            return []

        def get_by_namespace(self, episode_namespace):
            if episode_namespace == "尸解仙":
                return {
                    "episode_id": "EPU_1",
                    "episode_namespace": "尸解仙",
                    "disposition": "ACTIVE",
                }
            return None

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        episode = root / "episodes" / "尸解仙"
        (episode / "meta").mkdir(parents=True)
        service = RuntimeStatusApiService(
            repo_root=root,
            projector=lambda ep: {
                "production_stage": "IDEA_LOCKED",
                "execution_status": "IDLE",
                "episode_path": str(ep),
            },
            summary_repository=SummaryRepository(),
        )
        dispatcher = PlatformApiDispatcher({"RuntimeStatusApiController": RuntimeStatusApiController(service)})

        status, payload = dispatcher.dispatch("GET", "/api/v1/runtime/status?episode=%E5%B0%B8%E8%A7%A3%E4%BB%99")

        assert status == 200
        assert payload["data"]["episode_ref"] == "尸解仙"
        assert payload["data"]["production_stage"] == "IDEA_LOCKED"
        assert "episode_path" not in payload["data"]


def test_runtime_status_rejects_unregistered_directory_without_legacy_state_file():
    class SummaryRepository:
        def list_active_summaries(self, *, limit=50, offset=0):
            return []

        def get_by_namespace(self, episode_namespace):
            return None

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "episodes" / "12_千寻").mkdir(parents=True)
        service = RuntimeStatusApiService(
            repo_root=root,
            projector=lambda _ep: {"execution_status": "IDLE"},
            summary_repository=SummaryRepository(),
        )
        dispatcher = PlatformApiDispatcher({"RuntimeStatusApiController": RuntimeStatusApiController(service)})

        status, payload = dispatcher.dispatch("GET", "/api/v1/runtime/status?episode=12_%E5%8D%83%E5%AF%BB")

        assert status == 404
        assert payload["code"] == "EPISODE_NOT_FOUND"


def test_runtime_status_list_is_bounded_excludes_control_trees_and_isolates_bad_episode():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for ref in ("01_series/01_alpha", "01_series/02_beta", "02_series/01_bad"):
            meta = root / "episodes" / ref / "meta"
            meta.mkdir(parents=True)
            (meta / "episode-state.json").write_text('{"current_state":"STORYBOARD_LOCKED"}', encoding="utf-8")
        control = root / "episodes" / "_system" / "fake" / "meta"
        control.mkdir(parents=True)
        (control / "episode-state.json").write_text('{"current_state":"BROKEN"}', encoding="utf-8")

        def projector(ep: Path):
            if ep.name == "01_bad":
                raise RuntimeError(f"do not leak this host path: {ep}")
            return {
                "episode_path": str(ep),
                "production_stage": "STORYBOARD_LOCKED",
                "execution_status": "RUNNING",
                "current_action": "VISUAL_LOCK",
                "needs_user": False,
                "heartbeat": {"health": "HEALTHY"},
                "image_progress": {"generated_frames": 1},
                "review_progress": {"visual_lock_accepted": 1},
            }

        service = RuntimeStatusApiService(repo_root=root, projector=projector)
        dispatcher = PlatformApiDispatcher({"RuntimeStatusApiController": RuntimeStatusApiController(service)})

        status, first = dispatcher.dispatch("GET", "/api/v1/runtime/statuses?limit=2&offset=0")
        assert status == 200
        assert first["data"]["count"] == 2
        assert first["data"]["has_more"] is True
        assert [row["episode_ref"] for row in first["data"]["items"]] == [
            "01_series/01_alpha", "01_series/02_beta",
        ]
        assert all("episode_path" not in row for row in first["data"]["items"])

        status, second = dispatcher.dispatch("GET", "/api/v1/runtime/statuses?limit=2&offset=2")
        assert status == 200
        assert second["data"]["count"] == 1
        assert second["data"]["has_more"] is False
        assert second["data"]["items"][0] == {
            "episode_ref": "02_series/01_bad",
            "execution_status": "ERROR",
            "error": "STATUS_PROJECTION_FAILED",
        }
        assert second["data"]["errors"] == [{
            "episode_ref": "02_series/01_bad", "code": "STATUS_PROJECTION_FAILED"
        }]
        assert str(root) not in json.dumps(second, ensure_ascii=False)


def test_runtime_status_list_validates_paging_query():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "episodes").mkdir()
        service = RuntimeStatusApiService(repo_root=root, projector=lambda ep: {})
        dispatcher = PlatformApiDispatcher({"RuntimeStatusApiController": RuntimeStatusApiController(service)})

        for query in ("limit=0", "limit=101", "limit=nope", "offset=-1", "offset=nope"):
            status, payload = dispatcher.dispatch("GET", f"/api/v1/runtime/statuses?{query}")
            assert status == 400
            assert payload["code"] == "INVALID_REQUEST"


def test_runtime_status_list_uses_injected_summary_repository_without_full_projector():
    class SummaryRepository:
        def __init__(self):
            self.calls = []

        def list_active_summaries(self, *, limit=50, offset=0):
            self.calls.append((limit, offset))
            return [
                {
                    "episode_id": "EPU_1",
                    "business_episode_id": "09-05",
                    "episode_namespace": "09_series/05_wedding",
                    "title": "婚礼前夜",
                    "current_state": "PUBLISH_READY",
                    "state_source": "MYSQL_REDIS_CUTOVER",
                    "state_update_time": "2026-09-20T03:30:24",
                },
                {
                    "episode_id": "EPU_2",
                    "business_episode_id": "09-04",
                    "episode_namespace": "09_series/04_bottle",
                    "title": "瓶中世界",
                    "current_state": "PUBLISH_READY",
                    "state_source": "MYSQL_REDIS_CUTOVER",
                    "state_update_time": "2026-09-20T03:30:23",
                },
            ]

    summaries = SummaryRepository()
    service = RuntimeStatusApiService(
        projector=lambda _ep: (_ for _ in ()).throw(AssertionError("full projector must not run")),
        summary_repository=summaries,
    )

    page = service.list_episode_statuses(limit=1, offset=0)

    assert summaries.calls == [(2, 0)]
    assert page["has_more"] is True
    assert page["total"] is None
    assert page["stage_counts"] == {}
    row = page["items"][0]
    assert row["projection_level"] == "summary"
    assert row["episode_id"] == "EPU_1"
    assert row["title"] == "婚礼前夜"
    assert row["episode_ref"] == "09_series/05_wedding"
    assert row["production_stage"] == "PUBLISH_READY"
    assert row["state_source"] == "MYSQL_REDIS_CUTOVER"
    assert "execution_status" not in row


def test_default_composition_exposes_runtime_status_controller():
    assert "RuntimeStatusApiController" in build_default_controllers()
    assert "RuntimeEventApiController" in build_default_controllers()


def test_runtime_events_api_is_bounded_read_only_projection():
    class EventRepository:
        def __init__(self):
            self.calls = []

        def list_recent(self, *, limit=50, offset=0):
            self.calls.append((limit, offset))
            return [
                {
                    "event_id": "evt_2",
                    "event_type": "TASK_FINISHED",
                    "aggregate_type": "TASK",
                    "aggregate_id": "task-2",
                    "episode_id": "EPU_2",
                    "occurred_time": datetime(2026, 9, 21, 5, 0, 0),
                    "trace_id": "trace-2",
                    "task_id": "task-2",
                    "payload": {"must": "not leak"},
                    "metadata": {"must": "not leak"},
                },
                {"event_id": "evt_1", "event_type": "TASK_STARTED"},
            ]

    repository = EventRepository()
    dispatcher = PlatformApiDispatcher({
        "RuntimeEventApiController": RuntimeEventApiController(RuntimeEventApiService(repository))
    })

    status, payload = dispatcher.dispatch("GET", "/api/v1/runtime/events?limit=1&offset=50")

    assert status == 200
    assert repository.calls == [(2, 50)]
    page = payload["data"]
    assert page["count"] == 1
    assert page["offset"] == 50
    assert page["has_more"] is True
    assert page["items"][0]["event_id"] == "evt_2"
    assert page["items"][0]["occurred_at"].endswith("+00:00")
    assert "payload" not in page["items"][0]
    assert "metadata" not in page["items"][0]

    status, payload = dispatcher.dispatch("GET", "/api/v1/runtime/events?limit=101&offset=0")
    assert status == 400
    assert payload["code"] == "INVALID_REQUEST"


def test_healthz_is_available_without_business_controllers():
    dispatcher = PlatformApiDispatcher({})
    status, payload = dispatcher.dispatch("GET", "/healthz")
    assert status == 200
    assert payload["code"] == "OK"
    assert payload["data"]["status"] == "UP"


def test_unknown_route_returns_json_404_envelope():
    server = build_http_server(_controllers(), host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        try:
            urllib.request.urlopen(f"http://{host}:{port}/api/v1/missing", timeout=5)
        except urllib.error.HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 404
            assert payload["code"] == "ROUTE_NOT_FOUND"
        else:
            raise AssertionError("missing route must return HTTP 404")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
