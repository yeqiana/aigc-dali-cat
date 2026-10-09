"""Read-only frozen-capsule producer for legacy and Visual Agent Shadow runs."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
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
import story_json
import model_policy
from scoped_codex_worker import STEP_DIRECTIVES

DEFAULT_PROVIDER = "codex_cli_subscription"
DEFAULT_MODEL = model_policy.resolve_profile("authoring")["model"]
REASONING_EFFORT = model_policy.resolve_profile("authoring")["reasoning_effort"]
OUTPUT_SCHEMA_PATH = Path(__file__).with_name("visual_narrative_payload.schema.json")
VISUAL_SCOPE_ORDER = (
    "visual.narrative_core", "visual.shot_progression", "visual.capture_grammar",
)
SOURCE_FILES = {
    "story_gates": "meta/story-gates.json",
    "shot_progression_review": "meta/shot-progression-review.json",
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read(ep: Path, rel: str) -> dict:
    data = story_json.read_json(ep / rel, default={})
    return data if isinstance(data, dict) else {}


def freeze_task(ep: Path, task: dict) -> dict:
    """Bind the locked visual source files to the already-built PREIMAGE snapshot."""
    ep = Path(ep).resolve()
    if task.get("task_type") != "VISUAL_NARRATIVE_PREPARE":
        raise ValueError("Visual Narrative producer only accepts VISUAL_NARRATIVE_PREPARE")
    if list(task.get("authority_scope") or ()) != list(VISUAL_SCOPE_ORDER):
        raise ValueError("Visual Narrative authority scope differs from canonical task contract")
    snapshot = preimage_authority_snapshot.build(ep, write=False)
    if snapshot.get("snapshot_id") != task.get("snapshot_id"):
        raise ValueError("Visual Narrative frozen PREIMAGE snapshot is stale")
    gates = _read(ep, SOURCE_FILES["story_gates"])
    shot_review = _read(ep, SOURCE_FILES["shot_progression_review"])
    if shot_review.get("status") != "LOCKED":
        raise ValueError("Visual Narrative requires locked shot-progression review")
    paths = {key: rel for key, rel in SOURCE_FILES.items()}
    source_sha = {key: _sha((ep / rel).read_bytes()) for key, rel in paths.items()}
    story = gates.get("story") if isinstance(gates.get("story"), dict) else {}
    story_keys = ("hook_frames", "escalation_frames", "climax_frame", "payoff_frame",
                  "competing_explanations", "task_closed")
    frame_keys = ("frame", "action", "visual_function", "capture_purpose", "pov_mode",
                  "location_zone", "shot_scale", "scene_position_id", "anomaly_logic_stage",
                  "human_action_stage", "human_present", "emotion", "interaction", "new_information")
    frames = []
    for row in shot_review.get("frames") or []:
        if isinstance(row, dict):
            frames.append({key: copy.deepcopy(row[key]) for key in frame_keys if key in row})
    frozen_scopes = {
        "visual.narrative_core": {key: copy.deepcopy(story[key]) for key in story_keys if key in story},
        "visual.shot_progression": {"frames": frames},
        "visual.capture_grammar": {
            "schema_version": shot_review.get("schema_version"),
            "genre_family": shot_review.get("genre_family"),
            "anomaly_applicable": shot_review.get("anomaly_applicable"),
            "interaction_applicable": shot_review.get("interaction_applicable"),
            "rules": copy.deepcopy(shot_review.get("rules") or {}),
        },
    }
    if any(not isinstance(value, dict) or not value for value in frozen_scopes.values()):
        raise ValueError("Visual Narrative frozen obligations are incomplete")
    capsule = {
        "schema_version": 1, "kind": "visual_narrative_frozen_authority_capsule",
        "snapshot_id": task["snapshot_id"], "source_paths": paths,
        "source_sha256": source_sha,
        "authority_sha256": copy.deepcopy((task.get("input_contract") or {}).get("source_authority_sha256") or {}),
        "obligations": {"scopes": frozen_scopes},
    }
    canonical = json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    capsule["capsule_sha256"] = _sha(canonical)
    result = copy.deepcopy(task)
    result.setdefault("input_contract", {})["visual_narrative_capsule"] = capsule
    return result


def frozen_sources_unchanged(ep: Path, task: dict) -> bool:
    capsule = (task.get("input_contract") or {}).get("visual_narrative_capsule") or {}
    if capsule.get("snapshot_id") != task.get("snapshot_id"):
        return False
    for key, rel in (capsule.get("source_paths") or {}).items():
        path = Path(ep) / str(rel)
        if not path.is_file() or _sha(path.read_bytes()) != (capsule.get("source_sha256") or {}).get(key):
            return False
    return True


def _prompt(task: dict, role: str) -> str:
    contract = task.get("input_contract") or {}
    capsule = contract.get("visual_narrative_capsule") or {}
    if capsule.get("snapshot_id") != task.get("snapshot_id"):
        raise ValueError("Visual Narrative frozen authority capsule missing or stale")
    body = {"task_id": task["task_id"], "task_type": task["task_type"],
            "snapshot_id": task["snapshot_id"], "authority_scope": list(task["authority_scope"]),
            "source_authority_sha256": contract.get("source_authority_sha256") or {},
            "visual_narrative_capsule": capsule}
    frozen = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    if role == "legacy_control":
        instruction = ("LEGACY CONTROL. Follow the existing registered PREIMAGE_VISUAL_NARRATIVE instruction and "
                       "Candidate contract. This is an isolated read-only comparison; do not write files or authority. "
                       "Return exactly one JSON object containing the canonical Candidate payload only; do not emit "
                       "a Candidate envelope, telemetry, markdown, or explanation.\n" +
                       STEP_DIRECTIVES[preimage_task_contract.canonical_step("VISUAL_NARRATIVE_PREPARE")] + "\n")
        common = ("Use only this frozen task capsule and the registered legacy instruction. Do not inspect the "
                  "repository, call tools, run commands, or write files.\n")
    elif role in {"agent_shadow", "agent_production"}:
        obligations = agent_shadow_compare.visual_semantic_obligations(task)
        run_mode = "PRODUCTION" if role == "agent_production" else "SHADOW"
        instruction = (f"BOUNDED VISUAL NARRATIVE AGENT {run_mode}. Execute only VISUAL_NARRATIVE_PREPARE. "
                       "Do not expand into Character, Environment, World, Critic, Gate, or Release tasks. "
                       "Return exactly ONE JSON object matching the supplied output schema. Do not return Markdown, "
                       "code fences, explanations, examples, repeated JSON, or alternatives. Do not emit a Candidate "
                       "envelope, telemetry, or Gate decision. The first response character must be '{' and the last "
                       "response character must be '}'. For each scope, write a substantive summary of at least 80 "
                       "characters and list every top-level key from that scope's frozen obligation in anchors. "
                       "Ground every statement in the frozen fields; do not invent or alter story beats, temporal facts, "
                       "character references, shot order, POV, or capture rules.\nVISUAL_OBLIGATIONS=" +
                       json.dumps(obligations, ensure_ascii=False, separators=(",", ":")) + "\n")
        common = ("Host-frozen authority follows. Do not inspect the repository, call tools, run commands, or write files. "
                  "The Host binds all frozen fields into the Candidate and verifies them. Do not repeat those fields. "
                  "Do not emit a Candidate envelope, telemetry, or Gate decision.\n")
    else:
        raise ValueError(f"unsupported Visual Narrative producer role: {role}")
    return instruction + common + "FROZEN_AUTHORITY_CAPSULE=" + frozen


def _parse_agent_payload(text: str) -> dict:
    """Parse exactly one complete top-level JSON object; never recover fragments."""
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("VISUAL_OUTPUT_EMPTY")
    if raw.startswith("```"):
        raise ValueError("VISUAL_OUTPUT_MARKDOWN_FENCE")
    if not raw.startswith("{"):
        if "{" in raw:
            raise ValueError("VISUAL_OUTPUT_LEADING_CONTENT")
        try:
            top_level = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("VISUAL_OUTPUT_INVALID_JSON") from exc
        if not isinstance(top_level, dict):
            raise ValueError("VISUAL_OUTPUT_TOP_LEVEL_NOT_OBJECT")
        raise ValueError("VISUAL_OUTPUT_LEADING_CONTENT")
    decoder = json.JSONDecoder()
    try:
        value, end = decoder.raw_decode(raw)
    except json.JSONDecodeError as exc:
        if exc.pos >= len(raw) - 1 or "Unterminated" in exc.msg or "Expecting value" in exc.msg:
            raise ValueError("VISUAL_OUTPUT_TRUNCATED_OR_INVALID_JSON") from exc
        raise ValueError("VISUAL_OUTPUT_INVALID_JSON") from exc
    trailing = raw[end:].strip()
    if trailing:
        try:
            decoder.raw_decode(trailing)
        except json.JSONDecodeError:
            raise ValueError("VISUAL_OUTPUT_TRAILING_CONTENT")
        raise ValueError("VISUAL_MULTIPLE_JSON_DOCUMENTS")
    if not isinstance(value, dict):
        raise ValueError("VISUAL_OUTPUT_TOP_LEVEL_NOT_OBJECT")
    return value


def _validate_agent_payload(task: dict, payload: dict) -> None:
    """Validate the schema contract against the task's actual frozen scope keys."""
    if not isinstance(payload, dict) or set(payload) != set(VISUAL_SCOPE_ORDER):
        raise ValueError("VISUAL_PAYLOAD_SCOPE_SET_INVALID")
    obligations = agent_shadow_compare.visual_semantic_obligations(task).get("scopes") or {}
    for scope in VISUAL_SCOPE_ORDER:
        entry = payload.get(scope)
        if not isinstance(entry, dict) or set(entry) != {"proposal"}:
            raise ValueError(f"VISUAL_PAYLOAD_SCOPE_SCHEMA_INVALID:{scope}")
        proposal = entry.get("proposal")
        if not isinstance(proposal, dict) or set(proposal) != {"summary", "anchors"}:
            raise ValueError(f"VISUAL_PAYLOAD_PROPOSAL_SCHEMA_INVALID:{scope}")
        summary = proposal.get("summary")
        anchors = proposal.get("anchors")
        if not isinstance(summary, str) or not 80 <= len(summary) <= 1600:
            raise ValueError(f"VISUAL_PAYLOAD_SUMMARY_LENGTH_INVALID:{scope}")
        expected_keys = set((obligations.get(scope) or {}).keys())
        if (not isinstance(anchors, list) or not anchors
                or any(not isinstance(key, str) for key in anchors)
                or len(anchors) != len(set(anchors)) or set(anchors) != expected_keys):
            raise ValueError(f"VISUAL_PAYLOAD_ANCHORS_INVALID:{scope}")


