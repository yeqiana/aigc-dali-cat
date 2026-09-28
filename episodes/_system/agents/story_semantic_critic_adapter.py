#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decision-only Story Semantic Critic shadow adapter.

The existing Story Review stays authoritative. This module validates an advisory
decision, compares it with the existing deterministic/reviewer outcome, and can
prepare an immutable host request through the existing Product Review adapter.
It never writes Story Review, Gate, Episode state, or canonical Authority.
"""
from __future__ import annotations

import json
import hashlib
import tomllib
from pathlib import Path
from typing import Any

import product_review_adapter
import storyos_config

ROOT = Path(__file__).resolve().parents[3]
ADAPTER_KEY = "agent_runtime.adapters.story_semantic_critic"
REQUEST_KIND = "story-semantic-critic-shadow"
DECISIONS = frozenset({"ACCEPT_CANDIDATE", "REPAIR", "NEEDS_USER", "BLOCK"})
SEVERITIES = frozenset({"LOW", "MEDIUM", "HIGH"})
REQUIRED_KEYS = frozenset({"decision", "issue_codes", "severity", "repair_scope", "evidence"})
SCHEMA_PATH = ROOT / "episodes/_system/agents/critic_decision.schema.json"
RUBRIC_PATHS = (
    ROOT / "standards/制作规范_正式版.md",
    ROOT / "standards/创作执行强制规范_V2.0.3.2.md",
    ROOT / "standards/story_regressions/cases.json",
    ROOT / "standards/传播核与动作回应链规范_V1.0.md",
)
APPLICABILITY_REL = Path("meta/shot-progression-review.json")


class CriticDecisionError(ValueError):
    pass


def adapter_config() -> dict[str, Any]:
    cfg = storyos_config.load_config()
    errors = storyos_config.validate(cfg)
    if errors:
        raise CriticDecisionError("invalid StoryOS config: " + "; ".join(errors))
    value = storyos_config.get_path(cfg, ADAPTER_KEY)
    if not isinstance(value, dict):
        raise CriticDecisionError("Story Semantic Critic adapter config missing")
    return value


def validate_decision(payload: Any) -> dict[str, Any]:
    """Validate the strict decision-only wire contract; reject gate/telemetry fields."""
    if not isinstance(payload, dict):
        raise CriticDecisionError("critic decision must be a JSON object")
    keys = frozenset(payload)
    if keys != REQUIRED_KEYS:
        missing = sorted(REQUIRED_KEYS - keys)
        extra = sorted(keys - REQUIRED_KEYS)
        raise CriticDecisionError(f"critic decision keys mismatch; missing={missing}; extra={extra}")
    decision = payload.get("decision")
    if decision not in DECISIONS:
        raise CriticDecisionError("critic decision is outside the P3 decision enum")
    if payload.get("severity") not in SEVERITIES:
        raise CriticDecisionError("critic severity is invalid")
    for key in ("issue_codes", "repair_scope", "evidence"):
        values = payload.get(key)
        if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
            raise CriticDecisionError(f"critic {key} must be a list of non-empty strings")
    if decision == "ACCEPT_CANDIDATE" and payload["issue_codes"]:
        raise CriticDecisionError("ACCEPT_CANDIDATE cannot include issue_codes")
    if decision == "REPAIR" and not payload["issue_codes"]:
        raise CriticDecisionError("REPAIR requires at least one issue_code")
    return {key: list(value) if isinstance(value, list) else value for key, value in payload.items()}


def frozen_applicability_context(episode_dir: Path) -> dict[str, Any]:
    """Read the canonical locked applicability contract; never infer it from prose."""
    source = Path(episode_dir).resolve() / APPLICABILITY_REL
    if not source.is_file():
        raise CriticDecisionError("frozen Story applicability contract is missing")
    try:
        value = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise CriticDecisionError("frozen Story applicability contract is invalid JSON") from exc
    if not isinstance(value, dict) or value.get("status") != "LOCKED":
        raise CriticDecisionError("frozen Story applicability contract is not LOCKED")
    applicable = value.get("anomaly_applicable")
    if type(applicable) is not bool:
        raise CriticDecisionError("frozen Story applicability is missing a boolean anomaly_applicable")
    reason = str(value.get("anomaly_exception_reason") or "").strip()
    if applicable is False and not reason:
        raise CriticDecisionError("non-anomaly applicability requires its locked exception reason")
    try:
        rel = source.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise CriticDecisionError("frozen Story applicability source escapes repository") from exc
    return {
        "source_path": rel,
        "source_sha256": sha256_file(source),
        "status": "LOCKED",
        "anomaly_applicable": applicable,
        "anomaly_exception_reason": reason,
    }


def verify_applicability_context(context: Any) -> dict[str, Any]:
    """Recheck the persisted contract binding before prompt construction/execution."""
    if not isinstance(context, dict):
        raise CriticDecisionError("frozen Story applicability context is missing")
    source = (ROOT / str(context.get("source_path") or "")).resolve()
    try:
        source.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise CriticDecisionError("frozen Story applicability source escapes repository") from exc
    if not source.is_file() or sha256_file(source) != str(context.get("source_sha256") or ""):
        raise CriticDecisionError("frozen Story applicability SHA drift")
    actual = frozen_applicability_context(source.parent.parent)
    if actual != context:
        raise CriticDecisionError("frozen Story applicability context changed")
    return actual


def fixture_shadow_smoke() -> dict[str, Any]:
    """Run a deterministic synthetic comparison; this is not a real-model result."""
    shadow = {
        "decision": "ACCEPT_CANDIDATE",
        "issue_codes": [],
        "severity": "LOW",
        "repair_scope": [],
        "evidence": ["fixture: all frozen Story Semantic checks satisfied"],
    }
    existing = {"decision": "PASS", "summary": {"passed": True}, "issue_codes": []}
    comparison = compare_with_existing_review(shadow, existing)
    reflection = bounded_reflection_step("ACCEPT_CANDIDATE", critic_attempt=1, auto_repairs_used=0)
    return {
        "status": "PASS" if comparison["decision_equivalent"] else "FAIL",
        "fixture_only": True,
        "model_execution": False,
        "critic_invoked": False,
        "telemetry_complete": False,
        "decision": shadow["decision"],
        **comparison,
        "reflection": reflection,
        "repair_invoked": reflection["repair_invoked"],
        "authority_write": False,
        "episode_transition": False,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_immutable_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    try:
        with path.open("xb") as handle:
            handle.write(encoded)
    except FileExistsError:
        if path.read_bytes() != encoded:
            raise CriticDecisionError(f"immutable Critic evidence already exists with different content: {path}")
    return hashlib.sha256(encoded).hexdigest()


def build_decision_prompt(*, attempt: int, story_text: str, storyboard_text: str,
                          rubric_text: str, applicability: dict[str, Any]) -> str:
    """Build one frozen, decision-only input capsule for the Story Critic."""
    applicability = verify_applicability_context(applicability)
    if applicability["anomaly_applicable"]:
        applicability_rules = """APPLICABILITY: the frozen contract says anomaly rules apply.
