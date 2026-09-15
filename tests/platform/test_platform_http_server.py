from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from platform.api.controllers import AgentApiController, ExecutionApiController, TraceApiController
from platform.api.default_app import build_default_controllers
from platform.api.http_server import PlatformApiDispatcher, build_http_server
from platform.operations.experience_store import ExperienceStore, RuntimeExperience


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
