"""Task type -> DAG step is one mapping, and every step is registered (P0-E).

A PREIMAGE task type and its DAG step name are not the same string:
ENVIRONMENT_PREPARE runs as the step PREIMAGE_ENVIRONMENT. Producers used to
build the step by concatenation, "PREIMAGE_" + task_type, which invented
PREIMAGE_ENVIRONMENT_PREPARE / PREIMAGE_WORLD_PREPARE /
PREIMAGE_VISUAL_NARRATIVE_PREPARE -- names no registry has ever held.

The failure was deterministic and late: execution_capsule.compile_capsule raises
"unsupported step" only when a worker starts, so on a real episode the other
three tasks were already running when the fourth took the process down.

These tests keep the mapping single-sourced and every registry in agreement, and
they fail at test time rather than 20 minutes into a fan-out.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import execution_capsule
import preimage_task_contract as contract
import runtime_node_registry
import scoped_codex_worker
import storyos_config

SYSTEM = ROOT / "episodes" / "_system"


def _stage_read_sets() -> dict:
    return storyos_config.load_index()["stage_read_sets"]


def _executor_steps() -> frozenset:
    return frozenset(n.get("executor") for n in runtime_node_registry.first_batch_nodes())


# --- the mapping ------------------------------------------------------------

def test_every_task_type_has_a_canonical_step():
    assert set(contract.TASK_SPECS) == set(contract.TASK_TYPES)
    for task_type in contract.TASK_TYPES:
        assert contract.canonical_step(task_type) == contract.TASK_SPECS[task_type]["step"]


def test_step_index_is_a_true_inverse():
    for task_type in contract.TASK_TYPES:
        assert contract.task_type_for_step(contract.canonical_step(task_type)) == task_type


def test_unknown_task_type_fails_closed():
    try:
        contract.canonical_step("NOT_A_TASK")
    except ValueError as exc:
        assert "unsupported PREIMAGE task type" in str(exc)
    else:
        raise AssertionError("unknown task type must not resolve to a step")


def test_non_preimage_task_step_is_not_a_task_type():
    assert contract.task_type_for_step("PREIMAGE_COMPILE") is None
    assert contract.task_type_for_step("CREATIVE_STORY") is None


def test_step_names_are_not_the_concatenation():
    # The bug in one assertion: if these ever match again, the mapping has been
    # collapsed back into string building somewhere.
    for task_type in contract.TASK_TYPES:
        if task_type == "CHARACTER_FINALIZE":
            continue
        assert contract.canonical_step(task_type) != "PREIMAGE_" + task_type


# --- every registry agrees --------------------------------------------------

def test_all_registries_agree_on_the_real_repo():
    assert contract.registry_mismatches(
        stage_read_sets=_stage_read_sets(),
        step_directives=scoped_codex_worker.STEP_DIRECTIVES,
        executor_steps=_executor_steps(),
    ) == []


def test_assert_registries_aligned_passes():
    contract.assert_registries_aligned()


def test_registry_mismatches_detects_a_missing_read_set():
    read_sets = {k: v for k, v in _stage_read_sets().items() if k != "PREIMAGE_WORLD"}

    errors = contract.registry_mismatches(
        stage_read_sets=read_sets,
        step_directives=scoped_codex_worker.STEP_DIRECTIVES,
    )

    assert errors == ["WORLD_PREPARE: PREIMAGE_WORLD missing from stage_read_sets"]


def test_registry_mismatches_detects_a_missing_directive():
    directives = {k: v for k, v in scoped_codex_worker.STEP_DIRECTIVES.items() if k != "PREIMAGE_ENVIRONMENT"}

    errors = contract.registry_mismatches(
        stage_read_sets=_stage_read_sets(),
        step_directives=directives,
    )

    assert errors == ["ENVIRONMENT_PREPARE: PREIMAGE_ENVIRONMENT missing from STEP_DIRECTIVES"]


def test_registry_mismatches_detects_a_missing_executor():
    executors = _executor_steps() - {"PREIMAGE_VISUAL_NARRATIVE"}

    errors = contract.registry_mismatches(
        stage_read_sets=_stage_read_sets(),
        step_directives=scoped_codex_worker.STEP_DIRECTIVES,
        executor_steps=executors,
    )

    assert errors == ["VISUAL_NARRATIVE_PREPARE: PREIMAGE_VISUAL_NARRATIVE missing from the node registry executors"]


# --- the producers use the mapping ------------------------------------------

def _step_name_construction(path: Path) -> list[str]:
    """Ways a step name gets rebuilt from parts instead of looked up.

    Deliberately narrow. Comparing against a registered name
    (``step == "PREIMAGE_COMPILE"``) and testing a prefix
    (``startswith("PREIMAGE_")``) are both fine and common; only building the
    name from a task type is the defect.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant) and isinstance(side.value, str) and "PREIMAGE_" in side.value:
                    found.append(f"line {node.lineno}: \"PREIMAGE_\" + ...")
        elif isinstance(node, ast.JoinedStr):
            for part in node.values:
                # exact prefix only, so telemetry labels like
                # f"HOST_ACTION_PREIMAGE_{...}" are not swept up
                if isinstance(part, ast.Constant) and part.value == "PREIMAGE_":
                    found.append(f"line {node.lineno}: f\"PREIMAGE_{{...}}\"")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "removeprefix" and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and arg.value == "PREIMAGE_":
                    found.append(f"line {node.lineno}: .removeprefix(\"PREIMAGE_\")")
    return found


