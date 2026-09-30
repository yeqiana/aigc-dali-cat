"""Read-only, frozen-capsule producers for legacy and Agent World Prepare runs."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import agent_shadow_compare
import codex_execution_telemetry
import codex_user_runner
import preimage_authority_snapshot
import preimage_task_contract
import runtime_request
import story_json
import world_identity_contract
import world_state
import temporal_continuity_gate
import wardrobe_contract
import character_contract
import model_policy
from scoped_codex_worker import STEP_DIRECTIVES

DEFAULT_PROVIDER = "codex_cli_subscription"
DEFAULT_MODEL = model_policy.resolve_profile("structured_text")["model"]
REASONING_EFFORT = model_policy.resolve_profile("structured_text")["reasoning_effort"]
WORLD_SCOPE_ORDER = (
    "visual.world_identity",
    "visual.world_state",
    "visual.temporal_continuity",
    "visual.wardrobe",
)


def _json_sha(value) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _file_sha(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(ep: Path, rel: str) -> dict:
    value = story_json.read_json(ep / rel, default={})
    return value if isinstance(value, dict) else {}


def _wardrobe_baseline(ep: Path, state: dict, contract: dict) -> dict:
    if isinstance(contract, dict) and contract:
        return copy.deepcopy(contract)
    characters = ((state.get("initial_state") or {}).get("characters") or {})
    baseline = {
        str(cid): {
            key: value
            for key, value in (row or {}).items()
            if key in {"clothing_anchor", "status"} and value not in (None, "")
        }
        for cid, row in characters.items()
        if isinstance(row, dict)
    }
    return {"character_baselines": baseline, "source": "world_state_initial_characters"}


def freeze_task(ep: Path, task: dict) -> dict:
    """Read and bind the frozen World inputs once; never write to the Episode."""
    ep = Path(ep).resolve()
    if task.get("task_type") != "WORLD_PREPARE":
        raise ValueError("World Prepare producer only accepts WORLD_PREPARE")
    if list(task.get("authority_scope") or ()) != list(WORLD_SCOPE_ORDER):
        raise ValueError("WORLD_PREPARE authority scope differs from the canonical contract")
    snapshot = preimage_authority_snapshot.build(ep, write=False)
    if snapshot.get("snapshot_id") != task.get("snapshot_id"):
        raise ValueError("WORLD_PREPARE frozen PREIMAGE snapshot is stale")

    gates = _read_json(ep, "meta/story-gates.json")
    state = _read_json(ep, world_state.REL.as_posix())
    temporal = _read_json(ep, temporal_continuity_gate.REL.as_posix())
    wardrobe_contract_data = wardrobe_contract.load(ep) or {}
    character = character_contract.load(ep) or {}
    identity = world_identity_contract.effective(ep)
    request = runtime_request.authority_for_episode(ep) or {}
    request_projection = runtime_request.preimage_authority_projection(request)

    source_paths = {
        "story_gates": "meta/story-gates.json",
        "world_state": world_state.REL.as_posix(),
        "temporal_continuity": temporal_continuity_gate.REL.as_posix(),
        "wardrobe": wardrobe_contract.REL.as_posix(),
    }
    source_sha256 = {key: _file_sha(ep / rel) for key, rel in source_paths.items()}
    source_sha256["world_identity_effective"] = _json_sha(identity)
    source_sha256["wardrobe_contract_authority"] = wardrobe_contract.authority_sha256(ep)
    source_sha256["character_contract_authority"] = character_contract.authority_sha256(ep)
    source_sha256["runtime_request_preimage"] = runtime_request.preimage_authority_projection_sha256(request)
    frozen_scopes = {
        "visual.world_identity": copy.deepcopy(identity),
        "visual.world_state": copy.deepcopy(state),
        "visual.temporal_continuity": copy.deepcopy(temporal),
        "visual.wardrobe": _wardrobe_baseline(ep, state, wardrobe_contract_data),
    }
    story = gates.get("story") if isinstance(gates.get("story"), dict) else {}
    capsule = {
        "schema_version": 1,
        "kind": "world_prepare_frozen_authority_capsule",
        "snapshot_id": task["snapshot_id"],
        "authority_sha256": copy.deepcopy(
            (task.get("input_contract") or {}).get("source_authority_sha256") or {}
        ),
        "source_sha256": source_sha256,
        "authority": {
            "story_gate": copy.deepcopy(gates),
            "story_lock": copy.deepcopy(story),
            "runtime_request_preimage": request_projection,
            "character_contract": copy.deepcopy(character),
            "world_identity": copy.deepcopy(identity),
            "world_state": copy.deepcopy(state),
            "temporal_continuity": copy.deepcopy(temporal),
            "wardrobe": copy.deepcopy(wardrobe_contract_data),
        },
        "obligations": {
            "scopes": frozen_scopes,
            "story_lock_sha256": _json_sha({"story": story, "runtime_request": request_projection}),
        },
    }
    capsule["capsule_sha256"] = _json_sha({key: value for key, value in capsule.items() if key != "capsule_sha256"})
    frozen_task = copy.deepcopy(task)
    frozen_task.setdefault("input_contract", {})["world_prepare_capsule"] = capsule
    return frozen_task


def _prompt(task: dict, role: str) -> str:
    contract = task.get("input_contract") or {}
    capsule = contract.get("world_prepare_capsule") or {}
    if not capsule or capsule.get("snapshot_id") != task.get("snapshot_id"):
        raise ValueError("World Prepare frozen authority capsule missing or stale")
    body = {
        "task_id": task["task_id"],
        "task_type": task["task_type"],
        "snapshot_id": task["snapshot_id"],
        "authority_scope": list(task.get("authority_scope") or ()),
        "source_authority_sha256": contract.get("source_authority_sha256") or {},
        "world_prepare_capsule": capsule,
    }
    frozen = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    common = (
        "The Host has frozen all permitted authority in the capsule below. Do not inspect the repository, "
        "call tools, run commands, or write files. Use only this capsule. Return one JSON object and no prose. "
        "The JSON object must contain exactly the four authority scope keys listed in the task, each mapped to a "
        "non-empty object. Preserve every frozen value at its existing structural path. You may add derived notes, "
        "but never rewrite, omit, reorder, or contradict frozen Story Lock, world identity, time/location, world "
        "state, temporal continuity, or wardrobe values. Do not emit a Candidate envelope or telemetry; the Host "
        "will validate the payload and construct the Candidate envelope.\n"
    )
    if role == "legacy_control":
        # Keep the existing legacy WORLD_PREPARE instruction as the control contract.
        directive = STEP_DIRECTIVES["PREIMAGE_WORLD"]
        instruction = (
            "LEGACY CONTROL. Apply the existing PREIMAGE_WORLD instruction and Candidate contract below. "
            "For this read-only benchmark, return the declared payload as JSON instead of writing the candidate file.\n"
            + directive + "\n"
        )
    elif role == "agent_shadow":
        obligations = agent_shadow_compare.world_semantic_obligations(task)
        instruction = (
            "BOUNDED WORLD_PREPARE AGENT SHADOW. Execute only the World Prepare skill; do not broaden into "
            "Character Finalize, Environment Prepare, Visual Narrative, Critic, Gate, or Release work. Treat the "
            "machine contract below as mandatory: every required scope must be complete and every frozen leaf "
            "must remain unchanged.\n"
            "WORLD_OBLIGATIONS="
            + json.dumps(obligations, ensure_ascii=False, separators=(",", ":")) + "\n"
        )
    else:
        raise ValueError(f"unsupported World Prepare producer role: {role}")
    return instruction + common + "FROZEN_AUTHORITY_CAPSULE=" + frozen


def run(ep: Path, task: dict, *, role: str, timeout_seconds: int = 900,
        model: str | None = None) -> dict:
    """Execute one real read-only producer call and return Host-assembled evidence."""
    ep = Path(ep).resolve()
    selected_policy = model_policy.resolve("preimage.world_prepare", ep)
    model = str(model or selected_policy["model"])
    reasoning_effort = str(selected_policy["reasoning_effort"])
    frozen_task = task if (task.get("input_contract") or {}).get("world_prepare_capsule") else freeze_task(ep, task)
    prompt = _prompt(frozen_task, role)
    codex, resolution = codex_user_runner.resolve_codex(None)
    command = [
        str(codex), "exec", "--json", "--ephemeral", "--ignore-rules",
        "--skip-git-repo-check", "-C", str(ROOT), "-s", "read-only",
        "-c", f"model_reasoning_effort='{reasoning_effort}'", "-m", str(model), "-",
    ]
    request_id = uuid.uuid4().hex
    task_request = codex_user_runner.build_task(
        command, stdin_bytes=prompt.encode("utf-8"), timeout=int(timeout_seconds),
        cwd=ROOT, task_type="scoped_step", codex_home_mode="inherit", request_id=request_id,
    )
    result = (
        codex_user_runner.execute_codex(task_request)
        if codex_user_runner.bridge_required()
        else codex_user_runner.execute_task(task_request)
    )
    telemetry = codex_execution_telemetry.model_execution(
        result, provider=DEFAULT_PROVIDER, model=str(model), authority_capsule_read_once=True
    )
    telemetry.update({
        "reasoning_effort": reasoning_effort,
        "shadow": role == "agent_shadow",
        "canonical_write": False,
        "repeated_reads_scope": "frozen_authority_capsule",
        "capsule_sha256": (frozen_task["input_contract"]["world_prepare_capsule"]["capsule_sha256"]),
        "codex_resolution": resolution,
    })
    payload = None
    failure_reason = None
    try:
        if telemetry.get("returncode") != 0:
            failure_reason = f"codex_user_runner returncode={telemetry.get('returncode')}"
        elif telemetry.get("timeout") is not False:
            failure_reason = "codex_user_runner timeout status is missing or true"
        elif telemetry.get("tool_free") is not True:
            failure_reason = "producer attempted tool, command, or file activity"
        else:
            payload = codex_execution_telemetry.parse_json_object(
                codex_execution_telemetry.final_agent_message(result)
            )
    except Exception as exc:
        failure_reason = f"{type(exc).__name__}: {exc}"

    return {
        "schema_version": 1,
        "kind": "world_prepare_model_producer_result",
        "role": role,
        "payload": payload,
        "model_execution": telemetry,
        "failure_reason": failure_reason,
    }
