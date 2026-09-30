"""PROMPT_AUTHORING is one scoped step between PREIMAGE and Visual Lock."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_prompt_authoring_is_a_single_node_before_visual_lock():
    dag = json.loads((ROOT / "runtimes/runtime-dag.json").read_text(encoding="utf-8"))
    steps = {row["id"]: row for row in dag["steps"]}
    assert steps["PROMPT_AUTHORING"]["executor"] == "scoped_model"
    assert steps["PROMPT_AUTHORING"]["model_role"] == "prompt.production"
    assert steps["PROMPT_AUTHORING"]["depends_on"] == ["PREIMAGE_COMPILE"]
    assert steps["VISUAL_LOCK"]["depends_on"] == ["PROMPT_AUTHORING"]
    assert "REPAIR_PROMPT_AUTHORING" not in steps


def test_prompt_authoring_is_registered_with_existing_scheduler():
    contract = json.loads((ROOT / "runtimes/workflow-contract.json").read_text(encoding="utf-8"))
    node = contract["steps"]["PROMPT_AUTHORING"]
    assert node["runtime_node_only"] is True
    assert node["does_not_create_episode_stage"] is True
    assert node["model_role"] == "prompt.production"

    import sys

    sys.path.insert(0, str(ROOT / "episodes/_system"))
    import runtime_node_registry

    nodes = {row["node_id"]: row for row in runtime_node_registry.first_batch_nodes()}
    assert nodes["prompt_authoring"]["executor"] == "PROMPT_AUTHORING"
    assert nodes["prompt_authoring"]["depends_on"] == ["frame_contract_compile"]
    assert nodes["image_generation"]["depends_on"] == ["prompt_authoring"]