- Enforce the supplied anomaly mechanism, trigger, direct response and consequence requirements.
- Also check general story causality, continuity, payoff, and storyboard information gain.
"""
    else:
        applicability_rules = """APPLICABILITY: the frozen contract says this is explicitly non-anomaly Story.
- Do NOT require a core anomaly, abnormal response, anomaly trigger, or anomaly propagation_core.
- Do NOT invent horror, mystery, investigation, paranormal behavior, or an abnormal response to satisfy generic rubric language.
- Continue checking ordinary causal integrity: actions need plausible consequences; causal gaps and contradictions remain valid issues.
- Apply general character motivation, continuity, structure, payoff, and storyboard information-gain checks where relevant.
"""
    applicability_record = json.dumps(applicability, ensure_ascii=False, sort_keys=True)
    return f"""You are the bounded Story Semantic Critic shadow for review attempt {attempt}.
Evaluate only the frozen Story and Storyboard plus the supplied StoryOS rubric excerpts.
Do not search the repository, call tools, rewrite the Story, or inspect producer scratch.
Return exactly one decision object matching the supplied JSON Schema. No Markdown or prose.
Allowed decisions: ACCEPT_CANDIDATE, REPAIR, NEEDS_USER, BLOCK.
Use REPAIR only for a concrete, scoped semantic defect; NEEDS_USER for ambiguity requiring a human;
BLOCK for invalid/missing frozen input or an unresolvable contract problem.
Evidence must be short, source-grounded observations. Do not expose chain-of-thought.
Do not claim StoryOS Gate PASS. Do not write telemetry, receipt, execution, authority, or state fields.
Do not propose changes outside repair_scope. A decision is advisory and cannot alter the existing review.

