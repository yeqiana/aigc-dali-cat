from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


EvolutionStatus = Literal["OBSERVED", "PROPOSED", "NEEDS_REVIEW"]


@dataclass(frozen=True)
class CapabilityEvolutionProposal:
    """A controlled proposal for improving an agent capability.

    This object is a governance artifact only. It never mutates agent
    configuration, prompts, workflows, or production runtime automatically.
    """

    agent: str
    capability: str
    proposal: str
    evidence_refs: tuple[str, ...]
    confidence: float
    status: EvolutionStatus


class AgentCapabilityEvolution:
    """Generate agent improvement proposals from learned patterns."""

    def generate_proposal(
        self,
        *,
        agent: str,
        pattern: str,
        evidence_refs: list[str],
        confidence: float,
    ) -> CapabilityEvolutionProposal:
        capability = self._resolve_capability(pattern)
        status: EvolutionStatus = (
            "PROPOSED" if confidence >= 0.8 else "NEEDS_REVIEW"
        )

        return CapabilityEvolutionProposal(
            agent=agent,
            capability=capability,
            proposal=f"improve_{capability}",
            evidence_refs=tuple(evidence_refs),
            confidence=confidence,
            status=status,
        )

    def _resolve_capability(self, pattern: str) -> str:
        mapping = {
            "tool_timeout": "tool_retry_strategy",
            "memory_low_confidence": "memory_retrieval_strategy",
            "workflow_retry": "workflow_recovery_strategy",
        }
        return mapping.get(pattern, "general_runtime_behavior")
