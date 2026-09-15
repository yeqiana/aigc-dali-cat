from __future__ import annotations

import inspect
import json
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

from platform.api.contracts import (
    ApiResponse,
    CreateAgentRequest,
    MemorySearchRequest,
    StartWorkflowRunRequest,
)
from platform.api.routes import PLATFORM_API_ROUTES, RouteDefinition


REQUEST_FACTORIES: dict[str, Callable[[Mapping[str, Any]], Any]] = {
    "AgentApiController.create_agent": lambda body: CreateAgentRequest(**dict(body)),
    "WorkflowApiController.start_run": lambda body: StartWorkflowRunRequest(**dict(body)),
    "MemoryApiController.search": lambda body: MemorySearchRequest(**dict(body)),
}


@dataclass(frozen=True)
class CompiledRoute:
    definition: RouteDefinition
    pattern: re.Pattern[str]


def _compile_path_template(path: str) -> re.Pattern[str]:
    pieces: list[str] = []
    cursor = 0
    for match in re.finditer(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", path):
        pieces.append(re.escape(path[cursor:match.start()]))
        pieces.append(fr"(?P<{match.group(1)}>[^/]+)")
        cursor = match.end()
    pieces.append(re.escape(path[cursor:]))
    return re.compile("^" + "".join(pieces) + "$")


class PlatformApiDispatcher:
    """HTTP-agnostic router for ``PLATFORM_API_ROUTES``.

    Controllers remain the application boundary. This adapter only performs
    path matching, request DTO construction and stable HTTP status mapping; it
    does not create a second service/domain implementation.
    """

    def __init__(self, controllers: Mapping[str, object]) -> None:
        self.controllers = dict(controllers)
        self.routes = tuple(
            CompiledRoute(route, _compile_path_template(route.path))
            for route in PLATFORM_API_ROUTES
        )

    def dispatch(
        self,
        method: str,
        path: str,
        body: Mapping[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        clean_path = urlsplit(path).path
        method = str(method or "GET").upper()
        if method == "GET" and clean_path == "/healthz":
            return 200, {"code": "OK", "message": "platform api ready", "data": {"status": "UP"}}
        for route in self.routes:
            if route.definition.method != method:
                continue
            match = route.pattern.fullmatch(clean_path)
            if match is None:
                continue
            return self._invoke(route.definition, match.groupdict(), body or {})
        payload = ApiResponse.error(
            "ROUTE_NOT_FOUND",
            f"route not found: {method} {clean_path}",
        )
        return 404, payload.to_dict()

    def _invoke(
        self,
        route: RouteDefinition,
        path_params: Mapping[str, str],
        body: Mapping[str, Any],
    ) -> tuple[int, dict[str, Any]]:
        controller_name, method_name = route.handler.split(".", 1)
        controller = self.controllers.get(controller_name)
        if controller is None:
            payload = ApiResponse.error(
                "CAPABILITY_NOT_CONFIGURED",
                f"controller not configured: {controller_name}",
            )
            return 503, payload.to_dict()
        handler = getattr(controller, method_name, None)
        if handler is None or not callable(handler):
            payload = ApiResponse.error(
                "HANDLER_NOT_CONFIGURED",
                f"handler not configured: {route.handler}",
            )
            return 503, payload.to_dict()
        try:
            kwargs: dict[str, Any] = {}
            path_values = iter(path_params.values())
            factory = REQUEST_FACTORIES.get(route.handler)
            for param in inspect.signature(handler).parameters.values():
                if param.name in {"request", "payload"} and factory is not None:
                    kwargs[param.name] = factory(body)
                    continue
                try:
                    kwargs[param.name] = next(path_values)
                except StopIteration:
                    if param.default is inspect.Parameter.empty:
                        raise TypeError(f"missing route argument for {route.handler}: {param.name}")
            response = handler(**kwargs)
        except (TypeError, ValueError) as exc:
            payload = ApiResponse.error("INVALID_REQUEST", str(exc))
            return 400, payload.to_dict()
        except Exception as exc:  # application exception boundary
            payload = ApiResponse.error(
                "INTERNAL_ERROR",
                f"{type(exc).__name__}: {exc}",
            )
            return 500, payload.to_dict()
        if not isinstance(response, ApiResponse):
            payload = ApiResponse.error(
                "INVALID_HANDLER_RESPONSE",
                f"{route.handler} must return ApiResponse",
            )
            return 500, payload.to_dict()
        return self._status_for(response), response.to_dict()

    @staticmethod
    def _status_for(response: ApiResponse[Any]) -> int:
        if response.code == "OK":
            return 200
        if response.code.endswith("_NOT_FOUND"):
            return 404
        if response.code == "INVALID_REQUEST":
            return 400
        return 409


class PlatformApiHttpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address: tuple[str, int], dispatcher: PlatformApiDispatcher) -> None:
        self.dispatcher = dispatcher
        super().__init__(server_address, PlatformApiRequestHandler)


class PlatformApiRequestHandler(BaseHTTPRequestHandler):
    server: PlatformApiHttpServer

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003 - stdlib signature
        return

    def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib signature
        self.send_response(204)
        self._cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 - stdlib signature
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802 - stdlib signature
        self._handle("POST")

    def _handle(self, method: str) -> None:
        body: dict[str, Any] = {}
        if method != "GET":
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = -1
            if length < 0:
                self._send(400, ApiResponse.error("INVALID_REQUEST", "invalid Content-Length").to_dict())
                return
            if length:
                try:
                    decoded = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    self._send(400, ApiResponse.error("INVALID_JSON", str(exc)).to_dict())
                    return
                if not isinstance(decoded, dict):
                    self._send(400, ApiResponse.error("INVALID_JSON", "JSON body must be an object").to_dict())
                    return
                body = decoded
        status, payload = self.server.dispatcher.dispatch(method, self.path, body)
        self._send(status, payload)

    def _send(self, status: int, payload: Mapping[str, Any]) -> None:
        raw = json.dumps(dict(payload), ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def build_http_server(
    controllers: Mapping[str, object],
    host: str = "127.0.0.1",
    port: int = 0,
) -> PlatformApiHttpServer:
    return PlatformApiHttpServer((host, int(port)), PlatformApiDispatcher(controllers))


def build_default_http_server(
    host: str = "127.0.0.1",
    port: int = 8080,
) -> PlatformApiHttpServer:
    from platform.api.default_app import build_default_controllers

    return build_http_server(build_default_controllers(), host=host, port=port)
