"""Attempt-scoped review queue stored in the shared production queue."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import uuid

import logical_asset_identity
import runtime_timeout_policy

QUEUE_KEY = "review_work_items"
ACTIVE = {"queued", "running"}
TERMINAL = {"finalized", "failed", "stale"}
FAST_SCOUT = "FAST_SCOUT"
FINAL_SEMANTIC = "FINAL_SEMANTIC"
PHASE5A_SINGLE_FRAME = "PHASE5A_SINGLE_FRAME"
_REVIEW_ROLES = {FAST_SCOUT: "vision.fast", FINAL_SEMANTIC: "vision.final"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def item_key(*, episode_id: str, logical_asset_key: str, generation_key: str,
             artifact_sha256: str, review_kind: str) -> str:
    raw = "|".join((episode_id, logical_asset_key, generation_key,
                    artifact_sha256.lower(), review_kind))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def enqueue(q: dict, *, episode: Path, source_item: dict, artifact_path: str,
            artifact_sha256: str, policy: dict, review_kind: str = "FAST_SCOUT") -> dict:
    review_kind = str(review_kind or FAST_SCOUT).upper()
    model_role = _REVIEW_ROLES.get(review_kind)
    if not model_role:
        return {"status": "BLOCKED", "reason": "UNSUPPORTED_REVIEW_KIND"}
    policy_role = str(policy.get("role") or "")
    if policy_role and policy_role != model_role:
        return {"status": "BLOCKED", "reason": "REVIEW_POLICY_ROLE_MISMATCH"}
    generation_key = str(source_item.get("generation_key") or "")
    if not generation_key:
        return {"status": "BLOCKED", "reason": "GENERATION_KEY_MISSING"}
    frame = int(source_item.get("frame") or 0)
    episode_key = logical_asset_identity.episode_id(episode)
    asset_key = logical_asset_identity.frame_asset_key(episode, frame)
    key = item_key(episode_id=episode_key, logical_asset_key=asset_key,
                   generation_key=generation_key, artifact_sha256=artifact_sha256,
                   review_kind=review_kind)
    rows = q.setdefault(QUEUE_KEY, [])
    existing = next((row for row in rows if row.get("review_key") == key), None)
    if existing:
        return {"status": "ALREADY_ENQUEUED", "item": existing}
    item = {
        "review_key": key,
        "episode_id": episode_key,
        "logical_asset_key": asset_key,
        "generation_key": generation_key,
        "frame": frame,
        "attempt_index": int(source_item.get("attempt_index") or source_item.get("attempts") or 1),
        "artifact_path": str(artifact_path).replace("\\", "/"),
        "artifact_sha256": artifact_sha256.lower(),
        "frame_contract_sha256": str(source_item.get("frame_contract_sha256") or "").lower(),
        "prompt_package_sha256": str(
            source_item.get("prompt_package_sha256")
            or ((source_item.get("prompt_package") or {}).get("sha256")
                if isinstance(source_item.get("prompt_package"), dict) else "")
        ).lower(),
        "review_kind": review_kind,
        "source_scope": str(source_item.get("scope") or ""),
        "repair_wave_id": str(source_item.get("repair_wave_id") or ""),
        "model_role": model_role,
        "model_policy_sha256": str(policy.get("model_policy_sha256") or ""),
        "model": str(policy.get("model") or ""),
        "queued_at": now(),
        "status": "queued",
        "claim_token": None,
        "lease_expires_at": None,
        "receipt": None,
    }
    if review_kind == FINAL_SEMANTIC:
        item["profile"] = str(policy.get("profile") or "")
        item["reasoning_effort"] = str(policy.get("reasoning_effort") or "")
    if not item["model_policy_sha256"] or not item["model"]:
        return {"status": "BLOCKED", "reason": "BOUND_REVIEW_POLICY_MISSING"}
    rows.append(item)
    return {"status": "ENQUEUED", "item": item}


def enqueue_final_semantic(q: dict, *, episode: Path, source_item: dict,
                           artifact: Path, artifact_path: str,
                           review_scope: str | None = None) -> dict:
    """Enqueue the official final semantic review for one committed candidate.

    The caller owns persistence/queue locking, just as with enqueue_generated.
    Policy is resolved from the Episode-bound snapshot; global policy is never
    used as a fallback.
    """
    import fast_frame_scout
    import model_policy
    import production_recovery

    source = dict(source_item)
    if not source.get("generation_key"):
        source["generation_key"] = production_recovery.generation_key_for_item(episode, source)
    if not source.get("attempt_index"):
        lifecycle = production_recovery._read(production_recovery.lifecycle_path(episode, source))
        source["attempt_index"] = (lifecycle.get("attempt_index") or lifecycle.get("attempt")
                                   or source.get("attempts") or 1)
    if not source.get("generation_key") or not artifact.is_file():
        return {"status": "BLOCKED", "reason": "GENERATION_EVIDENCE_MISSING"}
    policy = model_policy.resolve("vision.final", episode=episode)
    result = enqueue(q, episode=episode, source_item=source,
                     artifact_path=artifact_path,
                     artifact_sha256=fast_frame_scout.sha256_file(artifact),
                     policy=policy, review_kind=FINAL_SEMANTIC)
    row = result.get("item") if isinstance(result.get("item"), dict) else None
    scope = str(review_scope or "").strip()
    if scope:
        if scope != PHASE5A_SINGLE_FRAME:
            return {"status": "BLOCKED", "reason": "UNSUPPORTED_FINAL_REVIEW_SCOPE"}
        if row is not None:
            existing_scope = str(row.get("review_scope") or "")
            if existing_scope and existing_scope != scope:
                return {"status": "BLOCKED", "reason": "FINAL_REVIEW_SCOPE_CONFLICT"}
            row["review_scope"] = scope
    if result.get("status") == "ALREADY_ENQUEUED" and row is not None:
        if scope == PHASE5A_SINGLE_FRAME and row.get("status") == "stale":
            row.update(
                status="queued", claim_token=None, lease_expires_at=None,
                receipt=None, queued_at=now(), review_scope=scope,
            )
            result = {"status": "REENQUEUED_STALE", "item": row}
    if result.get("status") in {"ENQUEUED", "REENQUEUED_STALE"}:
        telemetry(episode, "REVIEW_ENQUEUED", result["item"], queue_depth=depth(q))
    return result


def _receipt_matches_item(item: dict, receipt: dict | None) -> bool:
    if not isinstance(receipt, dict):
        return False
    if item.get("review_kind", FAST_SCOUT) == FAST_SCOUT:
        return (receipt.get("generation_key") == item.get("generation_key")
                and str(receipt.get("asset_sha256") or "").lower()
                == str(item.get("artifact_sha256") or "").lower()
                and receipt.get("model_policy_sha256") == item.get("model_policy_sha256"))
    try:
        attempt_matches = int(receipt.get("attempt_index") or 0) == int(item.get("attempt_index") or 0)
    except (TypeError, ValueError):
        return False
    common = (
        receipt.get("review_kind") == item.get("review_kind")
        and receipt.get("episode_id") == item.get("episode_id")
        and receipt.get("logical_asset_key") == item.get("logical_asset_key")
        and receipt.get("generation_key") == item.get("generation_key")
        and attempt_matches
        and str(receipt.get("artifact_sha256") or "").lower() == str(item.get("artifact_sha256") or "").lower()
        and receipt.get("model_role") == item.get("model_role")
        and receipt.get("model") == item.get("model")
        and receipt.get("profile") == item.get("profile")
        and receipt.get("reasoning_effort") == item.get("reasoning_effort")
        and receipt.get("model_policy_sha256") == item.get("model_policy_sha256")
    )
    if not common:
        return False
    if item.get("review_kind") == FINAL_SEMANTIC:
        return receipt.get("status") in {"SUCCESS", "COMPLETED_WITH_FINDINGS"}
    return False


def _current_final_candidate_matches(ep: Path, item: dict) -> bool:
    """Fail closed unless the official semantic-review binding is this item."""
    import frame_semantic_review

    try:
        only_frames = ([int(item.get("frame") or 0)]
                       if item.get("review_scope") == PHASE5A_SINGLE_FRAME else None)
        frame = next((row for row in frame_semantic_review.reviewable_frame_records(
            ep, require_files=True, only_frames=only_frames)
            if str(row.get("frame") or "").zfill(2)
            == f"{int(item.get('frame') or 0):02d}"), None)
    except Exception:
        return False
    if not frame:
        return False
    return (
        frame.get("logical_asset_key") == item.get("logical_asset_key")
        and frame.get("generation_key") == item.get("generation_key")
        and str(frame.get("sha256") or "").lower() == str(item.get("artifact_sha256") or "").lower()
    )


def _final_semantic_receipt(ep: Path, item: dict, *, codex: str | None, timeout: int) -> dict:
    """Run or adopt the official final semantic evidence for a queue item."""
    import frame_review_persistence
    import frame_semantic_review
    import model_policy
    bound = model_policy.resolve("vision.final", episode=ep)
    if (bound.get("model_policy_sha256") != item.get("model_policy_sha256")
            or bound.get("model") != item.get("model")):
        raise RuntimeError("FINAL_SEMANTIC_BOUND_POLICY_MISMATCH")
    if not _current_final_candidate_matches(ep, item):
        return {"status": "STALE_EVIDENCE", "review_outcome": "STALE_EVIDENCE"}

    review_attempt = int(item.get("attempt_index") or 1)
    if review_attempt not in {1, 2}:
        raise RuntimeError("FINAL_SEMANTIC_ATTEMPT_INDEX_INVALID")

    # A durable Review commit intent means the Final Semantic model already
    # ran. Recover its bound candidate/projections before considering any new
    # Critic dispatch; a receipt/commit problem must never spend another model
    # call or generation attempt.
    commit = frame_semantic_review.find_review_commit_for_item(
        ep, str(item.get("review_key") or ""))
    if commit is not None:
        commit_id = str(commit.get("commit_id") or "")
        manifest = commit.get("manifest")
        if not commit_id or not frame_semantic_review.review_commit_is_decided(manifest):
            raise RuntimeError("FINAL_SEMANTIC_REVIEW_COMMIT_MANIFEST_INVALID")
        if manifest.get("status") == "COMMIT_DECIDED":
            recovery = frame_semantic_review.reconcile_review_commit(ep, commit_id)
            if not isinstance(recovery, dict) or recovery.get("status") != "PROJECTIONS_APPLIED":
                raise RuntimeError("FINAL_SEMANTIC_REVIEW_COMMIT_INCOMPLETE")
            manifest = frame_semantic_review.load_review_commit(ep, commit_id)
        if (not frame_semantic_review.review_commit_projections_verified(ep, commit_id)
                or not isinstance(manifest, dict)
                or manifest.get("status") != "PROJECTIONS_APPLIED"):
            raise RuntimeError("FINAL_SEMANTIC_REVIEW_COMMIT_INCOMPLETE")

    # If official evidence was committed before the queue completion write,
    # adopt it. `verify_episode` checks the canonical receipt bindings and does
    # not make another model call.
    scoped = item.get("review_scope") == PHASE5A_SINGLE_FRAME
    if scoped:
        try:
            scoped_frames = frame_semantic_review.frame_records(
                ep, require_files=False, only_frames=[int(item["frame"])])
            verified = not frame_semantic_review.verify_scoped_review(
                ep, scoped_frames,
                review_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
                metadata_only=True)
        except Exception:
            verified = False
    else:
        verified = not frame_semantic_review.verify_episode(ep, metadata_only=True)
    current_review = frame_review_persistence.load(ep, int(item["frame"])) if verified else None
    can_adopt = (verified and isinstance(current_review, dict)
                 and current_review.get("generation_key") == item.get("generation_key")
                 and str(current_review.get("asset_sha256") or "").lower() == item["artifact_sha256"]
                 and current_review.get("logical_asset_key") == item.get("logical_asset_key")
                 and current_review.get("model_policy_sha256") == item.get("model_policy_sha256"))
    if commit is not None and not can_adopt:
        # A durable commit decision proves the Critic already ran. If its
        # projection cannot be adopted, stop for reconciliation; never spend a
        # second Final Semantic call to paper over a broken Review commit.
        raise RuntimeError("FINAL_SEMANTIC_REVIEW_COMMIT_INCOMPLETE")
    if can_adopt:
        critic_summary = frame_semantic_review.read_json(ep / frame_semantic_review.SUMMARY_REL)
        critic_receipt = ((critic_summary.get("critic_provenance") or {}).get("model_execution_receipt")
                          if isinstance(critic_summary, dict) else None)
        rc = 0
        reused = True
    else:
        reused = False
        rc = frame_semantic_review.run_critic(
            ep, attempt=review_attempt, codex_raw=codex, timeout=timeout,
            target_frames=([int(item["frame"])] if scoped else None),
            review_scope=(frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE
                          if scoped else "FULL_FRAME_SET"),
            review_item=item)
        pending = frame_semantic_review.pending_request_path(ep, review_attempt)
        candidate = ep / frame_semantic_review.CANDIDATE_REL
        if rc == 0 and pending.is_file() and candidate.is_file():
            rc = frame_semantic_review.apply_pending_candidate(ep, attempt=review_attempt)
        # A finding may be a legitimate completed semantic result (rc=2).
        # Preserve that result as evidence; technical failures without a bound
        # frame receipt remain failed queue items.
        current_review = frame_review_persistence.load(ep, int(item["frame"]))
        critic_summary = (frame_semantic_review.read_json(ep / frame_semantic_review.SUMMARY_REL)
                          if (ep / frame_semantic_review.SUMMARY_REL).is_file() else {})
        critic_receipt = ((critic_summary.get("critic_provenance") or {}).get("model_execution_receipt")
                          if isinstance(critic_summary, dict) else None)
        if scoped and rc == 0:
            scoped_frames = frame_semantic_review.frame_records(
                ep, require_files=False, only_frames=[int(item["frame"])])
            verify_errors = frame_semantic_review.verify_scoped_review(
                ep, scoped_frames,
                review_scope=frame_semantic_review.PHASE5A_SINGLE_FRAME_SCOPE,
                metadata_only=True)
        else:
            verify_errors = frame_semantic_review.verify_episode(ep, metadata_only=True)
    if reused:
        verify_errors = []

    if not _current_final_candidate_matches(ep, item):
        return {"status": "STALE_EVIDENCE", "review_outcome": "STALE_EVIDENCE"}
    bound_review = isinstance(current_review, dict) and (
        current_review.get("generation_key") == item.get("generation_key")
        and str(current_review.get("asset_sha256") or "").lower() == item["artifact_sha256"]
        and current_review.get("logical_asset_key") == item.get("logical_asset_key")
        and current_review.get("model_policy_sha256") == item.get("model_policy_sha256")
    )
    if not bound_review:
        raise RuntimeError("FINAL_SEMANTIC_EVIDENCE_BINDING_MISSING")

    issues = current_review.get("issue_codes") or []
    content_finding = bool(issues or current_review.get("decision") == "fail")
    critic_receipt_valid = isinstance(critic_receipt, dict) and not (
        frame_semantic_review.validate_final_semantic_execution_receipt(
            critic_receipt,
            {
                "review_item_id": str(item.get("review_key") or ""),
                "logical_asset_key": item.get("logical_asset_key"),
                "generation_key": item.get("generation_key"),
                "attempt_index": review_attempt,
                "candidate_sha256": item.get("artifact_sha256"),
                "frame_contract_sha256": item.get("frame_contract_sha256"),
                "prompt_package_sha256": item.get("prompt_package_sha256"),
                "model_policy_sha256": item.get("model_policy_sha256"),
                "evidence_fingerprint": current_review.get("evidence_fingerprint"),
            },
        )
    )
    passed = (current_review.get("decision") == "pass" and not issues and rc == 0
              and not verify_errors and critic_receipt_valid)
    outcome = ("PASS" if passed else "REPAIR_NEEDED" if content_finding and critic_receipt_valid
               else "TECH_FAILED")
    schema = int(frame_semantic_review.SCHEMA_VERSION)
    evidence_fingerprint = str(current_review.get("evidence_fingerprint") or "")
    return {
        "schema_version": 1,
        "review_kind": FINAL_SEMANTIC,
        "status": "SUCCESS" if passed else "COMPLETED_WITH_FINDINGS" if outcome == "REPAIR_NEEDED" else "TECH_FAILED",
        "decision": current_review.get("decision"),
        "review_outcome": outcome,
        "episode_id": item.get("episode_id"),
        "logical_asset_key": item.get("logical_asset_key"),
        "generation_key": item.get("generation_key"),
        "attempt_index": review_attempt,
        "artifact_sha256": item.get("artifact_sha256"),
        "model_role": "vision.final",
        "model": bound.get("model"),
        "profile": bound.get("profile"),
        "reasoning_effort": bound.get("reasoning_effort"),
        "model_policy_sha256": bound.get("model_policy_sha256"),
        "review_schema_version": schema,
        "evidence_fingerprint": evidence_fingerprint,
        "issue_codes": list(issues),
        "notes": current_review.get("notes"),
        "critic_receipt": critic_receipt,
        "critic_receipt_ref": str(frame_semantic_review.SUMMARY_REL).replace("\\", "/"),
        "reused_official_evidence": reused,
        "verified_at": now(),
    }


def _final_semantic_timeout(timeout: int) -> int:
    import runtime_timeout_policy
    return runtime_timeout_policy.resolve("deep_semantic_review", timeout)


def depth(q: dict) -> int:
    return sum(str(row.get("status") or "") in ACTIVE for row in q.get(QUEUE_KEY) or [])


def recover_claims(q: dict) -> int:
    """Release claims left by a stopped scheduler; caller owns the queue lock."""
    count = 0
    for row in q.get(QUEUE_KEY) or []:
        if row.get("status") == "running":
            row.update(status="queued", claim_token=None, lease_expires_at=None)
            count += 1
    return count


def oldest_wait_ms(q: dict, at: str | None = None) -> int | None:
    rows = [row for row in q.get(QUEUE_KEY) or [] if row.get("status") in ACTIVE]
    if not rows:
        return None
    current = datetime.fromisoformat(at or now())
    oldest = min(datetime.fromisoformat(str(row["queued_at"])) for row in rows)
    return max(0, int((current - oldest).total_seconds() * 1000))


def claim(q: dict, *, lease_seconds: int = 300, at: str | None = None) -> dict | None:
    current = datetime.fromisoformat(at or now())
    for row in sorted(q.get(QUEUE_KEY) or [], key=lambda value: str(value.get("queued_at") or "")):
        status = str(row.get("status") or "")
        if status == "running":
            expiry = row.get("lease_expires_at")
            if expiry and datetime.fromisoformat(str(expiry)) > current:
                continue
            row.update(status="queued", claim_token=None, lease_expires_at=None)
            status = "queued"
        if status != "queued":
            continue
        token = uuid.uuid4().hex
        row.update(status="running", claim_token=token,
                   lease_expires_at=(current + timedelta(seconds=lease_seconds)).isoformat())
        return row
    return None


def finish(q: dict, review_key: str, claim_token: str, *, status: str,
           receipt: dict | None = None) -> bool:
    if status not in TERMINAL:
        raise ValueError(f"invalid review terminal status: {status}")
    row = next((value for value in q.get(QUEUE_KEY) or []
                if value.get("review_key") == review_key), None)
    if not row or row.get("status") != "running" or row.get("claim_token") != claim_token:
        return False
    row.update(status=status, terminal_at=now(), receipt=receipt,
               claim_token=None, lease_expires_at=None)
    return True


def backpressure(q: dict, *, high: int, low: int) -> tuple[bool, str | None]:
    if type(high) is not int or type(low) is not int or low < 0 or high <= low:
        raise ValueError("review backpressure requires integer HIGH > LOW >= 0")
    state = q.setdefault("review_backpressure", {"paused": False})
    current = depth(q)
    was_paused = bool(state.get("paused"))
    paused = current >= high if not was_paused else current > low
    state.update(paused=paused, depth=current, high_watermark=high, low_watermark=low,
                 updated_at=now())
    transition = "PAUSED" if paused and not was_paused else "RESUMED" if was_paused and not paused else None
    return paused, transition


def reconcile_generated(q: dict, *, episode: Path, policy: dict,
                        sha256_file) -> list[dict]:
    """Idempotently enqueue committed queue artifacts that missed enqueue on crash."""
    created = []
    for source in q.get("items") or []:
        if source.get("status") != "generated" or not source.get("output_path"):
            continue
        artifact = Path(str(source["output_path"]))
        if not artifact.is_absolute():
            artifact = Path(__file__).resolve().parents[2] / artifact
        if not artifact.is_file():
            continue
        if not source.get("generation_key"):
            import production_recovery
            source["generation_key"] = production_recovery.generation_key_for_item(episode, source)
        if not source.get("attempt_index"):
            lifecycle = production_recovery._read(production_recovery.lifecycle_path(episode, source))
            source["attempt_index"] = lifecycle.get("attempt_index") or lifecycle.get("attempt") or source.get("attempts") or 1
        result = enqueue(q, episode=episode, source_item=source,
                         artifact_path=str(source["output_path"]),
                         artifact_sha256=sha256_file(artifact), policy=policy)
        if result.get("status") == "ENQUEUED":
            created.append(result["item"])
            telemetry(episode, "REVIEW_ENQUEUED", result["item"], queue_depth=depth(q))
    return created


def enqueue_generated(q: dict, *, episode: Path, source_item: dict,
                      artifact: Path, artifact_path: str) -> dict:
    import fast_frame_scout
    import model_policy
    import production_recovery
    source = dict(source_item)
    if not source.get("generation_key"):
        source["generation_key"] = production_recovery.generation_key_for_item(episode, source)
    if not source.get("attempt_index"):
        lifecycle = production_recovery._read(production_recovery.lifecycle_path(episode, source))
        source["attempt_index"] = lifecycle.get("attempt_index") or lifecycle.get("attempt") or source.get("attempts") or 1
    if not source.get("generation_key") or not artifact.is_file():
        return {"status": "BLOCKED", "reason": "GENERATION_EVIDENCE_MISSING"}
    policy = model_policy.resolve("vision.fast", episode=episode)
    result = enqueue(q, episode=episode, source_item=source, artifact_path=artifact_path,
                     artifact_sha256=fast_frame_scout.sha256_file(artifact), policy=policy)
    if result.get("status") == "ENQUEUED":
        telemetry(episode, "REVIEW_ENQUEUED", result["item"], queue_depth=depth(q))
    return result


def telemetry(ep: Path, event: str, item: dict, *, queue_depth: int) -> None:
    try:
        import runtime_observability
        runtime_observability.safe_record_runtime_event(
            ep, event, episode_id=item.get("episode_id"),
            logical_asset_key=item.get("logical_asset_key"),
            frame_id=f"{int(item.get('frame') or 0):02d}",
            generation_key=item.get("generation_key"),
            attempt_index=item.get("attempt_index"),
            model_role=item.get("model_role"),
            model_policy_sha256=item.get("model_policy_sha256"),
            queue_name="review", queue_depth=queue_depth,
            evidence_ref=item.get("review_key"), status=item.get("status"),
            source="review_queue")
        if item.get("source_scope") == "repair":
            repair_event = {"REVIEW_ENQUEUED":"REPAIR_ENQUEUED",
                            "REVIEW_STARTED":"REPAIR_REVIEW_STARTED",
                            "REVIEW_FINISHED":"REPAIR_REVIEW_FINISHED"}.get(event)
            if repair_event:
                runtime_observability.safe_record_runtime_event(
                    ep, repair_event, episode_id=item.get("episode_id"),
                    logical_asset_key=item.get("logical_asset_key"),
                    frame_id=f"{int(item.get('frame') or 0):02d}",
                    generation_key=item.get("generation_key"),
                    repair_generation_key=item.get("generation_key"),
                    repair_wave_id=item.get("repair_wave_id"),
                    attempt_index=item.get("attempt_index"),
                    model_role=item.get("model_role"),
                    model_policy_sha256=item.get("model_policy_sha256"),
                    queue_name="repair_review",queue_depth=queue_depth,
                    evidence_ref=item.get("review_key"),status=item.get("status"),
                    source="review_queue")
    except Exception:
        pass


def _claim_next_lane_item(ep: Path, scheduler_core) -> dict | None:
    """Claim work while serialized with Phase5A epoch retirement.

    The lane-start check is only an early rejection. This check shares the
    retirement lock at the actual claim boundary, so a lane started earlier
    cannot claim work after retirement commits.
    """
    ep = Path(ep).resolve()
    if (ep / "meta" / "phase5a-canary.json").is_file():
        import phase5a_collaborative_canary
        from runtime_atomic_store import FileLock

        with FileLock(
            phase5a_collaborative_canary.validation_epoch_lock_target(ep),
            timeout=runtime_timeout_policy.seconds("authority_lock"), stale_seconds=3600,
        ):
            phase5a_collaborative_canary.assert_validation_epoch_review_dispatch_eligible(ep)
            with scheduler_core.queue_transaction(ep):
                queue = scheduler_core.load_queue(ep)
                row = claim(queue)
                if row:
                    scheduler_core.save_queue(ep, queue)
            return row

    with scheduler_core.queue_transaction(ep):
        queue = scheduler_core.load_queue(ep)
        row = claim(queue)
        if row:
            scheduler_core.save_queue(ep, queue)
    return row


async def run_lane(episode: Path, *, changed, progress, stop, codex: str | None,
                   timeout: int, max_inflight: int) -> None:
    """Consume durable work concurrently with Generation; never dispatch images."""
    import asyncio
    import hashlib
    import fast_frame_scout
    import frame_scout_persistence
    import image_scheduler
    import model_policy
    import production_ledger
    import scheduler_core

    ep = Path(episode).resolve()
    phase5a_marker = ep / "meta" / "phase5a-canary.json"
    if phase5a_marker.is_file():
        import phase5a_collaborative_canary
        phase5a_collaborative_canary.assert_validation_epoch_review_dispatch_eligible(ep)
    active: set[asyncio.Task] = set()

    def current_artifact_sha(frame: int) -> str | None:
        ledger = production_ledger.load_authority(ep, default={}) or {}
        row = ((ledger.get("frames") or {}).get(f"{frame:02d}") or {})
        current = row.get("current_candidate") or row.get("approved_asset") or {}
        raw = current.get("path") or current.get("asset_path")
        expected = str(current.get("sha256") or "").lower()
        if raw:
            path = Path(str(raw))
            if not path.is_absolute():
                path = image_scheduler.ROOT / path
            if path.is_file():
                return fast_frame_scout.sha256_file(path)
        return expected or None

    async def execute(item: dict) -> None:
        event_item = dict(item)
        telemetry(ep, "REVIEW_STARTED", event_item, queue_depth=depth(scheduler_core.load_queue(ep)))
        result = item.get("receipt")
        receipt_match = _receipt_matches_item(item, result)
        if not receipt_match:
            try:
                if item.get("review_kind") == FINAL_SEMANTIC:
                    result = await asyncio.to_thread(
                        _final_semantic_receipt, ep, item, codex=codex,
                        timeout=_final_semantic_timeout(timeout))
                else:
                    image = image_scheduler.ROOT / item["artifact_path"]
                    result = await asyncio.to_thread(
                        fast_frame_scout.evaluate_candidate, ep, int(item["frame"]),
                        image, codex_raw=codex,
                        timeout=runtime_timeout_policy_cap(timeout), persist_result=False,
                        review_context={"generation_key": item["generation_key"],
                                        "logical_asset_key": item["logical_asset_key"],
                                        "attempt_index": item["attempt_index"],
                                        "model_policy_sha256": item["model_policy_sha256"]})
            except Exception as exc:
                if item.get("review_kind") == FINAL_SEMANTIC:
                    result = {"review_kind": FINAL_SEMANTIC, "status": "TECH_FAILED",
                              "review_outcome": "TECH_FAILED", "issue_codes": [],
                              "notes": f"Final semantic review technical failure: {exc}"}
                else:
                    result = {"decision": "DEFER_TO_FINAL", "issue_codes": [],
                              "notes": f"Review technical failure: {exc}",
                              "scout_status": "technical_defer", "model_called": False}
        result = dict(result or {})
        result.update(generation_key=item["generation_key"],
                      logical_asset_key=item["logical_asset_key"],
                      attempt_index=item["attempt_index"],
                      model_policy_sha256=item["model_policy_sha256"])
        if item.get("review_kind") == FINAL_SEMANTIC:
            result.update(artifact_sha256=item["artifact_sha256"],
                          review_kind=FINAL_SEMANTIC,
                          episode_id=item.get("episode_id"),
                          model_role=item.get("model_role"))
        # Receipt first, completion second: restart adopts this result without another model call.
        with scheduler_core.queue_transaction(ep):
            q = scheduler_core.load_queue(ep)
            row = next((value for value in q.get(QUEUE_KEY) or []
                        if value.get("review_key") == item["review_key"]), None)
            if row and row.get("claim_token") == item.get("claim_token"):
                row["receipt"] = result
                scheduler_core.save_queue(ep, q)
        current_sha = current_artifact_sha(int(item["frame"]))
        stale = not current_sha or current_sha.lower() != item["artifact_sha256"]
        if item.get("review_kind") == FINAL_SEMANTIC:
            stale = stale or not _current_final_candidate_matches(ep, item)
            technical = result.get("review_outcome") == "TECH_FAILED"
            outcome = ("STALE_EVIDENCE" if stale else
                       str(result.get("review_outcome") or "TECH_FAILED"))
        else:
            decision = str(result.get("decision") or "DEFER_TO_FINAL")
            technical = str(result.get("scout_status") or "") == "technical_defer"
            outcome = ("STALE_EVIDENCE" if stale else "TECH_FAILED" if technical else
                       "PASS" if decision == "PASS_FAST" else
                       "REPAIR_NEEDED" if decision == "REPAIR_NOW" else "NEEDS_USER")
        result["review_outcome"] = outcome
        terminal = "stale" if stale else "failed" if technical else "finalized"
        with scheduler_core.queue_transaction(ep):
            q = scheduler_core.load_queue(ep)
            ok = finish(q, item["review_key"], str(item.get("claim_token") or ""),
                        status=terminal, receipt=result)
            if ok:
                scheduler_core.save_queue(ep, q)
                # Keep the legacy latest-per-frame scout projection only for the current candidate.
                if not stale and item.get("review_kind") != FINAL_SEMANTIC:
                    frame_scout_persistence.save(ep, result)
                telemetry(ep, "REVIEW_FINISHED", {**item, "status": terminal}, queue_depth=depth(q))
        changed.set()
        progress.set()

    while True:
        while len(active) < max(1, int(max_inflight)):
            row = _claim_next_lane_item(ep, scheduler_core)
            if not row:
                break
            active.add(asyncio.create_task(execute(dict(row))))
        if active:
            done, active = await asyncio.wait(active, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                await task
            changed.set()
            continue
        if stop.is_set() and depth(scheduler_core.load_queue(ep)) == 0:
            return
        changed.clear()
        if stop.is_set() and depth(scheduler_core.load_queue(ep)) == 0:
            return
        await changed.wait()


def runtime_timeout_policy_cap(timeout: int) -> int:
    import runtime_timeout_policy
    return runtime_timeout_policy.cap("fast_scout", timeout)
