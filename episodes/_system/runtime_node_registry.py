"""Scheduling-only registry for Story OS Runtime nodes.

The registry defines topology and executor labels.  It does not execute a node,
write episode state, or decide any Gate.
"""
from __future__ import annotations


def node(node_id, node_type, *, depends_on=(), priority="MEDIUM", priority_score=None,
         executor, retry_policy=None, evidence_required=(), execution_policy=None):
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
        "execution_policy": dict(execution_policy or {"mode": "serial", "parallel_safe": False,
            "resource_class": "text", "max_concurrency": 1}),
    }


def first_batch_nodes():
    """Logical production topology; labels only, never independent executors."""
    return [
        node("story_lock", "story", priority="HIGH", executor="CREATIVE_STORY",
             evidence_required=("meta/story-gates.json",)),
        node("character_finalize", "character", depends_on=("story_lock",), executor="PREIMAGE_CHARACTER_FINALIZE",
             evidence_required=("meta/runtime/preimage-candidates/character-finalize.json",), execution_policy={"mode":"parallel_safe","parallel_safe":True,"resource_class":"authority","max_concurrency":4}),
        node("environment_prepare", "environment", depends_on=("story_lock",), executor="PREIMAGE_ENVIRONMENT",
             evidence_required=("meta/runtime/preimage-candidates/environment.json",), execution_policy={"mode":"parallel_safe","parallel_safe":True,"resource_class":"authority","max_concurrency":4}),
        node("world_prepare", "environment", depends_on=("story_lock",), executor="PREIMAGE_WORLD",
             evidence_required=("meta/runtime/preimage-candidates/world.json",), execution_policy={"mode":"parallel_safe","parallel_safe":True,"resource_class":"authority","max_concurrency":4}),
        node("visual_narrative_prepare", "story", depends_on=("story_lock",), executor="PREIMAGE_VISUAL_NARRATIVE",
             evidence_required=("meta/runtime/preimage-candidates/visual-narrative.json",), execution_policy={"mode":"parallel_safe","parallel_safe":True,"resource_class":"authority","max_concurrency":4}),
        node("preimage_authority_commit", "review", depends_on=("character_finalize","environment_prepare","world_prepare","visual_narrative_prepare"), executor="preimage_protocol.commit_candidates",
             evidence_required=("meta/runtime/preimage-authority-barrier.json",)),
        node("frame_contract_compile", "frame_contract",
             depends_on=("preimage_authority_commit",), executor="PREIMAGE_COMPILE",
             evidence_required=("meta/runtime/contracts/frame-contract-index.json",)),
        node("image_generation", "image_generation", depends_on=("frame_contract_compile",),
             priority="HIGH", executor="PRODUCTION",
             evidence_required=("meta/production-ledger.json",), execution_policy={
                 "mode": "image_managed", "parallel_safe": False, "resource_class": "image", "max_concurrency": 3,
                 "delegated_to": "image_scheduler"}),
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
        execution_policy=({"mode": "image_managed", "parallel_safe": False, "resource_class": "image",
                           "max_concurrency": 3, "delegated_to": "image_scheduler"}
                          if spec.step_id == "PRODUCTION" else None),
    ) for spec in step_specs]
