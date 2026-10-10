"""Shadow/legacy inventory cannot approve cutover or touch Episode state."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("shadow_inventory", ROOT / "scripts/storyos_shadow_inventory.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_inventory_classifies_shadow_without_automatic_retirement():
    cfg = {"agent_runtime": {
        "adapters": {
            "character_finalize": {"shadow_enabled": False, "production_enabled": True},
            "story_semantic_critic": {"shadow_enabled": True, "production_enabled": False},
            "final_semantic_critic": {"shadow_enabled": False, "production_enabled": False},
        },
        "task_capability_router": {"shadow_enabled": True, "production_enabled": True},
        "guardian_facade": {"shadow_enabled": True, "production_enabled": False},
    }}
    snapshot = repr(cfg)
    result = module.inventory(cfg)
    states = {x["component"]: x["status"] for x in result["components"]}
    assert states == {
        "adapter.character_finalize": "PRODUCTION_ONLY",
        "adapter.story_semantic_critic": "SHADOW_ONLY",
        "adapter.final_semantic_critic": "DISABLED",
        "task_capability_router": "PRODUCTION_AND_SHADOW",
        "guardian_facade": "SHADOW_ONLY",
    }
    assert result["retirement_auto_authorized"] is False
    assert result["diagnostic_only"] is True
    assert result["production_active_count"] == 2
    assert result["shadow_active_count"] == 3
    assert repr(cfg) == snapshot


def test_missing_or_invalid_control_flags_fail_closed():
    import pytest
    base = {"agent_runtime": {"adapters": {"x": {"shadow_enabled": True}},
           "task_capability_router": {"shadow_enabled": False, "production_enabled": False},
           "guardian_facade": {"shadow_enabled": False, "production_enabled": False}}}
    with pytest.raises(ValueError, match="boolean"):
        module.inventory(base)