<FROZEN_APPLICABILITY_CONTRACT source-sha256="{applicability['source_sha256']}">
{applicability_record}
</FROZEN_APPLICABILITY_CONTRACT>

{applicability_rules}

<FROZEN_STORY>
{story_text}
</FROZEN_STORY>

<FROZEN_STORYBOARD>
{storyboard_text}
</FROZEN_STORYBOARD>

<FROZEN_STORY_SEMANTIC_RUBRIC>
{rubric_text}
</FROZEN_STORY_SEMANTIC_RUBRIC>
"""


def decision_from_existing_review(review: Any) -> str:
    """Project the existing Story Review result into the shared decision vocabulary."""
    if not isinstance(review, dict):
        return "BLOCK"
    summary = review.get("summary")
    if not isinstance(summary, dict):
        return "BLOCK"
    issue_codes = review.get("issue_codes")
    if not isinstance(issue_codes, list):
        return "BLOCK"
    # Persisted Story Review payloads may omit the repository row's decision
    # column when projected back to a document. The frozen canonical payload's
    # summary.passed is the review result in that case.
    decision = review.get("decision")
    if decision is None and type(summary.get("passed")) is bool:
        decision = "PASS" if summary.get("passed") is True else "FAIL"
    if decision == "PASS" and summary.get("passed") is True:
        if not issue_codes:
            return "ACCEPT_CANDIDATE"
        return "REPAIR"
    if decision == "FAIL" or summary.get("passed") is False:
        return "REPAIR"
    return "BLOCK"


def compare_with_existing_review(shadow_payload: Any, existing_review: Any) -> dict[str, Any]:
    shadow = validate_decision(shadow_payload)
    existing = decision_from_existing_review(existing_review)
    existing_issues = sorted({
        str(value).strip() for value in (existing_review.get("issue_codes") or [])
        if isinstance(value, str) and value.strip()
    }) if isinstance(existing_review, dict) else []
    critic_issues = sorted(set(shadow["issue_codes"]))
    intersection = sorted(set(existing_issues) & set(critic_issues))
    critic_accept = shadow["decision"] == "ACCEPT_CANDIDATE"
    existing_accept = existing == "ACCEPT_CANDIDATE"
    return {
        "shadow_decision": shadow["decision"],
        "existing_review_decision": existing,
        "decision_equivalent": shadow["decision"] == existing,
        "decision_disagreement": shadow["decision"] != existing,
        "existing_issue_codes": existing_issues,
        "critic_issue_codes": critic_issues,
        "issue_intersection": intersection,
        "critic_extra_issues": sorted(set(critic_issues) - set(existing_issues)),
        "critic_missing_issues": sorted(set(existing_issues) - set(critic_issues)),
        "existing_accept": existing_accept,
        "critic_accept": critic_accept,
        "issue_disagreement": existing_issues != critic_issues,
        "shadow_is_advisory": True,
        "gate_pass": False,
        "authority_write": False,
        "episode_transition": False,
    }


def bounded_reflection_step(
    decision: Any, *, critic_attempt: int, auto_repairs_used: int
) -> dict[str, Any]:
    """Return a capped recommendation; never dispatches a repair or retries itself."""
    if decision not in DECISIONS:
        raise CriticDecisionError("unknown critic decision")
    if type(critic_attempt) is not int or critic_attempt not in {1, 2}:
        raise CriticDecisionError("critic_attempt must be 1 or 2")
    if type(auto_repairs_used) is not int or auto_repairs_used not in {0, 1}:
        raise CriticDecisionError("auto_repairs_used must be 0 or 1")
    if decision == "ACCEPT_CANDIDATE":
        action = "REVIEW_COMPLETE_ADVISORY"
    elif decision == "REPAIR" and critic_attempt == 1 and auto_repairs_used == 0:
        action = "PROPOSE_ONE_TARGETED_REPAIR"
    elif decision == "REPAIR":
        action = "NEEDS_USER"
    elif decision == "NEEDS_USER":
        action = "NEEDS_USER"
    else:
        action = "BLOCK"
    return {
        "action": action,
        "critic_attempt": critic_attempt,
        "max_review_attempts": 2,
        "auto_repairs_used": auto_repairs_used,
        "max_auto_repairs": 1,
        "repair_invoked": False,
        "gate_pass": False,
        "episode_transition": False,
    }


def prepare_shadow_request(
    episode_dir: Path,
    *,
    attempt: int,
    review_attempt: int | None = None,
    prompt: str,
    story_path: Path,
    storyboard_path: Path,
    rubric_paths: list[Path] | None = None,
    applicability_context: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Freeze a decision-only isolated host request; shadow candidate is runtime evidence."""
    cfg = adapter_config()
    if cfg.get("shadow_enabled") is not True:
        return None
    if cfg.get("production_enabled") is True:
        raise CriticDecisionError("Critic shadow cannot run while production is enabled")
    if not isinstance(prompt, str) or not prompt.strip():
        raise CriticDecisionError("shadow critic prompt is required")
    context = verify_applicability_context(applicability_context)
    ep = Path(episode_dir).resolve()
    sources = [Path(story_path).resolve(), Path(storyboard_path).resolve(),
               *[Path(value).resolve() for value in (list(RUBRIC_PATHS) if rubric_paths is None else rubric_paths)]]
    source_hashes = {}
    for path in sources:
        try:
            source_key = path.relative_to(ROOT).as_posix()
        except ValueError:
            source_key = path.as_posix()  # fixture seams may supply isolated temp sources
        source_hashes[source_key] = sha256_file(path)
    story_hash = sha256_file(Path(story_path))
    storyboard_hash = sha256_file(Path(storyboard_path))
    metadata = {
        "kind": REQUEST_KIND,
        "shadow_only": True,
        "candidate_authority": "runtime_evidence_only",
        "review_attempt": int(review_attempt if review_attempt is not None else attempt),
        "critic_attempt": attempt,
        "source_sha256": hashlib.sha256(json.dumps(source_hashes, sort_keys=True).encode("utf-8")).hexdigest(),
        "story_sha256": story_hash,
        "storyboard_sha256": storyboard_hash,
        "decision_schema_sha256": sha256_file(SCHEMA_PATH),
        "execution_domain": "STORY_SEMANTIC_CRITIC_SHADOW",
        "applicability_context": context,
    }
    candidate_path = ep / "meta/runtime/agent-shadow/story-semantic-critic" / f"attempt-{attempt}-decision.json"
    snapshot_path = candidate_path.with_name(f"attempt-{attempt}-request-snapshot.json")
    metadata["request_snapshot_path"] = snapshot_path.resolve().relative_to(ROOT.resolve()).as_posix()
    request = product_review_adapter.prepare(
        ep,
        kind=REQUEST_KIND,
        runtime="WORK",
        attempt=attempt,
        prompt=prompt,
        source_paths=sources,
        candidate_path=candidate_path,
        host_execution="codex_user_runner_shadow",
        request_metadata=metadata,
    )
    request["shadow_only"] = True
    request["candidate_authority"] = "runtime_evidence_only"
    request["critic_invoked"] = False
    snapshot = {"schema_version": 1, "request": request}
    snapshot_sha = _write_immutable_json(snapshot_path, snapshot)
    request["request_snapshot_path"] = snapshot_path.resolve().relative_to(ROOT.resolve()).as_posix()
    request["request_snapshot_sha256"] = snapshot_sha
    return request


