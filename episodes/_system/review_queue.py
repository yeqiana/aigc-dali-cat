"""Attempt-scoped Fast Scout review queue stored in the shared production queue."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import uuid

import logical_asset_identity

QUEUE_KEY = "review_work_items"
ACTIVE = {"queued", "running"}
TERMINAL = {"finalized", "failed", "stale"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def item_key(*, episode_id: str, logical_asset_key: str, generation_key: str,
             artifact_sha256: str, review_kind: str) -> str:
    raw = "|".join((episode_id, logical_asset_key, generation_key,
                    artifact_sha256.lower(), review_kind))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def enqueue(q: dict, *, episode: Path, source_item: dict, artifact_path: str,
            artifact_sha256: str, policy: dict, review_kind: str = "FAST_SCOUT") -> dict:
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
        "review_kind": review_kind,
        "source_scope": str(source_item.get("scope") or ""),
        "repair_wave_id": str(source_item.get("repair_wave_id") or ""),
        "model_role": "vision.fast",
        "model_policy_sha256": str(policy.get("model_policy_sha256") or ""),
        "model": str(policy.get("model") or ""),
        "queued_at": now(),
        "status": "queued",
        "claim_token": None,
        "lease_expires_at": None,
        "receipt": None,
    }
    if not item["model_policy_sha256"] or not item["model"]:
        return {"status": "BLOCKED", "reason": "BOUND_REVIEW_POLICY_MISSING"}
    rows.append(item)
    return {"status": "ENQUEUED", "item": item}


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
        receipt_match = (isinstance(result, dict)
                         and result.get("generation_key") == item["generation_key"]
                         and str(result.get("asset_sha256") or "").lower() == item["artifact_sha256"]
                         and result.get("model_policy_sha256") == item["model_policy_sha256"])
        if not receipt_match:
            try:
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
                result = {"decision": "DEFER_TO_FINAL", "issue_codes": [],
                          "notes": f"Review technical failure: {exc}",
                          "scout_status": "technical_defer", "model_called": False}
        result = dict(result or {})
        result.update(generation_key=item["generation_key"],
                      logical_asset_key=item["logical_asset_key"],
                      attempt_index=item["attempt_index"],
                      model_policy_sha256=item["model_policy_sha256"])
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
                # Keep the legacy latest-per-frame projection only for the current candidate.
                if not stale:
                    frame_scout_persistence.save(ep, result)
                telemetry(ep, "REVIEW_FINISHED", {**item, "status": terminal}, queue_depth=depth(q))
        changed.set()
        progress.set()

    while True:
        while len(active) < max(1, int(max_inflight)):
            with scheduler_core.queue_transaction(ep):
                q = scheduler_core.load_queue(ep)
                row = claim(q)
                if row:
                    scheduler_core.save_queue(ep, q)
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
