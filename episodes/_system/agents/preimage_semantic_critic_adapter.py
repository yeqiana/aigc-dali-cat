#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Advisory PREIMAGE Candidate Set Critic; canonical PREIMAGE stays authoritative."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import preimage_authority_snapshot
import preimage_task_contract
import product_review_adapter
import storyos_config

ROOT = Path(__file__).resolve().parents[3]
ADAPTER_KEY = "agent_runtime.adapters.preimage_semantic_critic"
REQUEST_KIND = "preimage-semantic-critic-shadow"
DECISION_SCHEMA = ROOT / "episodes/_system/agents/critic_decision.schema.json"
DECISIONS = frozenset({"ACCEPT_CANDIDATE", "REPAIR", "NEEDS_USER", "BLOCK"})
REQUIRED_DECISION_KEYS = frozenset({"decision", "issue_codes", "severity", "repair_scope", "evidence"})


class PreimageCriticError(ValueError):
    pass


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def request_sha256(path: Path, request: dict) -> str:
    """Hash the loaded request payload when persistence owns the logical path.

    Runtime Review requests may live in MySQL/dual persistence and therefore
    have no corresponding local file.  The caller already loaded this exact
    request through product_review_adapter, so bind the report to that payload.
    """
    persistence = product_review_adapter.runtime_review_persistence
    if persistence.is_request_path(path):
        return digest(request)
    return sha_file(path)


def request_snapshot_sha256(path: Path) -> str:
    """Hash the immutable request snapshot persisted beside the Critic attempt."""
    snapshot = Path(path)
    if not snapshot.is_file():
        raise PreimageCriticError("PREIMAGE Critic immutable request snapshot missing")
    return sha_file(snapshot)


def adapter_config() -> dict:
    cfg = storyos_config.load_config()
    errors = storyos_config.validate(cfg)
    if errors:
        raise PreimageCriticError("invalid StoryOS config: " + "; ".join(errors))
    value = storyos_config.get_path(cfg, ADAPTER_KEY)
    if not isinstance(value, dict):
        raise PreimageCriticError("PREIMAGE Semantic Critic config missing")
    return value


def validate_decision(payload: Any) -> dict:
    try:
        import story_semantic_critic_adapter as shared
    except ModuleNotFoundError:
        from agents import story_semantic_critic_adapter as shared
    try:
        return shared.validate_decision(payload)
    except shared.CriticDecisionError as exc:
        raise PreimageCriticError(str(exc)) from exc


def build_frozen_candidate_set(episode_dir: Path, snapshot: dict | None = None,
                               task_rows: list[dict] | None = None) -> dict:
    """Require current frozen snapshot and four canonically verified candidates."""
    ep = Path(episode_dir).resolve()
    if snapshot is None:
        snapshot = json.loads((ep / preimage_authority_snapshot.REL).read_text(encoding="utf-8-sig"))
    if not snapshot.get("snapshot_id") or preimage_authority_snapshot.stale_owned(ep, snapshot):
        raise PreimageCriticError("PREIMAGE authority snapshot is stale")
    rows = task_rows or preimage_task_contract.plan_tasks(ep, snapshot, resume=True)
    if {row.get("task_type") for row in rows} != set(preimage_task_contract.TASK_TYPES):
        raise PreimageCriticError("PREIMAGE candidate set is incomplete")
    candidates, obligations = {}, {}
    for task in rows:
        if task.get("status") != "REUSED":
            raise PreimageCriticError(f"PREIMAGE task is not finalized and reusable: {task.get('task_type')}")
        candidate = preimage_task_contract.read_candidate(ep, task)
        errors = preimage_task_contract.verify_candidate(candidate or {}, task)
        if errors:
            raise PreimageCriticError(f"canonical candidate verifier failed for {task.get('task_type')}: {'; '.join(errors)}")
        candidate_path = ep / task["candidate_output"]
        task_contract = {key: task.get(key) for key in (
            "task_id", "task_type", "node_id", "snapshot_id", "input_contract", "authority_scope", "verifier"
        )}
        candidates[task["task_type"]] = {
            "task_contract": task_contract,
            "task_contract_sha256": digest(task_contract),
            "candidate": candidate,
            "candidate_sha256": sha_file(candidate_path),
        }
        for scope in task["authority_scope"]:
            value = candidate["payload"][scope]
            applicability = "NOT_APPLICABLE" if value.get("applicable") is False else "APPLICABLE"
            obligations[scope] = {
                "applicability": applicability,
                "basis": "canonical_task_authority_scope_and_candidate_contract",
                "task_type": task["task_type"],
            }
    gates_path = ep / "meta/story-gates.json"
    gates = json.loads(gates_path.read_text(encoding="utf-8-sig")) if gates_path.is_file() else {}
    source_hashes = dict(snapshot.get("whole_authority_sha256") or snapshot.get("authority_sha256") or {})
    capsule = {
        "schema_version": 1,
        "kind": "preimage_semantic_critic_frozen_candidate_set",
        "snapshot_id": snapshot["snapshot_id"],
        "source_authority_sha256": source_hashes,
        "story_authority": gates.get("story") or {},
        "applicability": obligations,
        "candidate_set": candidates,
        "canonical_checks": {
            "all_task_contract_verifiers_pass": True,
            "all_candidates_match_snapshot": True,
            "canonical_semantic_decision": "ACCEPT_CANDIDATE",
            "canonical_authority_commit_invoked_by_critic": False,
        },
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
    }
    capsule["obligation_sha256"] = digest({"applicability": obligations, "source_authority_sha256": source_hashes})
    capsule["candidate_set_sha256"] = digest(candidates)
    capsule["capsule_sha256"] = digest(capsule)
    return capsule


