"""Scheduling-only registry for Story OS Runtime nodes.

The registry defines topology and executor labels.  It does not execute a node,
write episode state, or decide any Gate.
"""
from __future__ import annotations


def node(node_id, node_type, *, depends_on=(), priority="MEDIUM", priority_score=None,
         executor, retry_policy=None, evidence_required=()):
    return {
        "node_id": node_id,
        "node_type": node_type,
        "depends_on": list(depends_on),
        "priority": priority,
        "priority_score": priority_score,
        "executor": executor,
        "evidence_required": list(evidence_required),
        "input_contract": {},
        "output_contract": {},
        "retry_policy": dict(retry_policy or {}),
    }


def first_batch_nodes():
    """Logical production topology; labels only, never independent executors."""
    return [
        node("story_lock", "story", priority="HIGH", executor="CREATIVE_STORY",
             evidence_required=("meta/story-gates.json",)),
        node("character_prepare", "character", depends_on=("story_lock",),
             executor="character_contract.prepare",
             evidence_required=("meta/character-contract.json",)),
        node("environment_prepare", "environment", depends_on=("story_lock",),
             executor="PREIMAGE_COMPILE",
             evidence_required=("meta/story-gates.json",)),
        node("frame_contract_compile", "frame_contract",
             depends_on=("character_prepare", "environment_prepare"), executor="PREIMAGE_COMPILE",
             evidence_required=("meta/runtime/contracts/frame-contract-index.json",)),
        node("image_generation", "image_generation", depends_on=("frame_contract_compile",),
             priority="HIGH", executor="PRODUCTION",
             evidence_required=("meta/production-ledger.json",)),
        node("review", "review", depends_on=("image_generation",), executor="incremental_frame_review.review",
             evidence_required=("meta/frame-reviews",)),
        node("repair", "repair", depends_on=("review",), executor="repair_engine.plan_repairs",
             evidence_required=("meta/production-ledger.json",)),
        node("release", "release", depends_on=("review", "repair"), priority="HIGH", executor="RELEASE",
             evidence_required=("meta/release-manifest.json",)),
    ]


def runtime_step_nodes(step_specs):
    """Adapt existing runtime steps into Scheduler contracts without changing executors."""
    type_by_step = {
        "INCREMENTAL_PLAN": "review",
        "CREATIVE_STORY": "story",
        "PREIMAGE_COMPILE": "frame_contract",
        "VISUAL_LOCK": "review",
        "PRODUCTION": "image_generation",
        "RELEASE": "release",
    }
    priority_by_step = {"VISUAL_LOCK": "HIGH", "PRODUCTION": "HIGH", "RELEASE": "HIGH"}
    return [node(
        spec.step_id,
        type_by_step.get(spec.step_id, "review"),
        depends_on=spec.depends_on,
        priority=priority_by_step.get(spec.step_id, "MEDIUM"),
        executor=spec.executor,
        evidence_required=spec.evidence_paths,
    ) for spec in step_specs]
