"""Deterministic, advisory task capability routing for Runtime Router.

This module proposes execution targets only. Runtime Scheduler remains the only
runnable owner and callers retain the legacy dispatch in Shadow mode.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import re
import shutil
import threading
import time
from pathlib import Path
from typing import Iterable

import storyos_config

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_VERSION = "p4-capability-registry-v1"
SHADOW_ENABLED = True
PRODUCTION_ENABLED = False
HEALTH_TTL_SECONDS = 300
MAX_FALLBACK_DEPTH = 3


def _sha(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _utc(value: dt.datetime | None = None) -> dt.datetime:
    current = value or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        raise ValueError("health timestamps must include a timezone")
    return current.astimezone(dt.timezone.utc)


@dataclasses.dataclass(frozen=True)
class CapabilityRouteRequest:
    request_id: str
    task_type: str
    execution_domain: str
    stage: str
    agent: str
    required_capabilities: tuple[str, ...] = ()
    optional_capabilities: tuple[str, ...] = ()
    forbidden_capabilities: tuple[str, ...] = ()
    preferred_provider: str | None = None
    preferred_model: str | None = None
    fallback_allowed: bool = True
    latency_class: str = "normal"
    cost_class: str = "default"
    reasoning_requirement: str | None = "medium"
    multimodal_required: bool = False
    tools_allowed: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.request_id):
            raise ValueError("request_id must be a safe 1-128 character evidence key")
        if not self.task_type.strip():
            raise ValueError("task_type is required")
        if set(self.required_capabilities) & set(self.forbidden_capabilities):
            raise ValueError("a capability cannot be both required and forbidden")

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ModelCapability:
    provider: str
    model: str | None
    execution_runtime: str
    capabilities: frozenset[str]
    reasoning_levels: tuple[str, ...]
    telemetry: bool
    schema_output: bool
    subscription_available: bool | None
    source: str

    def to_dict(self) -> dict:
        value = dataclasses.asdict(self)
        value["capabilities"] = sorted(self.capabilities)
        return value


@dataclasses.dataclass(frozen=True)
class HealthRecord:
    provider: str
    model: str
    status: str
    observed_at: str
    expires_at: str
    ttl_seconds: int
    reason: str
    source: str

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


class HealthCache:
    """Thread-safe process-local health facts. Expired records become UNKNOWN."""

    def __init__(self, ttl_seconds: int = HEALTH_TTL_SECONDS):
        if int(ttl_seconds) < 1:
            raise ValueError("health TTL must be positive")
        self.ttl_seconds = int(ttl_seconds)
        self._rows: dict[tuple[str, str], HealthRecord] = {}
        self._lock = threading.RLock()

    def record(self, provider: str, model: str, status: str, *, reason: str,
               source: str, observed_at: dt.datetime | None = None,
               ttl_seconds: int | None = None) -> HealthRecord:
        status = str(status).upper()
        if status not in {"HEALTHY", "DEGRADED", "UNAVAILABLE", "UNKNOWN"}:
            raise ValueError(f"unsupported health status: {status}")
        ttl = self.ttl_seconds if ttl_seconds is None else int(ttl_seconds)
        if ttl < 1:
            raise ValueError("health TTL must be positive")
        observed = _utc(observed_at)
        row = HealthRecord(
            provider=str(provider), model=str(model), status=status,
            observed_at=observed.isoformat(timespec="seconds"),
            expires_at=(observed + dt.timedelta(seconds=ttl)).isoformat(timespec="seconds"),
            ttl_seconds=ttl, reason=str(reason), source=str(source),
        )
        with self._lock:
            self._rows[(row.provider, row.model)] = row
        return row

    def get(self, provider: str, model: str, *, now: dt.datetime | None = None) -> HealthRecord:
        key = (str(provider), str(model))
        current = _utc(now)
        with self._lock:
            row = self._rows.get(key)
        if row is None:
            return HealthRecord(key[0], key[1], "UNKNOWN", "", "", self.ttl_seconds,
                                "no unexpired health evidence", "none")
        if current >= _utc(dt.datetime.fromisoformat(row.expires_at)):
            return dataclasses.replace(row, status="UNKNOWN", reason="health evidence expired")
        return row

    def snapshot(self, *, now: dt.datetime | None = None) -> list[dict]:
        current = _utc(now)
        with self._lock:
            keys = sorted(self._rows)
        return [self.get(provider, model, now=current).to_dict() for provider, model in keys]


_CONFIG_PATH = ROOT / "config/storyos.yaml"
_POLICY = {
    "selection_order": ["required", "forbidden", "health", "task_policy", "preference", "fallback_order"],
    "fallback_order": ["WORK", "codex_user_runner", "codex_cli_subscription"],
    "max_fallback_depth": MAX_FALLBACK_DEPTH,
    "unknown_health_selectable": True,
    "degraded_health_selectable": False,
    "task_types": {
        "critic": {"required": ["text_input", "structured_output"],
                   "forbidden": ["image_generation", "write_tools"]},
        "story_semantic_critic": {"required": ["text_input", "structured_output"],
                                  "forbidden": ["image_generation", "write_tools"]},
        "preimage_semantic_critic": {"required": ["text_input", "structured_output"],
                                     "forbidden": ["image_generation", "write_tools"]},
        "final_semantic_critic": {"required": ["text_input", "image_input", "structured_output"],
                                  "forbidden": ["image_generation", "write_tools"]},
        "text_generation": {"required": ["text_input"], "forbidden": ["image_generation"]},
        "multimodal_review": {"required": ["text_input", "image_input", "structured_output"],
                              "forbidden": ["image_generation", "write_tools"]},
    },
}
_PROCESS_HEALTH_CACHE: HealthCache | None = None
_PROCESS_HEALTH_LOCK = threading.RLock()
_ROUTER_CONFIG_CACHE: tuple[int, int, dict] | None = None
_ROUTER_CONFIG_LOCK = threading.RLock()


def _configured_codex_model() -> tuple[str, str] | None:
    """Read only the active CLI model selectors; never starts Codex or reads secrets."""
    try:
        import codex_user_runner
        import tomllib

        home, _source = codex_user_runner.codex_home()
        config = tomllib.loads((home / "config.toml").read_text(encoding="utf-8"))
        model = str(config.get("model") or "").strip()
        effort = str(config.get("model_reasoning_effort") or "").strip().lower()
        if model and effort in {"low", "medium", "high", "xhigh", "max"}:
            return model, effort
    except Exception:
        return None
    return None


def build_registry(*, cli_model: tuple[str, str] | None = None) -> tuple[ModelCapability, ...]:
    """Build an immutable registry from current StoryOS model configuration and real producers."""
    config = storyos_config.load_config()
    text_model = str(storyos_config.get_path(config, "runtime.review.text.model") or "") or None
    rows = [
        ModelCapability(
            "WORK", text_model, "WORK",
            frozenset({"text_input", "structured_output", "schema_output", "read_only_mode"}),
            (), True, True, None, "config/storyos.yaml:runtime.review.text + runtime.workspace; model and reasoning level are host-selected",
        ),
    ]
    selected = cli_model if cli_model is not None else _configured_codex_model()
    if selected:
        model, effort = selected
        codex_capabilities = {"text_input", "image_input", "structured_output", "schema_output",
                              "tool_use", "read_only_mode"}
        if effort in {"high", "xhigh", "max"}:
            codex_capabilities.add("high_reasoning")
        rows.append(ModelCapability(
            "codex_user_runner", model, "CODEX",
            frozenset(codex_capabilities),
            tuple(dict.fromkeys((effort,))),
            True, True, None, "codex_user_runner config.toml + existing read-only critic producer; availability is host supplied",
        ))
    # Registered as a real image provider for future capability work only. P4 V1
    # task policies never select image_generation.
    image_model = str(storyos_config.get_path(config, "image.model") or "gpt-image-2.5-flare")
    rows.append(ModelCapability(
        "codex_cli_subscription", image_model, "CODEX",
        frozenset({"image_generation"}), (), True, False, None,
        "config/storyos.yaml:image.model + episodes/_system/codex_subscription_image.py",
    ))
    return tuple(sorted(rows, key=lambda row: (row.provider, row.model or "", row.execution_runtime)))


def registry_sha256(registry: Iterable[ModelCapability] | None = None) -> str:
    rows = tuple(registry) if registry is not None else build_registry()
    return _sha({"version": REGISTRY_VERSION, "models": [row.to_dict() for row in rows]})


def effective_router_config(config: dict | None = None) -> dict:
    """Read the validated task-router flag from the canonical StoryOS YAML loader."""
    global _ROUTER_CONFIG_CACHE
    if config is None:
        path = storyos_config.CONFIG_PATH
        stat = path.stat()
        with _ROUTER_CONFIG_LOCK:
            if (_ROUTER_CONFIG_CACHE is not None
                    and _ROUTER_CONFIG_CACHE[:2] == (stat.st_mtime_ns, stat.st_size)):
                return dict(_ROUTER_CONFIG_CACHE[2])
            cfg = storyos_config.load_config()
            resolved = _router_config_values(cfg)
            resolved["config_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            _ROUTER_CONFIG_CACHE = (stat.st_mtime_ns, stat.st_size, resolved)
            return dict(resolved)
    return _router_config_values(config)


def _router_config_values(cfg: dict) -> dict:
    raw = storyos_config.get_path(cfg, "agent_runtime.task_capability_router")
    if not isinstance(raw, dict):
        raise ValueError("CONFIG_INVALID: agent_runtime.task_capability_router must be a mapping")
    allowed = {"story_semantic_critic", "preimage_semantic_critic", "final_semantic_critic"}
    tasks = raw.get("supported_task_types")
    if (not isinstance(tasks, list) or not tasks or len(tasks) != len(set(tasks))
            or any(not isinstance(task, str) or task not in allowed for task in tasks)):
        raise ValueError("CONFIG_INVALID: invalid task capability router allowlist")
    return {
        "shadow_enabled": raw.get("shadow_enabled") is True,
        "production_enabled": raw.get("production_enabled") is True,
        "health_ttl_seconds": int(raw["health_ttl_seconds"]),
        "max_fallback_depth": int(raw["max_fallback_depth"]),
        "policy_mode": raw.get("policy_mode"),
        "supported_task_types": tuple(tasks),
        "config_sha256": _sha(cfg),
    }


def process_health_cache() -> HealthCache:
    """Return the immutable-snapshot, lock-protected process health cache."""
    global _PROCESS_HEALTH_CACHE
    cfg = effective_router_config()
    with _PROCESS_HEALTH_LOCK:
        if _PROCESS_HEALTH_CACHE is None or _PROCESS_HEALTH_CACHE.ttl_seconds != cfg["health_ttl_seconds"]:
            _PROCESS_HEALTH_CACHE = HealthCache(cfg["health_ttl_seconds"])
        return _PROCESS_HEALTH_CACHE


def policy_sha256(config: dict | None = None, *, allowed_providers: tuple[str, ...] | None = None) -> str:
    cfg = effective_router_config(config)
    return _sha({"mode": cfg["policy_mode"], "max_fallback_depth": cfg["max_fallback_depth"],
                 "supported_task_types": list(cfg["supported_task_types"]), "policy": _POLICY,
                 "allowed_providers": sorted(allowed_providers) if allowed_providers is not None else None})


def _candidate_order(request: CapabilityRouteRequest, registry: tuple[ModelCapability, ...]) -> list[ModelCapability]:
    rank = {name: index for index, name in enumerate(_POLICY["fallback_order"])}
    ordered = sorted(registry, key=lambda row: (
        0 if row.provider == request.preferred_provider else 1,
        0 if row.model == request.preferred_model else 1,
        rank.get(row.provider, len(rank)), row.provider, row.model or "",
    ))
    # A malformed or duplicated registry row must not make a fallback visit the
    # same provider/model more than once. Preserve deterministic first occurrence.
    unique: list[ModelCapability] = []
    visited: set[tuple[str, str | None, str]] = set()
    for row in ordered:
        key = (row.provider, row.model, row.execution_runtime)
        if key in visited:
            continue
        visited.add(key)
        unique.append(row)
    return unique


def resolve(request: CapabilityRouteRequest, *, registry: Iterable[ModelCapability] | None = None,
            health: HealthCache | None = None,
            now: dt.datetime | None = None, allowed_providers: tuple[str, ...] | None = None) -> dict:
    started = time.perf_counter()
    cfg = effective_router_config()
    rows = tuple(registry) if registry is not None else build_registry()
    registry_ms = (time.perf_counter() - started) * 1000
    health = health or process_health_cache()
    health_started = time.perf_counter()
    task = task_policy(request.task_type)
    required = set(request.required_capabilities) | set(task["required"])
    forbidden = set(request.forbidden_capabilities) | set(task["forbidden"])
    optional = set(request.optional_capabilities)
    candidates = _candidate_order(request, rows)
    rejected: list[dict] = []
    eligible: list[tuple[ModelCapability, HealthRecord]] = []
    visited: set[tuple[str, str]] = set()
    candidate_visits = 0
    for model in candidates:
        key = (model.provider, model.model)
        if key in visited or candidate_visits > cfg["max_fallback_depth"]:
            rejected.append({"provider": model.provider, "model": model.model,
                             "reasons": ["fallback_cycle_or_depth_limit"]})
            continue
        visited.add(key)
        candidate_visits += 1
        if allowed_providers is not None and model.provider not in allowed_providers:
            rejected.append({"provider": model.provider, "model": model.model, "reasons": ["policy_disallowed"]})
            continue
        missing = sorted(required - model.capabilities)
        if missing:
            rejected.append({"provider": model.provider, "model": model.model,
                             "reasons": ["missing_required_capability"], "missing": missing})
            continue
        present_forbidden = sorted(forbidden & model.capabilities)
        if present_forbidden:
            rejected.append({"provider": model.provider, "model": model.model,
                             "reasons": ["forbidden_capability_present"], "present": present_forbidden})
            continue
        if request.reasoning_requirement and request.reasoning_requirement not in model.reasoning_levels:
            rejected.append({"provider": model.provider, "model": model.model,
                             "reasons": ["reasoning_level_unsupported"],
                             "required_reasoning": request.reasoning_requirement})
            continue
        if request.multimodal_required and "image_input" not in model.capabilities:
            rejected.append({"provider": model.provider, "model": model.model,
                             "reasons": ["multimodal_required"]})
            continue
        health_row = health.get(model.provider, model.model or "host-managed", now=now)
        if health_row.status in {"DEGRADED", "UNAVAILABLE"}:
            rejected.append({"provider": model.provider, "model": model.model,
                             "reasons": ["provider_unhealthy"], "health_status": health_row.status})
            if not request.fallback_allowed:
                break
            continue
        eligible.append((model, health_row))
        if request.preferred_provider == model.provider and request.preferred_model in {None, model.model}:
            break
        if not request.fallback_allowed:
            break
    health_ms = (time.perf_counter() - health_started) * 1000
    selected = eligible[0] if eligible else None
    fallback_used = bool(selected and (
        (request.preferred_provider and selected[0].provider != request.preferred_provider)
        or (request.preferred_model and selected[0].model != request.preferred_model)
    ))
    decision = {
        "request_id": request.request_id,
        "task_type": request.task_type,
        "selected_provider": selected[0].provider if selected else None,
        "selected_model": selected[0].model if selected else None,
        "selected_runtime": selected[0].execution_runtime if selected else None,
        "status": "ROUTE" if selected else "NO_ROUTE",
        "selection_reason": "preferred capability match" if selected and not fallback_used else ("bounded capability-safe fallback" if selected else "no eligible candidate"),
        "matched_required_capabilities": sorted(required & selected[0].capabilities) if selected else [],
        "matched_optional_capabilities": sorted(optional & selected[0].capabilities) if selected else [],
        "forbidden_capabilities_clear": bool(selected and not (forbidden & selected[0].capabilities)),
        "health_status": selected[1].status if selected else "UNKNOWN",
        "health_evidence": selected[1].to_dict() if selected else None,
        "fallback_used": fallback_used,
        "fallback_from": request.preferred_provider if fallback_used else None,
        "fallback_depth": min(cfg["max_fallback_depth"], max(0, len(rejected))),
        "candidate_count": len(rows),
        "rejected_candidates": rejected,
        "policy_sha256": policy_sha256(allowed_providers=allowed_providers),
        "config_sha256": effective_router_config()["config_sha256"],
        "capability_registry_version": REGISTRY_VERSION,
        "capability_registry_sha256": registry_sha256(rows),
        "health_snapshot_sha256": _sha(health.snapshot(now=now)),
        "resolve_wall_ms": round((time.perf_counter() - started) * 1000, 4),
        "registry_lookup_ms": round(registry_ms, 4),
        "health_lookup_ms": round(health_ms, 4),
        "llm_calls": 0,
        "authority_writes": 0,
    }
    return decision


def compare_shadow(request: CapabilityRouteRequest, decision: dict, *, legacy_provider: str,
                   legacy_model: str | None, legacy_runtime: str) -> dict:
    equivalent = (decision.get("selected_provider") == legacy_provider
                  and (legacy_model is None or decision.get("selected_model") == legacy_model))
    return {
        "request_id": request.request_id,
        "legacy_provider": legacy_provider,
        "legacy_model": legacy_model,
        "legacy_runtime": legacy_runtime,
        "proposed_provider": decision.get("selected_provider"),
        "proposed_model": decision.get("selected_model"),
        "proposed_runtime": decision.get("selected_runtime"),
        "would_select": {"provider": decision.get("selected_provider"), "model": decision.get("selected_model")},
        "route_equivalent": equivalent,
        "reason": decision.get("selection_reason"),
        "capability_match": decision.get("status") == "ROUTE" and decision.get("forbidden_capabilities_clear") is True,
        "health_match": decision.get("status") == "ROUTE"
                        and decision.get("health_status") not in {"DEGRADED", "UNAVAILABLE"},
        "fallback_needed": decision.get("fallback_used") is True,
        "actual_dispatch": {"provider": legacy_provider, "model": legacy_model, "runtime": legacy_runtime},
        "actual_dispatch_unchanged": True,
    }


def _write_immutable(path: Path, payload: dict) -> str:
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError(f"capability route evidence conflict: {path}")
    return hashlib.sha256(raw).hexdigest()


def observe_shadow(request: CapabilityRouteRequest, *, legacy_provider: str,
                   legacy_model: str | None, legacy_runtime: str, registry=None,
                   health: HealthCache | None = None, evidence_root: Path | None = None,
                   now: dt.datetime | None = None) -> dict:
    """Persist one immutable, idempotent observation; never alters dispatch."""
    decision = resolve(request, registry=registry, health=health, now=now)
    comparison = compare_shadow(request, decision, legacy_provider=legacy_provider,
                                legacy_model=legacy_model, legacy_runtime=legacy_runtime)
    record = {"schema_version": 1, "kind": "p4_capability_router_shadow", "request": request.to_dict(),
              "decision": decision, "comparison": comparison,
              "actual_dispatch_unchanged": True}
    root = Path(evidence_root) if evidence_root is not None else ROOT / ".storyos/p4-capability-router"
    record["request_sha256"] = _sha(record["request"])
    record["decision_sha256"] = _sha(decision)
    record["comparison_sha256"] = _sha(comparison)
    path = root / f"{request.request_id}.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if existing.get("request_sha256") != record["request_sha256"]:
            raise ValueError(f"capability request id reused with different input: {path}")
        old_decision = existing.get("decision") or {}
        new_decision = record.get("decision") or {}
        for binding in ("policy_sha256", "config_sha256", "capability_registry_sha256", "health_snapshot_sha256"):
            if old_decision.get(binding) != new_decision.get(binding):
                raise ValueError(f"capability request id reused with changed {binding}: {path}")
        return {**existing, "evidence_path": str(path), "evidence_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    digest = _write_immutable(path, record)
    return {**record, "evidence_path": str(path), "evidence_sha256": digest}


def critic_route_request(*, request_id: str, kind: str, stage: str, host_execution: str,
                         legacy_provider: str, legacy_model: str | None) -> tuple[CapabilityRouteRequest, str, str | None, str]:
    """Map the three current semantic Critic classes to deterministic requirements."""
    multimodal = "final-semantic" in kind
    preimage = "preimage-semantic" in kind
    if multimodal:
        task_type = "final_semantic_critic"
    elif preimage:
        task_type = "preimage_semantic_critic"
    else:
        task_type = "story_semantic_critic"
    required = ["text_input", "structured_output"]
    if multimodal:
        required.append("image_input")
    optional = ["schema_output", "cached_input"]
    if not preimage:
        optional.append("high_reasoning")
    request = CapabilityRouteRequest(
        request_id=request_id, task_type=task_type, execution_domain=f"{stage}:{kind}",
        stage=stage, agent=f"{kind}-critic", required_capabilities=tuple(required),
        optional_capabilities=tuple(optional),
        forbidden_capabilities=("image_generation", "write_tools"),
        preferred_provider=legacy_provider, preferred_model=legacy_model,
        fallback_allowed=True, latency_class="interactive", cost_class="subscription",
        reasoning_requirement=None,
        multimodal_required=multimodal, tools_allowed=False,
    )
    return request, legacy_provider, legacy_model, "CODEX" if host_execution == "codex_user_runner_shadow" else "WORK"


def resolve_effective_route(request: CapabilityRouteRequest, *, legacy_provider: str,
                            legacy_model: str | None, legacy_runtime: str,
                            registry: Iterable[ModelCapability] | None = None,
                            health: HealthCache | None = None,
                            now: dt.datetime | None = None,
                            config: dict | None = None) -> dict:
    """Resolve the approved guarded production policy; this returns a route only."""
    started = time.perf_counter()
    cfg = effective_router_config(config)
    rows = tuple(registry) if registry is not None else build_registry()
    health = health or process_health_cache()
    request_policy = _POLICY["task_types"].get(request.task_type, {"required": [], "forbidden": []})
    required = set(request.required_capabilities) | set(request_policy["required"])
    forbidden = set(request.forbidden_capabilities) | set(request_policy["forbidden"])
    optional = set(request.optional_capabilities)
    health_rows = health.snapshot(now=now)
    health_sha = _sha(health_rows)
    registry_sha = registry_sha256(rows)

    legacy_rows = [row for row in rows if row.provider == legacy_provider
                   and (legacy_model is None or row.model == legacy_model)]
    legacy = legacy_rows[0] if legacy_rows else None
    legacy_health_model = legacy_model or "host-managed"
    legacy_health = health.get(legacy_provider, legacy_health_model, now=now)
    missing = sorted(required - set(legacy.capabilities)) if legacy else sorted(required)
    present_forbidden = sorted(forbidden & set(legacy.capabilities)) if legacy else []
    legacy_contract_valid = legacy is not None and not missing and not present_forbidden
    reason = ""
    action = "KEEP_LEGACY"
    selected = legacy
    warning = None
    fallback_used = False
    rejected: list[dict] = []

    def fresh_healthy(row: ModelCapability) -> bool:
        evidence = health.get(row.provider, row.model or "host-managed", now=now)
        return evidence.status == "HEALTHY" and bool(evidence.observed_at) and bool(evidence.expires_at)

    def find_fallback() -> ModelCapability | None:
        if not request.fallback_allowed:
            return None
        legacy_key = (legacy.provider, legacy.model) if legacy else (legacy_provider, legacy_model)
        ordered = _candidate_order(request, rows)
        max_depth = cfg["max_fallback_depth"]
        visited: set[tuple[str, str | None, str]] = set()
        depth = 0
        for row in ordered:
            key = (row.provider, row.model, row.execution_runtime)
            if key in visited or depth >= max_depth:
                continue
            visited.add(key)
            if (row.provider, row.model) == legacy_key:
                continue
            depth += 1
            reasons = []
            if row.provider not in {"WORK", "codex_user_runner", "codex_cli_subscription"}:
                reasons.append("policy_disallowed")
            absent = sorted(required - set(row.capabilities))
            if absent:
                reasons.append("missing_required_capability")
            forbidden_present = sorted(forbidden & set(row.capabilities))
            if forbidden_present:
                reasons.append("forbidden_capability_present")
            if request.reasoning_requirement and request.reasoning_requirement not in row.reasoning_levels:
                reasons.append("reasoning_level_unsupported")
            health_row = health.get(row.provider, row.model or "host-managed", now=now)
            if health_row.status != "HEALTHY" or not fresh_healthy(row):
                reasons.append("fallback_requires_fresh_healthy")
            if reasons:
                rejected.append({"provider": row.provider, "model": row.model,
                                 "reasons": reasons, "health_status": health_row.status})
                continue
            return row
        return None

    supported = request.task_type in cfg["supported_task_types"]
    if not supported:
        action, reason = "BYPASS_ROUTER_PRODUCTION", "task type is outside the production allowlist"
        selected = legacy
    elif not cfg["production_enabled"]:
        action, reason = "KEEP_LEGACY", "production flag is disabled"
    elif legacy_contract_valid and legacy_health.status == "UNKNOWN":
        action, reason = "KEEP_LEGACY", "legacy route contract is valid; health is UNKNOWN"
        warning = "LEGACY_HEALTH_UNKNOWN"
    elif legacy_contract_valid and legacy_health.status == "HEALTHY":
        action, reason = "KEEP_LEGACY", "legacy route satisfies capability and fresh health policy"
    elif legacy_contract_valid and legacy_health.status == "DEGRADED":
        fallback = find_fallback()
        if fallback:
            action, selected, fallback_used = "FALLBACK", fallback, True
            reason = "legacy route is DEGRADED; selected fresh HEALTHY capability-safe fallback"
        else:
            action, reason = "KEEP_LEGACY", "legacy route is DEGRADED; no fresh HEALTHY fallback; defer to existing recovery"
            warning = "LEGACY_HEALTH_DEGRADED"
    elif not legacy_contract_valid or legacy_health.status == "UNAVAILABLE":
        fallback = find_fallback()
        if fallback:
            action, selected, fallback_used = "FALLBACK", fallback, True
            reason = "legacy route is capability-invalid or UNAVAILABLE; selected fresh HEALTHY fallback"
        else:
            action, selected = "NO_ROUTE", None
            reason = "no fresh HEALTHY route satisfies required and forbidden capabilities"
    else:
        action, reason = "KEEP_LEGACY", f"unrecognized legacy health state {legacy_health.status}"
        warning = "LEGACY_HEALTH_UNKNOWN"

    selected_provider = selected.provider if selected else None
    selected_model = selected.model if selected else None
    selected_runtime = selected.execution_runtime if selected else None
    result = {
        "request_id": request.request_id, "task_type": request.task_type,
        "legacy_route": {"provider": legacy_provider, "model": legacy_model, "runtime": legacy_runtime},
        "router_proposal": {"provider": selected_provider, "model": selected_model, "runtime": selected_runtime},
        "effective_action": action,
        "effective_route": {"provider": selected_provider, "model": selected_model, "runtime": selected_runtime},
        "policy_mode": cfg["policy_mode"], "production_enabled": cfg["production_enabled"],
        "supported_task": supported,
        "health_status": legacy_health.status, "health_evidence": legacy_health.to_dict(),
        "health_snapshot_sha256": health_sha, "health_observed_at": legacy_health.observed_at,
        "health_ttl_seconds": cfg["health_ttl_seconds"],
        "registry_sha256": registry_sha, "policy_sha256": policy_sha256(config),
        "config_sha256": cfg["config_sha256"], "fallback_used": fallback_used,
        "no_route": action == "NO_ROUTE", "warning": warning, "reason": reason,
        "required_capabilities": sorted(required), "optional_capabilities": sorted(optional),
        "forbidden_capabilities": sorted(forbidden), "missing_legacy_capabilities": missing,
        "rejected_candidates": rejected,
        "actual_dispatch_changed": False,
        "llm_calls": 0, "network_calls": 0, "authority_writes": 0,
        "resolve_wall_ms": round((time.perf_counter() - started) * 1000, 4),
    }
    return result


def refresh_cutover_health(*, observed_at: dt.datetime | None = None) -> dict:
    """Collect local resolution/config evidence only; never probes a model or network."""
    stamp = _utc(observed_at).isoformat(timespec="seconds")
    cfg = storyos_config.load_config()
    config_sha = _sha(cfg)
    codex_path = shutil.which("codex") or shutil.which("codex.exe")
    configured_codex = _configured_codex_model()
    rows = []
    providers = (
        ("WORK", "host-managed", bool(storyos_config.get_path(cfg, "runtime.workspace.provider")),
         "config/storyos.yaml:runtime.workspace"),
        ("codex_user_runner", configured_codex[0] if configured_codex else None,
         bool(codex_path and configured_codex),
         "codex executable resolution + existing Codex model selector configuration"),
        ("codex_cli_subscription", str(storyos_config.get_path(cfg, "image.model") or ""),
         bool(codex_path and storyos_config.get_path(cfg, "image.model")),
         "codex executable resolution + config/storyos.yaml:image.model"),
    )
    ttl = effective_router_config(cfg)["health_ttl_seconds"]
    expires = (_utc(observed_at) + dt.timedelta(seconds=ttl)).isoformat(timespec="seconds")
    process_cache = process_health_cache()
    for provider, model, resolved, source in providers:
        health_model = model or "host-managed"
        evidence = process_cache.get(provider, health_model, now=observed_at)
        effective = evidence.status
        rows.append({
            "provider": provider, "model": model or None,
            "transport_status": "CONFIGURED" if provider == "WORK" and resolved else "UNKNOWN",
            "runtime_status": "AVAILABLE" if resolved else "UNKNOWN",
            "model_status": effective, "effective_health": effective,
            "source": source if resolved else "local deterministic resolution unavailable",
            "health_evidence_source": evidence.source if effective != "UNKNOWN" else None,
            "observed_at": evidence.observed_at if effective != "UNKNOWN" else stamp,
            "expires_at": evidence.expires_at if effective != "UNKNOWN" else expires,
            "ttl_seconds": ttl, "fresh": effective != "UNKNOWN",
            "component_evidence_fresh": True,
            "llm_probe_used": False, "image_probe_used": False,
        })
    return {"providers": rows, "observed_at": stamp, "config_sha256": config_sha,
            "llm_probe_used": False, "image_probe_used": False, "network_calls": 0}


def cutover_recheck(*, gate_path: Path, p3_closure_sha256: str,
                    health_review: dict | None = None,
                    regression_smoke: dict | None = None) -> dict:
    """Preflight future cutover inputs; this function never flips the production flag."""
    cfg = effective_router_config()
    try:
        gate_raw = Path(gate_path).read_bytes()
        gate = json.loads(gate_raw.decode("utf-8-sig"))
    except (OSError, ValueError):
        return {"status": "BLOCKED", "reason": "implementation gate missing or invalid",
                "production_enabled": cfg["production_enabled"]}
    blockers = []
    if cfg["production_enabled"]:
        blockers.append("production flag must remain false during recheck")
    if not gate.get("mandatory_checks_pass"):
        blockers.append("implementation gate is not passing")
    if gate.get("p3_closure_sha256") != p3_closure_sha256:
        blockers.append("P3 closure SHA mismatch")
    try:
        import subprocess
        current_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                      capture_output=True, text=True).stdout.strip()
    except Exception:
        current_head = None
    if gate.get("head_sha") != current_head:
        blockers.append("current HEAD differs from implementation gate")
    if gate.get("config_sha256") != cfg["config_sha256"]:
        blockers.append("config SHA differs from implementation gate")
    if gate.get("registry_sha256") != registry_sha256():
        blockers.append("registry SHA differs from implementation gate")
    if gate.get("policy_sha256") != policy_sha256():
        blockers.append("policy SHA differs from implementation gate")
    smoke = regression_smoke or (gate.get("regression_smoke") if isinstance(gate.get("regression_smoke"), dict) else None)
    if not smoke or smoke.get("focused_pass") is not True or smoke.get("broad_pass") is not True:
        blockers.append("fresh regression smoke is missing or failed")
    health = health_review or refresh_cutover_health()
    unknown = any(row.get("effective_health") == "UNKNOWN" for row in health.get("providers", []))
    status = "BLOCKED" if blockers else ("CONDITIONAL" if unknown else "READY")
    return {"status": status, "blockers": blockers,
            "health_snapshot_sha256": _sha(health), "gate_sha256": hashlib.sha256(gate_raw).hexdigest(),
            "config_sha256": cfg["config_sha256"], "registry_sha256": registry_sha256(),
            "policy_sha256": policy_sha256(), "head_sha": current_head,
            "production_enabled": cfg["production_enabled"],
            "llm_probe_used": False, "image_probe_used": False}


def task_policy(task_type: str) -> dict:
    """Return a defensive copy of the deterministic built-in task policy."""
    try:
        return json.loads(json.dumps(_POLICY["task_types"][task_type]))
    except KeyError as exc:
        raise ValueError(f"unsupported capability task type: {task_type}") from exc


def record_execution_outcome(health: HealthCache, provider: str, model: str | None, *,
                             successful: bool, failure_type: str | None = None,
                             source: str = "execution_telemetry", reason: str = "",
                             observed_at: dt.datetime | None = None) -> HealthRecord:
    """Refresh TTL health from an existing runner/telemetry failure classification."""
    if successful:
        status, explanation = "HEALTHY", reason or "latest execution succeeded"
    else:
        if not failure_type:
            raise ValueError("failure_type is required for a failed execution")
        import runtime_failure_strategy
        classified = runtime_failure_strategy.resolve(failure_type)
        if classified["failure_type"] != "technical_failure":
            return health.get(provider, model or "host-managed")
        status, explanation = "DEGRADED", reason or "technical execution failure"
    return health.record(provider, model or "host-managed", status, reason=explanation, source=source,
                         observed_at=observed_at)


def self_test() -> None:
    req = CapabilityRouteRequest("self-test", "critic", "TEST", "TEST", "critic",
                                 required_capabilities=("text_input", "structured_output"),
                                 forbidden_capabilities=("image_generation",),
                                 preferred_provider="codex_user_runner",
                                 reasoning_requirement="high")
    out = resolve(req, registry=build_registry(cli_model=("gpt-5.6-luna", "high")))
    assert out["status"] == "ROUTE" and out["llm_calls"] == 0 and out["authority_writes"] == 0


if __name__ == "__main__":
    self_test()
    print("CAPABILITY ROUTER SELF-TEST PASS")