def test_producers_do_not_build_step_names_by_concatenation():
    offenders = []
    for path in sorted(SYSTEM.glob("*.py")):
        if path.name.startswith("test_"):
            continue
        for hit in _step_name_construction(path):
            offenders.append(f"{path.name}:{hit}")

    assert offenders == []


def test_the_scan_would_catch_the_original_bug(tmp_path):
    """Keep the detector honest: it must flag the exact line that broke PREIMAGE."""
    probe = tmp_path / "probe.py"
    probe.write_text(
        'step = "PREIMAGE_" + task["task_type"]\n'
        'kind = step.removeprefix("PREIMAGE_")\n'
        'other = f"PREIMAGE_{task}"\n'
        'ok = step.startswith("PREIMAGE_") == (step == "PREIMAGE_COMPILE")\n',
        encoding="utf-8",
    )

    hits = _step_name_construction(probe)

    assert len(hits) == 3
    assert any("removeprefix" in h for h in hits)


def test_host_requests_name_a_registered_step(tmp_path):
    """The host-request `next_step` must be a step the registries hold."""
    ep = tmp_path / "ep"
    (ep / "meta/runtime").mkdir(parents=True)
    (ep / "meta/runtime/preimage-authority-snapshot.json").write_text(
        json.dumps({"snapshot_id": "a" * 24, "authority_sha256": {}}), encoding="utf-8"
    )
    snapshot = json.loads((ep / "meta/runtime/preimage-authority-snapshot.json").read_text(encoding="utf-8"))

    steps = {
        contract.canonical_step(task["task_type"])
        for task in contract.plan_tasks(ep, snapshot)
    }

    assert steps == set(contract.PREIMAGE_STEPS)
    assert steps <= set(_stage_read_sets())


# --- the capsule can actually compile every task ----------------------------

def test_capsule_compiles_and_enriches_every_task(tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta/runtime").mkdir(parents=True)
    (ep / "meta/runtime/preimage-authority-snapshot.json").write_text(
        json.dumps({"snapshot_id": "b" * 24, "authority_sha256": {"meta/story-gates.json": "c" * 64}}),
        encoding="utf-8",
    )

    for task_type in contract.TASK_TYPES:
        step = contract.canonical_step(task_type)
        data = execution_capsule.compile_capsule(ep, step, write=False)

        assert data["step"] == step
        # Reverse lookup used to strip the prefix by hand, yielding "ENVIRONMENT"
        # for PREIMAGE_ENVIRONMENT -- not a task type, so this enrichment was
        # silently None for all three _PREPARE tasks.
        assert data["preimage_task"] is not None, f"{step} lost its task contract"
        assert data["preimage_task"]["task_type"] == task_type


def test_concatenated_names_are_rejected_by_the_capsule(tmp_path):
    """The regression itself: the old names must stay unrecognised."""
    ep = tmp_path / "ep"
    (ep / "meta/runtime").mkdir(parents=True)
    (ep / "meta/runtime/preimage-authority-snapshot.json").write_text(
        json.dumps({"snapshot_id": "d" * 24, "authority_sha256": {}}), encoding="utf-8"
    )
    read_sets = set(_stage_read_sets())

    for task_type in contract.TASK_TYPES:
        invented = "PREIMAGE_" + task_type
        if invented in read_sets:
            continue
        try:
            execution_capsule.compile_capsule(ep, invented, write=False)
        except ValueError as exc:
            assert "unsupported step" in str(exc)
        else:
            raise AssertionError(f"{invented} should not compile")