def build_prompt(capsule: dict, *, attempt: int) -> str:
    if not isinstance(capsule, dict) or not capsule.get("capsule_sha256"):
        raise PreimageCriticError("frozen PREIMAGE capsule is missing")
    return f"""You are the bounded PREIMAGE Semantic Critic shadow, attempt {attempt}.
Review only the frozen, verified PREIMAGE candidate set below. This is advisory evidence.
The four candidates have already passed their existing canonical task verifiers.
Check only scopes whose applicability is APPLICABLE. NOT_APPLICABLE scopes are not defects.
Focus on cross-scope contradictions: identity, world/temporal continuity, wardrobe, POV,
visual narrative progression, environment consistency, and preservation of frozen authority.
Do not invent requirements beyond the supplied frozen contracts. Do not search files or call tools.
Return one decision object under the provided schema. Allowed decisions are ACCEPT_CANDIDATE,
REPAIR, NEEDS_USER, BLOCK. REPAIR must name the narrow affected scope(s). Never propose a full
PREIMAGE redo. Do not modify candidates. Do not claim Gate PASS, authority writes, Episode state,
receipt, telemetry, execution id, retry, or commit. No reflection repair is executed.

<FROZEN_PREIMAGE_CANDIDATE_SET sha256="{capsule['capsule_sha256']}" obligation-sha256="{capsule['obligation_sha256']}">
{json.dumps(capsule, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
</FROZEN_PREIMAGE_CANDIDATE_SET>
"""


def verify_capsule_integrity(capsule: Any) -> dict:
    if not isinstance(capsule, dict):
        raise PreimageCriticError("frozen PREIMAGE capsule is missing")
    expected = str(capsule.get("capsule_sha256") or "")
    actual = digest({key: value for key, value in capsule.items() if key != "capsule_sha256"})
    if not expected or expected != actual:
        raise PreimageCriticError("PREIMAGE capsule obligation/candidate-set SHA mismatch")
    return capsule


def verify_frozen_candidate_files_unchanged(episode_dir: Path, capsule: dict) -> None:
    """Verify frozen candidate bytes without requiring the pre-commit snapshot to stay current."""
    ep = Path(episode_dir).resolve()
    verify_capsule_integrity(capsule)
    rows = capsule.get("candidate_set") or {}
    if set(rows) != set(preimage_task_contract.TASK_TYPES):
        raise PreimageCriticError("PREIMAGE frozen candidate set is incomplete")
    for task_type, row in rows.items():
        filename = preimage_task_contract.TASK_SPECS[task_type]["candidate"]
        path = ep / preimage_task_contract.CANDIDATE_REL / filename
        expected = str(row.get("candidate_sha256") or "")
        if not path.is_file() or not expected or sha_file(path).lower() != expected.lower():
            raise PreimageCriticError(f"PREIMAGE frozen candidate changed after freeze: {task_type}")


