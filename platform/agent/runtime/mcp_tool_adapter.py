from __future__ import annotations

from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


class McpToolAdapter:
    """Small MCP/tool execution boundary for Agent Runtime.

    P7.4 keeps tool discovery and invocation isolated from Agent logic. Real
    MCP transport can replace handlers later without changing Agent Runtime.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, tool_code: str, handler: ToolHandler) -> None:
        if not tool_code.strip():
            raise ValueError("tool_code must not be empty")
        self._handlers[tool_code] = handler

    def has_tool(self, tool_code: str) -> bool:
        return tool_code in self._handlers

    def invoke(self, tool_code: str, request_data: dict[str, Any]) -> dict[str, Any]:
        try:
            handler = self._handlers[tool_code]
        except KeyError as exc:
            raise LookupError(f"tool not registered: {tool_code}") from exc
        result = handler(dict(request_data))
        if not isinstance(result, dict):
            raise TypeError(f"tool {tool_code} must return dict")
        return result