def finalize_shadow_candidate(
    episode_dir: Path,
    *,
    attempt: int,
    runner_result: Any = None,
    provider: str = "",
    model: str = "",
    authority_capsule_read_once: bool = False,
) -> dict[str, Any]:
    """Verify a host response against the frozen Product Review request and return advisory evidence."""
    cfg = adapter_config()
    if cfg.get("shadow_enabled") is not True or cfg.get("production_enabled") is True:
        raise CriticDecisionError("Story Semantic Critic shadow is not active")
    ep = Path(episode_dir).resolve()
    candidate_path = ep / "meta/runtime/agent-shadow/story-semantic-critic" / f"attempt-{attempt}-decision.json"
    payload, provenance = product_review_adapter.finalize_candidate(
        ep,
        kind=REQUEST_KIND,
        runtime="WORK",
        attempt=attempt,
        candidate_path=candidate_path,
    )
    decision = validate_decision(payload)
    telemetry = execution_telemetry(
        runner_result,
        provider=provider,
        model=model,
        authority_capsule_read_once=authority_capsule_read_once,
    )
    return {
        "decision": decision,
        "critic_provenance": provenance,
        "critic_invoked": True if telemetry["real_model_execution"] else None,
        "telemetry_complete": telemetry["complete"],
        "model_execution": telemetry,
        "reflection_round": attempt,
        "repair_invoked": False,
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
    }


