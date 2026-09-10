from __future__ import annotations

from typing import Any, Callable

from platform.agent.runtime.contracts import AgentContext


ToolInvoker = Callable[[str, dict[str, Any]], dict[str, Any]]
SkillHandler = Callable[[dict[str, Any], AgentContext, ToolInvoker], dict[str, Any]]


class SkillRuntimeAdapter:
    """Loads and executes registered Skill handlers.

    Skill handlers receive an explicit tool invoker. They do not receive the
    MCP registry directly, so Agent Runtime can enforce allowed-tools policy.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, SkillHandler] = {}

    def register(self, skill_code: str, handler: SkillHandler) -> None:
        if not skill_code.strip():
            raise ValueError("skill_code must not be empty")
        self._handlers[skill_code] = handler

    def has_skill(self, skill_code: str) -> bool:
        return skill_code in self._handlers

    def execute(
        self,
        skill_code: str,
        input_data: dict[str, Any],
        context: AgentContext,
        tool_invoker: ToolInvoker,
    ) -> dict[str, Any]:
        try:
            handler = self._handlers[skill_code]
        except KeyError as exc:
            raise LookupError(f"skill not registered: {skill_code}") from exc
        result = handler(dict(input_data), context, tool_invoker)
        if not isinstance(result, dict):
            raise TypeError(f"skill {skill_code} must return dict")
        return result
