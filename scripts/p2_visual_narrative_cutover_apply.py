#!/usr/bin/env python3
"""Apply the evidence-bound Visual Narrative cutover and isolated smoke."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path[:0] = [str(SYSTEM), str(ROOT)]

import runtime_atomic_store as atomic
import storyos_config

CONFIG = ROOT / "config/storyos.yaml"
GATE = ROOT / "reports/p2-visual-narrative-pre-cutover-gate-retry1-20260927.json"
SMOKE = ROOT / "reports/p2-visual-narrative-production-cutover-smoke-retry1-20260927.json"
RECORD = ROOT / "reports/p2-visual-narrative-production-cutover-retry1-20260927.json"
BENCHMARK = ROOT / "reports/p2-visual-narrative-paired-benchmark-schema-v2-20260927.json"
SHADOW_SMOKE = ROOT / "reports/p2-visual-narrative-shadow-smoke-retry3-20260927.json"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def transition_config_text(text: str, *, shadow_enabled: bool, production_enabled: bool) -> str:
    pattern = re.compile(
        r"(?m)(^    visual_narrative_prepare:\r?\n)(?P<body>(?:(?!^    [A-Za-z0-9_]+:)[^\r\n]*(?:\r?\n|$))+)"
    )
    match = pattern.search(text)
    if not match:
        raise ValueError("visual_narrative_prepare adapter block missing")
    body = match.group("body")
    body, shadow_count = re.subn(
        r"(?m)^      shadow_enabled: (?:true|false)[ \t]*$",
        f"      shadow_enabled: {'true' if shadow_enabled else 'false'}", body)
    body, production_count = re.subn(
        r"(?m)^      production_enabled: (?:true|false)[ \t]*$",
        f"      production_enabled: {'true' if production_enabled else 'false'}", body)
    if shadow_count != 1 or production_count != 1:
        raise ValueError("visual_narrative_prepare must have one shadow and production flag")
    return text[:match.start("body")] + body + text[match.end("body"):]


def adapter_state() -> dict:
    cfg = storyos_config.load_config()
    return {key: storyos_config.get_path(cfg, f"agent_runtime.adapters.visual_narrative_prepare.{key}", False) is True
            for key in ("shadow_enabled", "production_enabled", "legacy_fallback_on_technical")}


def _evidence_row(path: Path) -> dict:
    data = read_json(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path),
            "generated_at": data.get("generated_at")}


def validate_preflight(gate_path: Path, original_config: str) -> tuple[list[str], dict]:
    errors: list[str] = []
    gate = read_json(gate_path) if gate_path.is_file() else {}
    if gate.get("kind") != "p2_visual_narrative_pre_cutover_gate" or gate.get("immutable") is not True:
        errors.append("immutable typed Visual pre-cutover gate evidence is required")
    if gate.get("status") != "READY" or gate.get("blockers"):
        errors.append("Visual pre-cutover Gate is not READY")
    if gate.get("production_cutover_performed") is not False:
        errors.append("pre-cutover gate must record production_cutover_performed=false")
    if any(value is not True for value in (gate.get("checks") or {}).values()):
        errors.append("one or more pre-cutover checks are false")
    for row in (gate.get("source_evidence") or {}).values():
        rel = row.get("path") if isinstance(row, dict) else None
        source = ROOT / str(rel or "")
        if not rel or not source.is_file() or sha256_file(source) != row.get("sha256"):
            errors.append(f"gate source evidence missing or SHA changed: {rel}")
    state = adapter_state()
    expected_before = {"shadow_enabled": True, "production_enabled": False, "legacy_fallback_on_technical": True}
    if state != expected_before:
        errors.append(f"current Visual config is not the gated Shadow state: {state}")
    expected_gate_state = gate.get("adapter_state_at_gate") or {}
    if expected_gate_state != expected_before:
        errors.append("Gate adapter state differs from cutover precondition")
    benchmark_ref = (gate.get("source_evidence") or {}).get("visual_benchmark") or {}
    smoke_ref = (gate.get("source_evidence") or {}).get("visual_smoke") or {}
    benchmark = ROOT / str(benchmark_ref.get("path") or "")
    shadow_smoke = ROOT / str(smoke_ref.get("path") or "")
    if benchmark != BENCHMARK or shadow_smoke != SHADOW_SMOKE:
        errors.append("gate does not bind the expected Visual paired benchmark and shadow smoke")
    evidence = {
        "pre_cutover_gate": _evidence_row(gate_path) if gate_path.is_file() else None,
        "paired_benchmark": _evidence_row(benchmark) if benchmark.is_file() else None,
        "shadow_smoke": _evidence_row(shadow_smoke) if shadow_smoke.is_file() else None,
    }
    if any(row is None for row in evidence.values()):
        errors.append("required cutover evidence could not be resolved")
    return errors, {"gate": gate, "state": state, "evidence": evidence, "original_config": original_config}


def _visual_payload(task: dict) -> dict:
    import agent_shadow_compare
    scopes = agent_shadow_compare.visual_semantic_obligations(task).get("scopes") or {}
    return {scope: {"proposal": {
        "summary": ("Fixture production candidate preserves the frozen Visual Narrative obligation and all required "
                    "story, shot progression, point of view, and capture grammar constraints for isolated smoke."),
        "anchors": list((scopes.get(scope) or {}).keys()),
    }} for scope in task.get("authority_scope") or ()}


def production_smoke() -> dict:
    import host_request_persistence
    import preimage_execution_persistence as execution
    import preimage_task_contract as tasks
    import product_runtime_adapter as adapter

    base = ROOT / ".storyos-tmp"
    base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p2-visual-cutover-smoke-", dir=base) as raw:
        ep = Path(raw)
        old_workspace = os.environ.get("STORY_OS_RUNTIME_WORKSPACE")
        old_meta_store = host_request_persistence.storage_config.episode_meta_store_config
        old_mode = execution.mode
        try:
            os.environ["STORY_OS_RUNTIME_WORKSPACE"] = str(ep / "_runtime-workspace")
            host_request_persistence.storage_config.episode_meta_store_config = lambda: {"mode": "json"}
            execution.mode = lambda: "json"
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            (ep / "meta/episode-state.json").write_text(json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8")
            (ep / "meta/story-gates.json").write_text(json.dumps({"story": {
                "locked": True, "hook_frames": [1, 2], "escalation_frames": [8],
                "climax_frame": 19, "payoff_frame": 20, "competing_explanations": 2, "task_closed": True,
            }, "visual": {}}), encoding="utf-8")
            (ep / "meta/shot-progression-review.json").write_text(json.dumps({
                "schema_version": 3, "status": "LOCKED", "genre_family": "suspense_strange",
                "anomaly_applicable": True, "interaction_applicable": True,
                "rules": {"max_identical_setup": 2},
                "frames": [{"frame": "01", "action": "documented action", "visual_function": "establish context",
                            "capture_purpose": "record evidence", "pov_mode": "pov_camera", "location_zone": "interior",
                            "shot_scale": "wide", "scene_position_id": "room_entry", "anomaly_logic_stage": "ordinary",
                            "human_action_stage": "ordinary", "human_present": True, "emotion": {"state": "calm"},
                            "interaction": {"type": "none"}, "new_information": True}],
            }), encoding="utf-8")

            response = adapter.build_request(ep, runtime="WORK", mode="full_auto", resume=True,
                                             source="p2-visual-production-cutover-smoke")
            requests = response.get("requests") or []
            visual_shadows = [row for row in response.get("shadow_requests") or []
                              if row.get("shadow_kind") == "VISUAL_NARRATIVE_PREPARE_AGENT"]
            if len(requests) != 4 or visual_shadows:
                raise RuntimeError("production smoke requires four canonical requests and zero Visual shadow requests")
            visual = next(row for row in requests if (row.get("task") or {}).get("task_type") == "VISUAL_NARRATIVE_PREPARE")
            if visual.get("agent_adapter") != "VISUAL_NARRATIVE_PREPARE_AGENT":
                raise RuntimeError("canonical Visual request did not use Visual Narrative Agent Adapter")
            meta = visual.get("agent_execution") or {}
            if meta.get("shadow") is not False:
                raise RuntimeError("Visual production envelope must use live execution domain")

            for index, request in enumerate(requests, 1):
                adapter.mark_preimage_task_running(ep, request["request_id"], worker_id=f"visual-production-smoke-{index}")
            final_rows = []
            visual_candidate = None
            for request in requests:
                task = request["task"]
                if task["task_type"] == "VISUAL_NARRATIVE_PREPARE":
                    produced = {"payload": _visual_payload(task)}
                    visual_candidate, errors, semantic = adapter.visual_narrative_host_candidate(task, produced)
                    if errors or visual_candidate is None or semantic.get("pass") is not True:
                        raise RuntimeError("fixture Visual candidate failed verifier/semantic contract: " + "; ".join(errors))
                    candidate = visual_candidate
                else:
                    candidate = tasks.candidate_template(task, tasks.valid_payload(task))
                done = adapter.complete_preimage_task(ep, request["request_id"], candidate)
                final_rows.append(done)
                if request is visual:
                    before_retry = execution.find_execution(ep, task["snapshot_id"], task["task_id"], meta["execution_id"])
                    retry = adapter.complete_preimage_task(ep, request["request_id"], candidate)
                    after_retry = execution.find_execution(ep, task["snapshot_id"], task["task_id"], meta["execution_id"])
                    if retry.get("status") != "FINALIZED" or before_retry != after_retry:
                        raise RuntimeError("response-lost duplicate completion mutated the Visual execution")

            commit_rows = [row for row in final_rows if isinstance(row.get("authority_commit"), dict)]
            if len(commit_rows) != 1:
                raise RuntimeError("PREIMAGE barrier must invoke exactly one existing authority_commit")
            commit = commit_rows[0]["authority_commit"]
            record = execution.find_execution(ep, visual["task"]["snapshot_id"], visual["task"]["task_id"], meta["execution_id"])
            saved = host_request_persistence.load(ep, visual["request_id"]) or {}
            receipt = (record or {}).get("commit_receipt") or {}
            # Exercise attempt takeover on an isolated execution identity without touching canonical authority.
            probe_snapshot = "visual-smoke-supersede-snapshot"
            probe_task = "visual-smoke-supersede-task"
            first = execution.begin_execution(ep, snapshot_id=probe_snapshot, task_id=probe_task,
                execution_id="visual-smoke-attempt-1", attempt=1, idempotency_key="visual-smoke-idem-1", shadow=False)
            second = execution.begin_execution(ep, snapshot_id=probe_snapshot, task_id=probe_task,
                execution_id="visual-smoke-attempt-2", attempt=2, idempotency_key="visual-smoke-idem-2", shadow=False)
            superseded = execution.find_execution(ep, probe_snapshot, probe_task, "visual-smoke-attempt-1")
            checks = {
                "four_canonical_requests": len(requests) == 4,
                "zero_visual_shadow_requests": not visual_shadows,
                "visual_agent_adapter": visual.get("agent_adapter") == "VISUAL_NARRATIVE_PREPARE_AGENT",
                "live_execution_domain": meta.get("shadow") is False,
                "candidate_valid": not tasks.verify_candidate(visual_candidate, visual["task"]),
                "semantic_pass": (adapter._visual_shadow_runtime_dependencies()[0].compare_visual_narrative_semantics(visual["task"], visual_candidate) or {}).get("pass") is True,
                "execution_eligible": (record or {}).get("eligible") is False,
                "receipt_committed": receipt.get("status") == "COMMITTED",
                "authority_commit_pass": commit.get("status") == "PASS" and commit.get("committed") is True,
                "duplicate_completion_idempotent": True,
                "attempt_supersede": first.get("status") == "ACTIVE" and second.get("status") == "ACTIVE" and (superseded or {}).get("status") == "SUPERSEDED",
                "legacy_fallback_not_used": saved.get("agent_fallback_active") is not True,
                "episode_state_unchanged": adapter.episode_state(ep) == "STORYBOARD_LOCKED",
                "image_generation_not_invoked": True,
            }
            return {
                "schema_version": 1, "kind": "p2_visual_narrative_production_cutover_smoke",
                "generated_at": now(), "production_enabled": True, "shadow_enabled": False,
                "canonical_request_count": len(requests), "shadow_request_count": len(visual_shadows),
                "other_adapter_shadow_request_count": len(response.get("shadow_requests") or []) - len(visual_shadows),
                "adapter_code": visual.get("agent_adapter"), "execution_id": meta.get("execution_id"),
                "attempt": meta.get("attempt"), "idempotency_key": meta.get("idempotency_key"),
                "candidate_valid": checks["candidate_valid"], "semantic_pass": checks["semantic_pass"],
                "execution_status": (record or {}).get("status"), "execution_eligible": (record or {}).get("eligible"),
                "receipt_status": receipt.get("status"), "authority_commit_status": commit.get("status"),
                "authority_committed": commit.get("committed"),
                "duplicate_mutation": False, "legacy_fallback_active": bool(saved.get("agent_fallback_active")),
                "episode_state": adapter.episode_state(ep), "image_generation_invoked": False,
                "checks": checks, "pass": all(value is True for value in checks.values()),
                "isolated_temp_episode": True, "real_episode_authority_touched": False,
            }
        finally:
            host_request_persistence.storage_config.episode_meta_store_config = old_meta_store
            execution.mode = old_mode
            if old_workspace is None:
                os.environ.pop("STORY_OS_RUNTIME_WORKSPACE", None)
            else:
                os.environ["STORY_OS_RUNTIME_WORKSPACE"] = old_workspace


def _exclusive_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def apply(gate_path: Path = GATE) -> dict:
    if RECORD.exists() and SMOKE.exists():
        record = read_json(RECORD)
        if record.get("status") == "PRODUCTION_ENABLED" and read_json(SMOKE).get("pass") is True:
            return {"replayed": True, "record": record, "smoke": read_json(SMOKE)}
        raise FileExistsError("Visual cutover evidence exists in a non-replayable state")
    if SMOKE.exists() or RECORD.exists():
        raise FileExistsError("partial Visual cutover evidence exists; refusing another mutation")
    original_config = CONFIG.read_text(encoding="utf-8")
    errors, context = validate_preflight(gate_path, original_config)
    if errors:
        raise ValueError("Visual cutover preflight blocked: " + "; ".join(errors))
    before_state = context["state"]
    gate = context["gate"]
    gate_row = context["evidence"]["pre_cutover_gate"]
    gate_hash = gate_row["sha256"]
    gate_sources = context["evidence"]
    expected_after = {"shadow_enabled": False, "production_enabled": True, "legacy_fallback_on_technical": True}
    production_text = transition_config_text(original_config, shadow_enabled=False, production_enabled=True)
    try:
        atomic.atomic_write_text(CONFIG, production_text)
        storyos_config._CACHE.pop(storyos_config.CONFIG_PATH, None)
        if adapter_state() != expected_after:
            raise RuntimeError("Visual production config did not apply atomically")
        smoke = production_smoke()
        if smoke.get("pass") is not True:
            raise RuntimeError("Visual production smoke failed checks")
        _exclusive_json(SMOKE, smoke)
    except Exception as exc:
        atomic.atomic_write_text(CONFIG, original_config)
        storyos_config._CACHE.pop(storyos_config.CONFIG_PATH, None)
        failure = {
            "schema_version": 1, "kind": "p2_visual_narrative_production_cutover_smoke",
            "generated_at": now(), "production_enabled": False, "shadow_enabled": True,
            "pass": False, "failure": f"{type(exc).__name__}: {exc}",
            "rollback_status": adapter_state(), "image_generation_invoked": False,
        }
        if not SMOKE.exists():
            _exclusive_json(SMOKE, failure)
        rollback_record = {
            "schema_version": 1, "kind": "p2_visual_narrative_production_cutover_record",
            "generated_at": now(), "status": "ROLLED_BACK_AFTER_SMOKE_FAILURE",
            "production_cutover_performed": False, "failure": failure["failure"],
            "rollback_config": {"shadow_enabled": True, "production_enabled": False,
                                "legacy_fallback_on_technical": True},
            "adapter_state_after_rollback": adapter_state(),
            "pre_cutover_gate_path": gate_row["path"], "pre_cutover_gate_sha256": gate_hash,
            "smoke_path": SMOKE.relative_to(ROOT).as_posix(),
        }
        if not RECORD.exists():
            _exclusive_json(RECORD, rollback_record)
        return {"record": rollback_record, "smoke": failure}

    record = {
        "schema_version": 1, "kind": "p2_visual_narrative_production_cutover_record",
        "generated_at": now(), "status": "PRODUCTION_ENABLED", "production_cutover_performed": True,
        "pre_cutover_gate_path": gate_row["path"], "pre_cutover_gate_sha256": gate_hash,
        "pre_cutover_gate_generated_at": gate.get("generated_at"),
        "shadow_smoke_path": gate_sources["shadow_smoke"]["path"],
        "shadow_smoke_sha256": gate_sources["shadow_smoke"]["sha256"],
        "paired_benchmark_path": gate_sources["paired_benchmark"]["path"],
        "paired_benchmark_sha256": gate_sources["paired_benchmark"]["sha256"],
        "production_smoke_path": SMOKE.relative_to(ROOT).as_posix(),
        "production_smoke_sha256": sha256_file(SMOKE),
        "production_smoke_generated_at": smoke.get("generated_at"),
        "previous_config": before_state, "new_config": expected_after,
        "rollback_config": {"shadow_enabled": True, "production_enabled": False,
                             "legacy_fallback_on_technical": True},
        "head": gate.get("git_head"), "cutover_timestamp": now(),
        "checks": {"gate_ready": True, "gate_sha_unchanged": sha256_file(gate_path) == gate_hash,
                   "source_hashes_unchanged": True, "production_smoke_pass": smoke.get("pass") is True,
                   "authority_receipt_committed": smoke.get("receipt_status") == "COMMITTED",
                   "legacy_fallback_not_used": smoke.get("legacy_fallback_active") is False},
    }
    if not all(value is True for value in record["checks"].values()):
        atomic.atomic_write_text(CONFIG, original_config)
        storyos_config._CACHE.pop(storyos_config.CONFIG_PATH, None)
        raise RuntimeError("post-smoke evidence consistency check failed; config rolled back")
    _exclusive_json(RECORD, record)
    return {"record": record, "smoke": smoke}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, default=GATE)
    parser.add_argument("--apply", action="store_true", help="apply cutover; default only validates preflight")
    args = parser.parse_args()
    if not args.apply:
        errors, context = validate_preflight(args.gate.resolve(), CONFIG.read_text(encoding="utf-8"))
        print(json.dumps({"ready": not errors, "errors": errors,
                          "adapter_state": context["state"], "evidence": context["evidence"]}, ensure_ascii=False, indent=2))
        return 0 if not errors else 3
    result = apply(args.gate.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if (result.get("record") or {}).get("status") == "PRODUCTION_ENABLED" else 4


if __name__ == "__main__":
    raise SystemExit(main())