def execution_telemetry(
    runner_result: Any,
    *,
    provider: str,
    model: str,
    authority_capsule_read_once: bool = False,
) -> dict[str, Any]:
    """Normalize only real Codex JSONL usage plus the user-runner receipt."""
    if runner_result is None:
        return {
            "real_model_execution": False,
            "wall_seconds": None,
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
            "reasoning_output_tokens": None,
            "repeated_reads": None,
            "failure": None,
            "timeout": None,
            "provider": str(provider or "") or None,
            "model": str(model or "") or None,
            "telemetry_source": None,
            "complete": False,
        }
    import codex_execution_telemetry

    telemetry = codex_execution_telemetry.model_execution(
        runner_result,
        provider=provider,
        model=model,
        authority_capsule_read_once=authority_capsule_read_once,
    )
    telemetry["complete"] = all(
        telemetry.get(key) is not None
        for key in (
            "wall_seconds", "input_tokens", "cached_input_tokens", "output_tokens",
            "reasoning_output_tokens", "failure", "timeout",
            "returncode", "telemetry_source",
        )
    ) and bool(telemetry.get("provider")) and bool(telemetry.get("model")) and bool(telemetry.get("real_model_execution"))
    return telemetry


def configured_cli_model() -> tuple[str | None, str | None]:
    """Read only the active Codex model/effort selectors; never return config contents."""
    try:
        import codex_user_runner
        home, _source = codex_user_runner.codex_home()
        config_path = home / "config.toml"
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        model = str(data.get("model") or "").strip() or None
        effort = str(data.get("model_reasoning_effort") or "").strip() or None
        return model, effort
    except Exception:
        return None, None


