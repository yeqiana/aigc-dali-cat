from platform.operations.agent_capability_evolution import (
    AgentCapabilityEvolution,
)


def test_generate_capability_evolution_proposal():
    engine = AgentCapabilityEvolution()

    proposal = engine.generate_proposal(
        agent="story-agent",
        pattern="tool_timeout",
        evidence_refs=["exp-001", "exp-002"],
        confidence=0.9,
    )

    assert proposal.agent == "story-agent"
    assert proposal.capability == "tool_retry_strategy"
    assert proposal.status == "PROPOSED"
    assert len(proposal.evidence_refs) == 2


def test_low_confidence_requires_review():
    engine = AgentCapabilityEvolution()

    proposal = engine.generate_proposal(
        agent="workflow-agent",
        pattern="unknown_pattern",
        evidence_refs=["exp-003"],
        confidence=0.5,
    )

    assert proposal.status == "NEEDS_REVIEW"