def _legacy_schema_node(value):
    """Build a strict JSON shape schema from the frozen canonical payload."""
    if isinstance(value, dict):
        properties = {str(key): _legacy_schema_node(item) for key, item in value.items()}
        return {
            "type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False,
        }
    if isinstance(value, list):
        if value:
            item_schema = _legacy_schema_node(value[0])
            if any(_legacy_schema_node(item) != item_schema for item in value[1:]):
                raise ValueError("VISUAL_LEGACY_FROZEN_ARRAY_SHAPE_UNSUPPORTED")
        else:
            item_schema = {"type": "string"}
        return {"type": "array", "items": item_schema, "minItems": len(value), "maxItems": len(value)}
    if isinstance(value, bool):
        kind = "boolean"
    elif isinstance(value, int):
        kind = "integer"
    elif isinstance(value, float):
        kind = "number"
    elif isinstance(value, str):
        kind = "string"
    elif value is None:
        kind = "null"
    else:
        raise ValueError(f"VISUAL_LEGACY_FROZEN_VALUE_UNSUPPORTED:{type(value).__name__}")
    return {"type": kind}


def _legacy_output_schema(task: dict) -> dict:
    """Require the full legacy payload shape without applying the Agent proposal schema."""
    obligations = agent_shadow_compare.visual_semantic_obligations(task).get("scopes") or {}
    required = list(task.get("authority_scope") or ())
    if required != list(VISUAL_SCOPE_ORDER) or set(obligations) != set(required):
        raise ValueError("VISUAL_LEGACY_FROZEN_SCOPE_CONTRACT_INVALID")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "StoryOS Visual Narrative legacy Candidate payload",
        "type": "object",
        "properties": {scope: _legacy_schema_node(obligations[scope]) for scope in required},
        "required": required,
        "additionalProperties": False,
    }


