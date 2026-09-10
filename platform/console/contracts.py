from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConsolePage:
    """A product page exposed by Web Console."""

    key: str
    title: str
    api_prefix: str


@dataclass(frozen=True)
class ConsoleModule:
    """A grouped console capability."""

    key: str
    title: str
    pages: tuple[ConsolePage, ...]


CONSOLE_MODULES: tuple[ConsoleModule, ...] = (
    ConsoleModule(
        key="dashboard",
        title="Dashboard",
        pages=(ConsolePage("overview", "Overview", "/api/v1"),),
    ),
    ConsoleModule(
        key="agent",
        title="Agent Console",
        pages=(
            ConsolePage("agents", "Agents", "/api/v1/agents"),
            ConsolePage("executions", "Executions", "/api/v1/executions"),
        ),
    ),
    ConsoleModule(
        key="workflow",
        title="Workflow Console",
        pages=(ConsolePage("runs", "Workflow Runs", "/api/v1/workflows"),),
    ),
    ConsoleModule(
        key="observability",
        title="Observability",
        pages=(
            ConsolePage("trace", "Trace Explorer", "/api/v1/traces"),
            ConsolePage("artifact", "Artifact Browser", "/api/v1/artifacts"),
        ),
    ),
    ConsoleModule(
        key="memory",
        title="Memory Console",
        pages=(ConsolePage("memory", "Memory Search", "/api/v1/memory"),),
    ),
)
