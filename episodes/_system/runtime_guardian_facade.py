#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P5 shadow facade over existing runtime failure facts and recovery advice.

This module has no retry, scheduler, persistence, Episode-state, or authority
ownership. Callers pass facts already observed by existing runtime components.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

import runtime_failure_classifier
import runtime_failure_strategy
import storyos_config

CLASSIFICATIONS = frozenset({
    "NETWORK_TRANSIENT", "MYSQL_TRANSIENT", "JOB_TIMEOUT", "HEARTBEAT_STALE",
    "QUEUE_STUCK", "LEASE_STALE", "HOST_REQUEST_STALE", "INVALID_TRANSITION",
    "STALE_AUTHORITY", "TECHNICAL_RETRY_EXHAUSTED", "CONTENT_FAILURE", "UNKNOWN",
})
STALE_SECONDS = 300


def _parse_time(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def _age_seconds(value: Any, now: dt.datetime) -> float | None:
    parsed = _parse_time(value)
    return max(0.0, (now - parsed).total_seconds()) if parsed else None


def config() -> dict:
    cfg = storyos_config.load_config()
    errors = storyos_config.validate(cfg)
    if errors:
        return {"shadow_enabled": False, "production_enabled": False,
                "config_valid": False, "config_errors": errors}
    value = storyos_config.get_path(cfg, "agent_runtime.guardian_facade") or {}
    return {"shadow_enabled": value.get("shadow_enabled") is True,
            "production_enabled": False, "config_valid": True}


def detect(snapshot: dict, *, now: dt.datetime | None = None) -> list[dict]:
    """Detect deterministic findings from a caller-provided runtime snapshot."""
    if not isinstance(snapshot, dict):
        raise ValueError("runtime snapshot must be a mapping")
    current = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    findings: list[dict] = []

    def add(code: str, source: str, reason: str, **evidence: Any) -> None:
        findings.append({"classification": code, "source": source,
                         "reason": reason, "evidence": evidence})

    failure = snapshot.get("failure") if isinstance(snapshot.get("failure"), dict) else {}
    error_kind = str(failure.get("error_kind") or "").lower()
    note = str(failure.get("note") or failure.get("message") or "").lower()
    rc = failure.get("return_code")
    attempts = failure.get("attempt")
    max_attempts = failure.get("max_attempts")
    existing_category = str(failure.get("existing_category") or "").upper()
    if (isinstance(attempts, int) and isinstance(max_attempts, int)
            and max_attempts > 0 and attempts >= max_attempts
            and (rc not in (None, 0))):
        add("TECHNICAL_RETRY_EXHAUSTED", "runtime_failure_telemetry",
            "existing bounded retry budget is exhausted", attempt=attempts,
            max_attempts=max_attempts, return_code=rc)
    elif error_kind in {"network", "dns", "connection", "websocket"} or any(
            token in note for token in ("network", "connection", "websocket", "dns")):
        add("NETWORK_TRANSIENT", "runtime_failure_telemetry",
            "existing execution telemetry reports a network failure", return_code=rc)
    elif error_kind in {"mysql", "database", "db"} or any(
            token in note for token in ("mysql", "database", "deadlock", "lock wait timeout")):
        add("MYSQL_TRANSIENT", "runtime_failure_telemetry",
            "existing execution telemetry reports a database failure", return_code=rc)
    elif rc not in (None, 0) and ("timeout" in note or rc == 124):
        add("JOB_TIMEOUT", "runtime_failure_telemetry",
            "existing execution telemetry reports a timeout", return_code=rc)
    elif rc not in (None, 0) and (existing_category == "CONTENT_FAILED" or any(
            token in note for token in ("visual", "identity", "quality", "content", "contract"))):
        add("CONTENT_FAILURE", "runtime_failure_telemetry",
            "existing execution telemetry reports a content failure", return_code=rc)
    elif rc not in (None, 0):
        add("UNKNOWN", "runtime_failure_telemetry",
            "existing failure classifier has no deterministic specialized match", return_code=rc)

    runner = snapshot.get("runner_state") if isinstance(snapshot.get("runner_state"), dict) else {}
    heartbeat_age = _age_seconds(runner.get("heartbeat"), current)
    if runner.get("status") == "RUNNING" and heartbeat_age is not None and heartbeat_age > STALE_SECONDS:
        add("HEARTBEAT_STALE", "runner_state_store", "running runner heartbeat exceeds stale threshold",
            age_seconds=heartbeat_age, threshold_seconds=STALE_SECONDS)

    job = snapshot.get("running_job") if isinstance(snapshot.get("running_job"), dict) else {}
    job_age = _age_seconds(job.get("started_at"), current)
    timeout = job.get("timeout_seconds")
    if (job.get("status") == "RUNNING" and job_age is not None
            and isinstance(timeout, (int, float)) and timeout > 0 and job_age > timeout):
        add("JOB_TIMEOUT", "runtime_scheduler", "running job exceeded its existing timeout",
            age_seconds=job_age, timeout_seconds=timeout)

    queue = snapshot.get("queue") if isinstance(snapshot.get("queue"), dict) else {}
    progress_age = _age_seconds(queue.get("last_progress_at"), current)
    stuck_after = queue.get("stuck_after_seconds")
    if (queue.get("has_runnable_work") is True and progress_age is not None
            and isinstance(stuck_after, (int, float)) and stuck_after > 0
            and progress_age > stuck_after):
        add("QUEUE_STUCK", "runtime_scheduler", "runnable queue has made no progress",
            age_seconds=progress_age, threshold_seconds=stuck_after)

    lease = snapshot.get("lease") if isinstance(snapshot.get("lease"), dict) else {}
    lease_age = _age_seconds(lease.get("acquired_at"), current)
    lease_limit = lease.get("max_age_seconds")
    if (lease.get("active") is True and lease_age is not None
            and isinstance(lease_limit, (int, float)) and lease_limit > 0 and lease_age > lease_limit):
        add("LEASE_STALE", "existing_owner_lock", "active lease exceeds its existing age limit",
            age_seconds=lease_age, max_age_seconds=lease_limit)

    host = snapshot.get("host_request") if isinstance(snapshot.get("host_request"), dict) else {}
    host_age = _age_seconds(host.get("created_at"), current)
    host_limit = host.get("max_age_seconds")
    if (host.get("status") == "HOST_WAIT" and host_age is not None
            and isinstance(host_limit, (int, float)) and host_limit > 0 and host_age > host_limit):
        add("HOST_REQUEST_STALE", "host_request_receipt", "host request exceeds its existing age limit",
            age_seconds=host_age, max_age_seconds=host_limit)

    transition = snapshot.get("transition") if isinstance(snapshot.get("transition"), dict) else {}
    if transition.get("valid") is False:
        add("INVALID_TRANSITION", "existing_transition_validator",
            "existing transition validator rejected the transition", reason_detail=transition.get("reason"))

    authority = snapshot.get("authority") if isinstance(snapshot.get("authority"), dict) else {}
    if authority.get("stale") is True or (
            authority.get("expected_sha256") and authority.get("actual_sha256")
            and authority.get("expected_sha256") != authority.get("actual_sha256")):
        add("STALE_AUTHORITY", "existing_authority_snapshot",
            "existing authority evidence does not match its frozen snapshot")

    return findings


def classify(finding: dict) -> dict:
    """Bind Guardian's specific observation to existing classifier semantics."""
    if not isinstance(finding, dict) or finding.get("classification") not in CLASSIFICATIONS:
        code = "UNKNOWN"
    else:
        code = finding["classification"]
    reason = str(finding.get("reason") or code)
    if code == "CONTENT_FAILURE":
        evidence = finding.get("evidence") if isinstance(finding.get("evidence"), dict) else {}
        existing = runtime_failure_classifier.classify(
            int(evidence.get("return_code") or 1), "content quality failure: " + reason)
        recovery = runtime_failure_strategy.resolve("quality_failure")
        action = "NEVER_RETRY_TECH"
    elif code in {"INVALID_TRANSITION", "STALE_AUTHORITY", "TECHNICAL_RETRY_EXHAUSTED"}:
        existing = runtime_failure_classifier.classify(23, reason)
        recovery = None
        action = {"INVALID_TRANSITION": "BLOCKED_NO_FORCE_TRANSITION",
                  "STALE_AUTHORITY": "BLOCKED_REFRESH_EXISTING_AUTHORITY",
                  "TECHNICAL_RETRY_EXHAUSTED": "EXISTING_TERMINAL_STRATEGY"}[code]
    elif code == "UNKNOWN":
        evidence = finding.get("evidence") if isinstance(finding.get("evidence"), dict) else {}
        existing = runtime_failure_classifier.classify(
            int(evidence.get("return_code") or 1), reason)
        recovery = None
        action = "DIAGNOSTIC_REQUIRED"
    else:
        existing = runtime_failure_classifier.classify(21, reason)
        recovery = runtime_failure_strategy.resolve("technical_failure")
        action = {
            "NETWORK_TRANSIENT": "EXISTING_TECHNICAL_RETRY",
            "MYSQL_TRANSIENT": "EXISTING_PERSISTENCE_RECOVERY",
            "JOB_TIMEOUT": "EXISTING_SCHEDULER_TIMEOUT_HANDLING",
            "HEARTBEAT_STALE": "EXISTING_RUNNER_HEARTBEAT_RECOVERY",
            "QUEUE_STUCK": "EXISTING_SCHEDULER_RECOVERY",
            "LEASE_STALE": "EXISTING_OWNER_LOCK_RECOVERY",
            "HOST_REQUEST_STALE": "EXISTING_HOST_REQUEST_RECONCILIATION",
        }[code]
    return {
        "classification": code,
        "existing_classifier_category": existing.category,
        "existing_classifier_action": existing.action,
        "existing_recovery_advice": recovery,
        "proposed_action": action,
        "retry_tech_allowed": code not in {"CONTENT_FAILURE", "UNKNOWN", "INVALID_TRANSITION",
                                          "STALE_AUTHORITY", "TECHNICAL_RETRY_EXHAUSTED"},
        "reason": reason,
    }


def observe(snapshot: dict, *, existing_recovery: dict | None = None,
            now: dt.datetime | None = None) -> dict:
    """Produce shadow-only findings; never calls recovery or writes authority."""
    settings = config()
    if not settings.get("shadow_enabled") or not settings.get("config_valid"):
        return {"status": "DISABLED", "findings": [], "shadow_only": True,
                "recovery_executed": False, "authority_writes": 0,
                "llm_calls": 0, "network_calls": 0}
    detected = detect(snapshot, now=now)
    rows = []
    for finding in detected:
        row = classify(finding)
        row.update({"source": finding["source"], "evidence": finding["evidence"],
                    "recovery_executed": False})
        if isinstance(existing_recovery, dict):
            existing = str(existing_recovery.get("next_action") or existing_recovery.get("action") or "")
            row["existing_recovery_action"] = existing
            row["matched_existing_recovery"] = bool(existing) and (
                (row["retry_tech_allowed"] and existing.lower() in {"retry", "technical_retry"})
                or (not row["retry_tech_allowed"] and existing.lower() not in {"retry", "technical_retry"})
            )
        rows.append(row)
    return {
        "status": "OBSERVED" if rows else "NO_FINDINGS",
        "findings": rows,
        "shadow_only": True,
        "recovery_executed": False,
        "authority_writes": 0,
        "episode_transitions": 0,
        "force_pass": False,
        "llm_calls": 0,
        "network_calls": 0,
    }


def observe_failure(return_code: int, *, note: str = "", existing_category: str = "",
                    existing_recovery: dict | None = None, attempt: int | None = None,
                    max_attempts: int | None = None) -> dict:
    """Shadow an already-observed runner outcome without changing its policy."""
    return observe({"failure": {"return_code": int(return_code), "note": str(note),
                                 "existing_category": str(existing_category),
                                 "attempt": attempt, "max_attempts": max_attempts}},
                   existing_recovery=existing_recovery)