_CROSS_SCOPE_FACT_KEYS = frozenset({
    "identity", "character_identity", "character_id", "pov", "point_of_view",
    "time", "time_of_day", "timeline", "temporal_continuity", "wardrobe", "location",
})


def cross_scope_fact_conflicts(capsule: dict) -> list[dict]:
    """Emit advisory-only structural conflicts for repeated canonical fact keys.

    This does not replace a verifier: only identical semantic key names shared
    by two applicable scopes are compared, and any result remains evidence.
    """
    facts: dict[str, list[tuple[str, str]]] = {}

    def visit(value: Any, scope: str, path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key).strip().lower()
                child_path = f"{path}.{key_text}" if path else key_text
                if key_text in _CROSS_SCOPE_FACT_KEYS and isinstance(child, (str, int, float, bool)):
                    facts.setdefault(key_text, []).append((scope, str(child).strip().casefold()))
                visit(child, scope, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, scope, f"{path}[{index}]")

    for task_type, row in (capsule.get("candidate_set") or {}).items():
        payload = (row.get("candidate") or {}).get("payload") or {}
        for scope, value in payload.items():
            if (capsule.get("applicability") or {}).get(scope, {}).get("applicability") == "NOT_APPLICABLE":
                continue
            visit(value, scope)
    issues = []
    for key, values in sorted(facts.items()):
        distinct = {value for _scope, value in values if value}
        scopes = sorted({scope for scope, value in values if value})
        if len(distinct) > 1 and len(scopes) > 1:
            issues.append({
                "issue_code": "PREIMAGE_CROSS_SCOPE_FACT_CONFLICT",
                "fact_key": key,
                "scopes": scopes,
                "observed_values": sorted(distinct),
                "authority": "advisory_comparison_only",
            })
    return issues


def prepare_shadow_request(episode_dir: Path, capsule: dict, *, attempt: int = 1,
                           review_attempt: int = 1) -> dict | None:
    cfg = adapter_config()
    if cfg.get("shadow_enabled") is not True:
        return None
    if cfg.get("production_enabled") is True:
        raise PreimageCriticError("PREIMAGE Critic shadow and production cannot both be enabled")
    verify_capsule_integrity(capsule)
    current = build_frozen_candidate_set(episode_dir)
    if current["capsule_sha256"] != capsule.get("capsule_sha256"):
        raise PreimageCriticError("PREIMAGE candidate set changed after freeze")
    ep = Path(episode_dir).resolve()
    evidence_dir = ep / "meta/runtime/agent-shadow/preimage-semantic-critic"
    capsule_path = evidence_dir / f"attempt-{attempt}-candidate-set.json"
    _write_immutable(capsule_path, capsule)
    candidate_path = evidence_dir / f"attempt-{attempt}-decision.json"
    metadata = {
        "kind": REQUEST_KIND,
        "shadow_only": True,
        "candidate_authority": "runtime_evidence_only",
        "snapshot_id": capsule["snapshot_id"],
        "candidate_set_sha256": capsule["candidate_set_sha256"],
        "source_sha256": digest(capsule["source_authority_sha256"]),
        "obligation_sha256": capsule["obligation_sha256"],
        "decision_schema_sha256": sha_file(DECISION_SCHEMA),
        "critic_attempt": attempt,
        "review_attempt": review_attempt,
        "execution_domain": "PREIMAGE_SEMANTIC_CRITIC_SHADOW",
        "request_snapshot_path": (evidence_dir / f"attempt-{attempt}-request-snapshot.json").resolve().relative_to(ROOT).as_posix(),
    }
    request = product_review_adapter.prepare(
        ep, kind=REQUEST_KIND, runtime="WORK", attempt=attempt,
        prompt=build_prompt(capsule, attempt=attempt),
        source_paths=[capsule_path, DECISION_SCHEMA], candidate_path=candidate_path,
        host_execution="codex_user_runner_shadow", request_metadata=metadata,
    )
    snapshot_path = ROOT / metadata["request_snapshot_path"]
    snapshot = {"schema_version": 1, "kind": "immutable_preimage_critic_request_snapshot", "request": request}
    snapshot_sha = _write_immutable(snapshot_path, snapshot)
    request["request_snapshot_path"] = metadata["request_snapshot_path"]
    request["request_snapshot_sha256"] = snapshot_sha
    return request