def execute_shadow_request(
    episode_dir: Path,
    *,
    attempt: int,
    review_attempt: int | None = None,
    timeout: int,
    existing_review: dict[str, Any],
) -> dict[str, Any]:
    """Execute the persisted shadow Host Request using the existing Codex critic runner."""
    import codex_critic_runner
    import product_review_adapter
    import story_review

    ep = Path(episode_dir).resolve()
    request_path = product_review_adapter.request_path(ep, REQUEST_KIND, attempt=attempt)
    request = product_review_adapter._read_json(request_path)
    if request.get("status") != product_review_adapter.AWAITING:
        raise CriticDecisionError("Critic shadow Host Request is not awaiting execution")
    if request.get("host_execution") != "codex_user_runner_shadow":
        raise CriticDecisionError("Critic shadow Host Request has the wrong Host execution contract")
    metadata = request.get("request_metadata") if isinstance(request.get("request_metadata"), dict) else {}
    if metadata.get("shadow_only") is not True or metadata.get("candidate_authority") != "runtime_evidence_only":
        raise CriticDecisionError("Critic shadow Host Request is missing advisory-only metadata")
    applicability = verify_applicability_context(metadata.get("applicability_context"))
    bound_review_attempt = int(review_attempt if review_attempt is not None else metadata.get("review_attempt") or 0)
    if metadata.get("critic_attempt") != attempt or metadata.get("review_attempt") != bound_review_attempt:
        raise CriticDecisionError("Critic Host Request attempt binding mismatch")
    snapshot_rel = str(metadata.get("request_snapshot_path") or "")
    snapshot_path = (ROOT / snapshot_rel).resolve()
    try:
        snapshot_path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise CriticDecisionError("Critic request evidence escapes repository") from exc
    if not snapshot_path.is_file():
        raise CriticDecisionError("immutable Critic request snapshot is missing")
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise CriticDecisionError("immutable Critic request snapshot is invalid") from exc
    frozen_request = snapshot.get("request") if isinstance(snapshot, dict) else None
    if not isinstance(frozen_request, dict) or any(
        frozen_request.get(key) != request.get(key)
        for key in ("request_id", "request_fingerprint", "prompt_sha256", "source_files", "candidate_path")
    ):
        raise CriticDecisionError("Critic request differs from its immutable evidence snapshot")
    for row in request.get("source_files") or []:
        source = (ROOT / str(row.get("path") or "")).resolve()
        if not source.is_file() or sha256_file(source).lower() != str(row.get("sha256") or "").lower():
            raise CriticDecisionError(f"Critic frozen source is stale: {row.get('path')}")
    candidate = (ROOT / str(request.get("candidate_path") or "")).resolve()
    if candidate.exists():
        raise CriticDecisionError("Critic candidate already exists; duplicate dispatch rejected")
    sources = [ROOT / str(row["path"]) for row in request.get("source_files") or []]
    story_text = sources[0].read_text(encoding="utf-8-sig")
    storyboard_text = sources[1].read_text(encoding="utf-8-sig")
    applicability_path = str(applicability["source_path"])
    rubric_text = "\n\n".join(
        path.read_text(encoding="utf-8-sig") for path in sources[2:]
        if path.resolve().relative_to(ROOT.resolve()).as_posix() != applicability_path
    )
    prompt = build_decision_prompt(attempt=attempt, story_text=story_text,
                                   storyboard_text=storyboard_text, rubric_text=rubric_text,
                                   applicability=applicability)
    model, effort = configured_cli_model()
    if not model or not effort:
        raise CriticDecisionError("active Codex model/reasoning effort is not observable")
    execution_target = codex_critic_runner.effective_execution_target(
        task_type="story_semantic_critic",
        legacy_target={"provider": "codex_user_runner", "model": model, "runtime": "CODEX"},
        route_decision=request.get("capability_route_decision"),
    )
    model = execution_target["model"]
    codex = codex_critic_runner.resolve_codex(None)
    log_path = candidate.parent / f"attempt-{attempt}-codex.jsonl"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    before_story = sha256_file(sources[0])
    before_board = sha256_file(sources[1])
    result = codex_critic_runner.launch(
        prompt,
        codex=codex,
        root=ROOT,
        timeout=timeout,
        output_path=candidate,
        output_schema=SCHEMA_PATH,
        model=model,
        reasoning_effort=effort,
        sandbox="read-only",
        log_path=log_path,
        execution_target=execution_target,
    )
    telemetry = execution_telemetry(
        result,
        provider="codex_user_runner",
        model=model,
        authority_capsule_read_once=True,
    )
    if result.returncode != 0:
        raise CriticDecisionError(f"Critic model failed with returncode={result.returncode}")
    if sha256_file(sources[0]) != before_story or sha256_file(sources[1]) != before_board:
        raise CriticDecisionError("Critic modified frozen Story or Storyboard")
    finalized = finalize_shadow_candidate(
        ep, attempt=attempt, runner_result=result,
        provider=execution_target["provider"], model=model, authority_capsule_read_once=True,
    )
    comparison = compare_with_existing_review(finalized["decision"], existing_review)
    existing_attempt = int((existing_review.get("revision_count") or 0) + 1)
    if existing_attempt != bound_review_attempt:
        raise CriticDecisionError("review_attempt does not match the frozen Existing Story Review")
    decision = finalized["decision"]
    reflection = bounded_reflection_step(decision["decision"], critic_attempt=attempt, auto_repairs_used=0)
    telemetry_path = candidate.with_name(f"attempt-{attempt}-telemetry-evidence.json")
    telemetry_evidence = {
        "schema_version": 1,
        "kind": "story_semantic_critic_shadow_telemetry_evidence",
        "request_id": request.get("request_id"),
        "request_snapshot_path": snapshot_rel,
        "request_snapshot_sha256": sha256_file(snapshot_path),
        "candidate_path": candidate.resolve().relative_to(ROOT).as_posix(),
        "candidate_sha256": sha256_file(candidate),
        "model_execution": telemetry,
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
    }
    telemetry_sha = _write_immutable_json(telemetry_path, telemetry_evidence)
    return {
        "request_id": request.get("request_id"),
        "request_path": request_path.resolve().relative_to(ROOT).as_posix(),
        "candidate_path": candidate.resolve().relative_to(ROOT).as_posix(),
        "candidate_sha256": sha256_file(candidate),
        "request_snapshot_path": snapshot_rel,
        "request_snapshot_sha256": sha256_file(snapshot_path),
        "applicability_context": applicability,
        "telemetry_evidence_path": log_path.resolve().relative_to(ROOT).as_posix(),
        "telemetry_evidence_sha256": sha256_file(log_path) if log_path.is_file() else None,
        "telemetry_receipt_evidence_path": telemetry_path.resolve().relative_to(ROOT).as_posix(),
        "telemetry_receipt_evidence_sha256": telemetry_sha,
        "decision": decision,
        **comparison,
        "issue_disagreement": decision.get("issue_codes") != list(existing_review.get("issue_codes") or []),
        "existing_issue_codes": list(existing_review.get("issue_codes") or []),
        "critic_issue_codes": decision["issue_codes"],
        "decision_schema_valid": True,
        "model_execution": telemetry,
        "telemetry_complete": telemetry["complete"],
        "critic_invoked": telemetry["real_model_execution"],
        "reflection": reflection,
        "repair_invoked": False,
        "authority_write": False,
        "gate_pass": False,
        "episode_transition": False,
        "allowed_tools_empty": telemetry.get("tool_free") is True,
    }


def load_decision(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CriticDecisionError(f"critic decision JSON invalid: {exc}") from exc
    return validate_decision(payload)