def run(ep: Path, task: dict, *, role: str, timeout_seconds: int = 900, model: str | None = None) -> dict:
    ep = Path(ep).resolve()
    selected_policy = model_policy.resolve("preimage.visual_narrative", ep)
    model = str(model or selected_policy["model"])
    reasoning_effort = str(selected_policy["reasoning_effort"])
    frozen_task = task if (task.get("input_contract") or {}).get("visual_narrative_capsule") else freeze_task(ep, task)
    capsule = frozen_task["input_contract"]["visual_narrative_capsule"]
    # Reject stale source before dispatch; completion performs the same SHA check.
    if not frozen_sources_unchanged(ep, frozen_task):
        raise ValueError("frozen Visual Narrative source changed or capsule snapshot is stale")
    prompt = _prompt(frozen_task, role)
    codex, resolution = codex_user_runner.resolve_codex(None)
    command = [str(codex), "exec", "--json", "--ephemeral", "--ignore-rules", "--skip-git-repo-check",
               "-C", str(ROOT), "-s", "read-only",
               "-c", f"model_reasoning_effort='{reasoning_effort}'",
               "-m", str(model), "-"]
    if role in {"agent_shadow", "agent_production"}:
        if not OUTPUT_SCHEMA_PATH.is_file():
            raise FileNotFoundError(f"Visual Narrative output schema missing: {OUTPUT_SCHEMA_PATH}")
        schema_context = None
        schema_path = OUTPUT_SCHEMA_PATH
    elif role == "legacy_control":
        schema_context = tempfile.TemporaryDirectory(prefix="storyos-visual-legacy-schema-")
        schema_path = Path(schema_context.name) / "legacy-payload.schema.json"
        schema_path.write_text(json.dumps(_legacy_output_schema(frozen_task), ensure_ascii=False), encoding="utf-8")
    else:
        raise ValueError(f"unsupported Visual Narrative producer role: {role}")
    command[command.index("-c"):command.index("-c")] = ["--output-schema", str(schema_path)]
    request_id = uuid.uuid4().hex
    task_request = codex_user_runner.build_task(command, stdin_bytes=prompt.encode("utf-8"),
        timeout=int(timeout_seconds), cwd=ROOT, task_type="scoped_step", codex_home_mode="inherit",
        request_id=request_id)
    try:
        result = codex_user_runner.execute_model_task(task_request)
    finally:
        if schema_context is not None:
            schema_context.cleanup()
    telemetry = codex_execution_telemetry.model_execution(
        result, provider=DEFAULT_PROVIDER, model=str(model), authority_capsule_read_once=True)
    telemetry.update({"reasoning_effort": reasoning_effort, "shadow": role == "agent_shadow",
                      "canonical_write": False, "repeated_reads_scope": "frozen_authority_capsule",
                      "capsule_sha256": capsule["capsule_sha256"], "codex_resolution": resolution})
    payload = None
    failure = None
    try:
        if telemetry.get("returncode") != 0:
            failure = f"codex_user_runner returncode={telemetry.get('returncode')}"
        elif telemetry.get("timeout") is not False:
            failure = "codex_user_runner timeout status is missing or true"
        elif telemetry.get("tool_free") is not True:
            failure = "producer attempted tool, command, or file activity"
        else:
            payload = _parse_agent_payload(codex_execution_telemetry.final_agent_message(result))
            if role in {"agent_shadow", "agent_production"}:
                _validate_agent_payload(frozen_task, payload)
            elif set(payload) != set(VISUAL_SCOPE_ORDER):
                raise ValueError("VISUAL_LEGACY_PAYLOAD_SCOPE_SET_INVALID")
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    return {"schema_version": 1, "kind": "visual_narrative_prepare_model_producer_result",
            "role": role, "payload": payload, "model_execution": telemetry, "failure_reason": failure}
