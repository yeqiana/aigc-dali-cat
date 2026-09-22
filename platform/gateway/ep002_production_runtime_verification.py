from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


VerificationStatus = Literal["VERIFIED", "FAILED"]


@dataclass(frozen=True)
class EP002ProductionRuntimeVerificationResult:
    episode_id: str
    status: VerificationStatus
    checks: tuple[str, ...]
    failures: tuple[str, ...]


class EP002ProductionRuntimeVerifier:
    """Verify the first real EP002 production path on V3 runtime.

    This module validates runtime evidence only. It does not mutate episode
    state, workflow state, artifacts, or release metadata.
    """

    def verify(
        self,
        *,
        episode_id: str,
        workflow_ok: bool,
        agent_runtime_ok: bool,
        skill_execution_ok: bool,
        mcp_tool_ok: bool,
        trace_ok: bool,
        memory_ok: bool,
        artifact_ok: bool,
    ) -> EP002ProductionRuntimeVerificationResult:
        checks: list[str] = []
        failures: list[str] = []

        validations = (
            ("workflow", workflow_ok),
            ("agent_runtime", agent_runtime_ok),
            ("skill_execution", skill_execution_ok),
            ("mcp_tool", mcp_tool_ok),
            ("trace", trace_ok),
            ("memory", memory_ok),
            ("artifact", artifact_ok),
        )

        for name, passed in validations:
            if passed:
                checks.append(name)
            else:
                failures.append(name)

        return EP002ProductionRuntimeVerificationResult(
            episode_id=episode_id,
            status="VERIFIED" if not failures else "FAILED",
            checks=tuple(checks),
            failures=tuple(failures),
        )
