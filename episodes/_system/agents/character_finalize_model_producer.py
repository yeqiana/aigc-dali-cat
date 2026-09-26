"""Read-only real-model producer for Character Finalize benchmark/shadow runs."""
from __future__ import annotations

import json
import agent_shadow_compare
import uuid
from pathlib import Path

import codex_execution_telemetry
import codex_user_runner
import preimage_task_contract
import story_json

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROVIDER = "codex_cli_subscription"
DEFAULT_MODEL = "codex-config-default"


def _embedded_authority(ep: Path, task: dict) -> dict:
    """Read each declared authority source at most once and freeze it in the prompt."""
    embedded = dict((task.get("input_contract") or {}).get("authority_inputs") or {})
    for rel in task.get("required_read") or []:
        if rel in embedded:
            continue
        path = Path(ep) / rel
        embedded[rel] = story_json.read_json(path, default={}) if path.is_file() else {}
    return embedded


def _prompt(task: dict, authority: dict, role: str) -> str:
    obligations = agent_shadow_compare.character_semantic_obligations(task)
    capsule = {
        "role": role,
        "task": {
            "task_id": task["task_id"],
            "task_type": task["task_type"],
            "snapshot_id": task["snapshot_id"],
            "authority_scope": list(task.get("authority_scope") or []),
            "source_authority_sha256": (task.get("input_contract") or {}).get("source_authority_sha256") or {},
        },
        "strict_obligations": obligations,
        "authority": authority,
    }
    frozen = json.dumps(capsule, ensure_ascii=False, separators=(",", ":"))
    common = (
        "All required authority is embedded below. Do not inspect the repository, call tools, "
        "run commands, or write files. Use only this frozen capsule.\n"
        "Return only one JSON object with exactly these top-level keys: character, identity, pov, appearance. "
        "Each value must be a non-empty JSON object. Do not include telemetry.\n"
        "STRICT CONTRACT: character.visible_cast must cover every strict_obligations.cast_ids value; identity and "
        "appearance keys must exactly equal those cast ids; identity[Pxx] must contain the matching frozen name; "
        "appearance[Pxx] must contain the matching strict_obligations.appearance_anchors[Pxx] string verbatim, "
        "without rewriting 86版 as 1986版 or paraphrasing any locked anchor; pov.character_id and pov.person must "
        "exactly match strict_obligations. character.relationship, character.continuity_rule and pov.capture_rule "
        "must be non-empty.\n"
    )
    if role == "legacy_control":
        instruction = (
            "TARGET: produce only the CHARACTER_FINALIZE Candidate declared by the execution capsule/request. "
            "Read the locked Story and Character Seed Contract. Validate final identity, wardrobe baseline, POV "
            "and textual appearance anchor. Do not rewrite Story or create pixel masters. "
            "Preserve cast ids, names, POV and appearance anchors from authority.\n"
        )
    elif role == "agent_shadow":
        instruction = (
            "You are the bounded Character Finalize Agent shadow producer. Resolve only character.finalize from the "
            "provided authority capsule. Preserve identity continuity, POV, wardrobe baseline and textual appearance "
            "anchors. Do not expand into environment/world/visual narrative work.\n"
        )
    else:
        raise ValueError(f"unsupported benchmark role: {role}")
    return instruction + common + "FROZEN_CAPSULE=" + frozen


def run(
    ep: Path,
    task: dict,
    *,
    role: str,
    timeout_seconds: int = 900,
    model: str | None = None,
) -> dict:
    ep = Path(ep).resolve()
    if task.get("task_type") != "CHARACTER_FINALIZE":
        raise ValueError("real model producer only supports CHARACTER_FINALIZE")
    authority = _embedded_authority(ep, task)
    prompt = _prompt(task, authority, role)
    codex, resolution = codex_user_runner.resolve_codex(None)
    selected_model = str(model or DEFAULT_MODEL)
    command = [
        str(codex),
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-rules",
        "--skip-git-repo-check",
        "-C",
        str(ROOT),
        "-s",
        "read-only",
        "-c",
        "model_reasoning_effort='medium'",
    ]
    if model:
        command += ["-m", str(model)]
    command.append("-")
    request_id = uuid.uuid4().hex
    task_request = codex_user_runner.build_task(
        command,
        stdin_bytes=prompt.encode("utf-8"),
        timeout=timeout_seconds,
        cwd=ROOT,
        task_type="scoped_step",
        codex_home_mode="inherit",
        request_id=request_id,
    )
    result = (
        codex_user_runner.execute_codex(task_request)
        if codex_user_runner.bridge_required()
        else codex_user_runner.execute_task(task_request)
    )
    telemetry = codex_execution_telemetry.model_execution(
        result,
        provider=DEFAULT_PROVIDER,
        model=selected_model,
        authority_capsule_read_once=True,
    )
    telemetry.update({
        "shadow": role == "agent_shadow",
        "canonical_write": False,
        "codex_resolution": resolution,
        "authority_capsule_source_count": len(authority),
        "repeated_reads_scope": "frozen_authority_capsule",
    })
    if result.returncode != 0:
        raise RuntimeError(f"Character Finalize model producer failed rc={result.returncode}")
    payload = codex_execution_telemetry.parse_json_object(
        codex_execution_telemetry.final_agent_message(result)
    )
    candidate = preimage_task_contract.candidate_template(
        task, {"character.finalize": payload}
    )
    candidate["model_execution"] = telemetry
    errors = preimage_task_contract.verify_candidate(candidate, task)
    if errors:
        raise ValueError("real model Character Finalize candidate invalid: " + "; ".join(errors))
    semantic = agent_shadow_compare.compare_character_finalize_semantics(task, candidate)
    if not semantic["pass"]:
        raise ValueError("real model Character Finalize obligations failed: " + "; ".join(semantic["errors"]))
    return candidate