def prepare_after_candidate_set(episode_dir: Path, snapshot: dict, task_rows: list[dict]) -> dict | None:
    """Create the advisory request after all four canonical candidates are finalized."""
    cfg = adapter_config()
    if cfg.get("shadow_enabled") is not True:
        return None
    if cfg.get("production_enabled") is True:
        raise PreimageCriticError("PREIMAGE Critic production is unsupported in Shadow phase")
    capsule = build_frozen_candidate_set(episode_dir, snapshot, task_rows)
    return prepare_shadow_request(episode_dir, capsule, attempt=1, review_attempt=1)


def _write_immutable(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with path.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise PreimageCriticError(f"immutable PREIMAGE Critic evidence conflict: {path}")
    return hashlib.sha256(raw).hexdigest()


def compare_with_existing(capsule: dict, decision: Any, *, reference_label: str | None = None,
                          reference_issue_codes: list[str] | None = None) -> dict:
    critic = validate_decision(decision)
    existing_issues: list[str] = []
    critic_issues = sorted(set(critic["issue_codes"]))
    intersection = sorted(set(existing_issues) & set(critic_issues))
    result = {
        "existing_accept": capsule["canonical_checks"]["all_task_contract_verifiers_pass"],
        "critic_accept": critic["decision"] == "ACCEPT_CANDIDATE",
        "existing_issue_codes": existing_issues,
        "critic_issue_codes": critic_issues,
        "issue_intersection": intersection,
        "critic_extra_issues": sorted(set(critic_issues) - set(existing_issues)),
        "critic_missing_issues": sorted(set(existing_issues) - set(critic_issues)),
        "decision_disagreement": (critic["decision"] == "ACCEPT_CANDIDATE") != bool(capsule["canonical_checks"]["all_task_contract_verifiers_pass"]),
        "issue_disagreement": bool(critic_issues != existing_issues),
        "ground_truth_available": reference_label is not None,
        "deterministic_cross_scope_flags": cross_scope_fact_conflicts(capsule),
        "reference_label": reference_label,
        "false_accept_critic": (critic["decision"] == "ACCEPT_CANDIDATE" and reference_label == "FAIL") if reference_label else None,
        "false_reject_critic": (critic["decision"] != "ACCEPT_CANDIDATE" and reference_label == "PASS") if reference_label else None,
    }
    if reference_issue_codes is not None:
        expected = sorted(set(reference_issue_codes))
        result["reference_issue_codes"] = expected
        result["critic_issue_precision"] = len(set(critic_issues) & set(expected)) / max(1, len(critic_issues))
        result["critic_issue_recall"] = len(set(critic_issues) & set(expected)) / max(1, len(expected))
    return {"decision": critic, **result, "authority_write": False, "gate_pass": False, "episode_transition": False}


def execution_telemetry(runner_result: Any, *, provider: str, model: str) -> dict:
    import codex_execution_telemetry
    telemetry = codex_execution_telemetry.model_execution(
        runner_result, provider=provider, model=model, authority_capsule_read_once=True
    )
    telemetry["complete"] = all(telemetry.get(key) is not None for key in (
        "wall_seconds", "input_tokens", "cached_input_tokens", "output_tokens",
        "reasoning_output_tokens", "failure", "timeout", "returncode", "telemetry_source"
    )) and bool(telemetry.get("provider")) and bool(telemetry.get("model")) and telemetry.get("real_model_execution") is True
    return telemetry


def configured_cli_model(episode_dir: str | Path) -> tuple[str | None, str | None]:
    try:
        import model_policy
        resolved = model_policy.resolve("critic.preimage", Path(episode_dir).resolve())
        return str(resolved["model"]), str(resolved["reasoning_effort"])
    except Exception:
        return None, None


def _comparison_evidence(existing: dict, critic: dict) -> dict:
    left = sorted(set(existing.get("issue_codes") or []))
    right = sorted(set(critic.get("issue_codes") or []))
    return {
        "existing_accept": existing.get("decision") == "ACCEPT_CANDIDATE",
        "critic_accept": critic.get("decision") == "ACCEPT_CANDIDATE",
        "existing_issue_codes": left,
        "critic_issue_codes": right,
        "issue_intersection": sorted(set(left) & set(right)),
        "critic_extra_issues": sorted(set(right) - set(left)),
        "critic_missing_issues": sorted(set(left) - set(right)),
        "decision_disagreement": (existing.get("decision") == "ACCEPT_CANDIDATE") != (critic.get("decision") == "ACCEPT_CANDIDATE"),
        "issue_disagreement": left != right,
    }


def legacy_execution_target(episode_dir: str | Path) -> dict[str, str]:
    model, _effort = configured_cli_model(episode_dir)
    if not model:
        raise PreimageCriticError("Episode-bound PREIMAGE Critic Model Policy is not available")
    return {"provider": "codex_user_runner", "model": model, "runtime": "CODEX"}


def execute_shadow_request(episode_dir: Path, *, attempt: int, timeout: int = 900,
                           reference_label: str | None = None,
                           reference_issue_codes: list[str] | None = None,
                           dispatch_authorization: dict | None = None) -> dict:
    if dispatch_authorization is None:
        import sys
        import runtime_dag
        routed = runtime_dag.dispatch_pending_critic(
            "preimage_semantic_critic", adapter=sys.modules[__name__], episode_dir=episode_dir,
            attempt=attempt, adapter_kwargs={"timeout": timeout, "reference_label": reference_label,
                "reference_issue_codes": reference_issue_codes},
        )
        if routed.get("status") != "DISPATCHED":
            return routed
        receipt = {key: routed.get(key) for key in (
            "task_type", "scheduler_authorization", "scheduler_authorized_target")}
        return {**routed.get("adapter_result", {}), "runtime_dispatch_receipt": receipt}
    import codex_critic_runner

    ep = Path(episode_dir).resolve()
    path = product_review_adapter.request_path(ep, REQUEST_KIND, attempt=attempt)
    request = product_review_adapter._read_json(path)
    if request.get("status") != product_review_adapter.AWAITING:
        raise PreimageCriticError("PREIMAGE Critic request is not awaiting execution")
    metadata = request.get("request_metadata") or {}
    if metadata.get("shadow_only") is not True or metadata.get("candidate_authority") != "runtime_evidence_only":
        raise PreimageCriticError("PREIMAGE Critic request is not advisory-only")
    sources = [(ROOT / row["path"]).resolve() for row in request.get("source_files") or []]
    if len(sources) != 2 or any(not p.is_file() for p in sources):
        raise PreimageCriticError("PREIMAGE Critic request source set is incomplete")
    if [sha_file(p) for p in sources] != [row["sha256"] for row in request["source_files"]]:
        raise PreimageCriticError("PREIMAGE Critic source SHA drift")
    snapshot_rel = str(metadata.get("request_snapshot_path") or "")
    request_snapshot_path = (ROOT / snapshot_rel).resolve()
    try:
        request_snapshot_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PreimageCriticError("PREIMAGE Critic request snapshot escapes repository") from exc
    if not request_snapshot_path.is_file():
        raise PreimageCriticError("PREIMAGE Critic immutable request snapshot missing")
    request_snapshot = json.loads(request_snapshot_path.read_text(encoding="utf-8-sig"))
    frozen = request_snapshot.get("request") if isinstance(request_snapshot, dict) else None
    if not isinstance(frozen, dict) or any(frozen.get(key) != request.get(key) for key in (
        "request_id", "request_fingerprint", "prompt_sha256", "source_files", "candidate_path"
    )):
        raise PreimageCriticError("PREIMAGE Critic request differs from immutable request evidence")
    capsule = json.loads(sources[0].read_text(encoding="utf-8-sig"))
    verify_capsule_integrity(capsule)
    candidate_path = (ROOT / request["candidate_path"]).resolve()
    if candidate_path.exists():
        raise PreimageCriticError("duplicate PREIMAGE Critic dispatch rejected")
    verify_frozen_candidate_files_unchanged(ep, capsule)
    model, effort = configured_cli_model(ep)
    if not model or not effort:
        raise PreimageCriticError("Episode-bound PREIMAGE Critic model/reasoning effort is not available")
    legacy_target = {"provider": "codex_user_runner", "model": model, "runtime": "CODEX"}
    execution_target = codex_critic_runner.consume_scheduler_authorization(
        task_type="preimage_semantic_critic", legacy_target=legacy_target,
        dispatch_authorization=dispatch_authorization,
    )
    model = execution_target["model"]
    prompt = str(request.get("prompt") or "")
    log_path = candidate_path.with_name(f"attempt-{attempt}-codex.jsonl")
    result = codex_critic_runner.launch(
        prompt, codex=codex_critic_runner.resolve_codex(None), root=ROOT, timeout=timeout,
        output_path=candidate_path, output_schema=DECISION_SCHEMA, model=model,
        reasoning_effort=effort, sandbox="read-only", log_path=log_path,
        execution_target=execution_target, dispatch_authorization=dispatch_authorization,
        router_proposed_target=request.get("effective_execution_target"),
    )
    telemetry = execution_telemetry(result, provider=execution_target["provider"], model=model)
    telemetry.update({
        "router_proposed_target": request.get("effective_execution_target"),
        "scheduler_authorized_target": (dispatch_authorization or {}).get("execution_target"),
        "adapter_execution_target": execution_target,
        "actual_dispatch_target": result.actual_dispatch_target,
        "route_behavior": "PRODUCTION_DISABLED" if (dispatch_authorization or {}).get("reason") == "PRODUCTION_DISABLED" else None,
    })
    if result.returncode != 0:
        raise PreimageCriticError(f"PREIMAGE Critic model failed with returncode={result.returncode}")
    decision = validate_decision(json.loads(candidate_path.read_text(encoding="utf-8-sig")))
    finalized_candidate, provenance = product_review_adapter.finalize_candidate(
        ep, kind=REQUEST_KIND, runtime="WORK", attempt=attempt,
        candidate_path=candidate_path, source_bindings=None,
    )
    if validate_decision(finalized_candidate) != decision:
        raise PreimageCriticError("finalized PREIMAGE Critic decision differs from Host candidate")
    verify_frozen_candidate_files_unchanged(ep, capsule)
    existing = {"decision": "ACCEPT_CANDIDATE", "issue_codes": []}
    comparison = _comparison_evidence(existing, decision)
    report = {
        "schema_version": 1,
        "kind": "preimage_semantic_critic_shadow_result",
        "request_id": request.get("request_id"),
        "request_sha256": request_sha256(path, request),
        "request_snapshot_sha256": request_snapshot_sha256(request_snapshot_path),
        "request_snapshot_path": snapshot_rel,
        "critic_provenance": provenance,
        "candidate_sha256": sha_file(candidate_path),
        "candidate_set_sha256": capsule["candidate_set_sha256"],
        "obligation_sha256": capsule["obligation_sha256"],
        "decision_schema_sha256": sha_file(DECISION_SCHEMA),
        "decision": decision,
        "comparison": comparison,
        "reference_label": reference_label,
        "reference_issue_codes": reference_issue_codes,
        "model_execution": telemetry,
        "telemetry_complete": telemetry["complete"],
        "critic_invoked": telemetry["real_model_execution"],
        "repair_invoked": False,
        "bounded_reflection": {"max_review_attempts": 2, "max_auto_repairs": 1, "repair_invoked": False},
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
        "image_generation_invoked": False,
    }
    evidence_path = candidate_path.with_name(f"attempt-{attempt}-result-evidence.json")
    _write_immutable(evidence_path, report)
    product_review_adapter.mark_complete(ep, REQUEST_KIND, final_path=evidence_path, attempt=attempt)
    import runtime_router
    report["health_update"] = runtime_router.capability_route_record_execution_telemetry(telemetry)
    return report
