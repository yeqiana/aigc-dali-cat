#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS shared production-queue / ledger primitives (B0).

image_scheduler (single-frame first-completed lane) and batch_scheduler
(5-frame logical batch lane) manage the same queue document under the same
OS advisory lock.  This module is the single implementation source for those
queue/ledger primitives; it does NOT merge the two scheduler main loops.

Lane policy stays with the consumer for B0/B1:
- dependency_satisfied: generic ledger/queue check.  Visual Lock baseline
  approval remains an image_scheduler lane rule passed by the caller.
- ready_items: generic scan; the batch lane filters scope=="batch" itself.
- ledger_begin notes are consumer-supplied so existing ledger text is kept.
"""
from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
QUEUE_REL = Path("meta/production-queue.json")
SCHEDULER_LOCK_REL = Path("meta/runtime-image-scheduler.lock")
EMPTY_QUEUE = {"schema_version": 1, "items": [], "waves": []}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    import story_json

    data = story_json.read_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    import story_json

    story_json.write_json(path, data)


def empty_queue(*, max_parallel: int | None = None) -> dict:
    """Fresh queue document shared by both lanes."""
    q = {"schema_version": 1, "created_at": now(), "updated_at": now(),
         "items": [], "waves": []}
    if max_parallel is not None:
        q["max_parallel"] = int(max_parallel)
    return q


def load_queue(ep: Path) -> dict:
    """Read production queue with the portability path guard.

    Missing file returns EMPTY_QUEUE (same semantics as both scheduler lanes'
    private copies).
    """
    p = Path(ep).resolve() / QUEUE_REL
    if not p.is_file():
        return dict(EMPTY_QUEUE)
    q = read_json(p)
    import runtime_portability

    errors = runtime_portability.queue_path_errors(q)
    if errors:
        raise ValueError("production queue portability guard failed: "
                         + "; ".join(errors[:8]))
    return q


def save_queue(ep: Path, q: dict) -> None:
    q["updated_at"] = now()
    write_json(Path(ep).resolve() / QUEUE_REL, q)


class QueueMutationBusy(RuntimeError):
    """A queue writer raced an active scheduler or another writer."""


@contextmanager
def queue_transaction(ep: Path):
    """Serialize queue read-modify-write against image execution.

    Both scheduler lanes hold this same OS lock for the whole run, so small
    direct mutations fail with QueueMutationBusy while pixels/ledger
    transitions are in flight.  The caller can retry later.
    """
    import runner_state_store

    ep = Path(ep).resolve()
    if not runner_state_store.acquire_lock(ep, lock_rel=SCHEDULER_LOCK_REL):
        raise QueueMutationBusy("QUEUE_MUTATION_BUSY: image scheduler owns "
                                "the production queue; retry later")
    try:
        yield
    finally:
        runner_state_store.release_lock(ep, lock_rel=SCHEDULER_LOCK_REL)


def ledger(ep: Path) -> dict:
    p = Path(ep).resolve() / "meta/production-ledger.json"
    if not p.is_file():
        return {}
    data = read_json(p)
    return data if isinstance(data, dict) else {}


def ledger_state(ep: Path, frame: int) -> str:
    return str((((ledger(ep).get("frames") or {}).get(f"{frame:02d}") or {})
                .get("status") or "PENDING"))


def dependency_satisfied(ep: Path, q: dict, dep: int,
                         extra_ok: Callable[[int], bool] | None = None) -> bool:
    """True when ledger/queue show the dependency already produced.

    extra_ok lets the image lane add its Visual Lock baseline-approval rule
    without embedding lane policy here.
    """
    import production_ledger

    if extra_ok is not None and extra_ok(int(dep)):
        return True
    if ledger_state(ep, int(dep)) in production_ledger.READY_LEDGER_STATES:
        return True
    return any(int(x.get("frame") or 0) == int(dep)
               and x.get("status") == "generated"
               for x in q.get("items") or [])


def ready_items(ep: Path, q: dict, *, scope: str | None = None,
                extra_ok: Callable[[int], bool] | None = None) -> list[dict]:
    """Queued items whose generation_depends_on prerequisites are satisfied.

    Priority desc then frame asc matches the image lane; batch items without a
    priority field sort by frame only, preserving the batch lane order.
    """
    rows = []
    for item in q.get("items") or []:
        if item.get("status") != "queued":
            continue
        if scope is not None and str(item.get("scope") or "") != scope:
            continue
        deps = [int(x) for x in item.get("depends_on") or []]
        if all(dependency_satisfied(ep, q, x, extra_ok=extra_ok) for x in deps):
            rows.append(item)
    return sorted(rows,
                  key=lambda x: (-int(x.get("priority") or 0),
                                 int(x.get("frame") or 0)))


def current_contract_sha(ep: Path, frame: int) -> str:
    import frame_contract

    prov = frame_contract.provenance(ep, int(frame))
    if not prov:
        raise ValueError(f"frame {int(frame):02d} missing Frame Contract provenance")
    return str(prov["contract_sha256"])


def _prompt_path(item: dict) -> Path:
    raw = Path(str(item["prompt_file"]))
    return raw if raw.is_absolute() else (ROOT / raw).resolve()


def _ledger_references(item: dict) -> list[str]:
    return [f"{(ROOT / ref['path']).resolve()}::{ref['role']}::{ref['kind']}"
            for ref in item.get("references") or []]


def ledger_begin(ep: Path, item: dict, *, notes: str | None = None,
                 batch_id: str | None = None) -> tuple[bool, str]:
    import ledger_call

    return ledger_call.begin(
        ep,
        frame=int(item["frame"]),
        kind=item["kind"],
        prompt_file=_prompt_path(item),
        capture_id=item["capture_id"],
        model=item.get("model") or "default",
        quality=item.get("quality") or "high",
        notes=notes or f"scheduler item={item.get('id')} scope={item.get('scope')}",
        references=_ledger_references(item),
        batch_id=batch_id,
        transaction_id=str((item.get("execution") or {}).get("transaction_id") or "")
        or None,
    )


def ledger_success(ep: Path, item: dict, result: dict,
                   *, default_quality: str = "high") -> tuple[bool, str]:
    import ledger_call

    returned_policy = (result.get("payload") or {}).get("image_model") or {}
    requested_model = str(item.get("model") or "default")
    requested_quality = str(item.get("quality") or default_quality)
    if str(returned_policy.get("model") or "") != requested_model:
        return False, (f"IMAGE_MODEL_CONTRACT_MISMATCH: returned="
                       f"{returned_policy.get('model')} requested={requested_model}")
    if str(returned_policy.get("quality") or "") != requested_quality:
        return False, (f"IMAGE_QUALITY_CONTRACT_MISMATCH: returned="
                       f"{returned_policy.get('quality')} requested={requested_quality}")
    returned = ((result.get("payload") or {}).get("frame_contract") or {})
    returned_sha = returned.get("contract_sha256")
    current = current_contract_sha(ep, int(item["frame"]))
    if returned_sha and str(returned_sha).lower() != str(current).lower():
        return False, (f"backend frame contract drift returned={returned_sha} "
                       f"current={current}")
    receipt = ((result.get("payload") or {}).get("provider_receipt") or {})
    receipt_path = receipt.get("path")
    resolved = None
    if receipt_path:
        resolved = Path(str(receipt_path))
        if not resolved.is_absolute():
            resolved = ROOT / resolved
    return ledger_call.success(ep, frame=int(item["frame"]),
                               path=Path(str(result["output"])),
                               provider_receipt=resolved)


def ledger_tech_fail(ep: Path, item: dict, code: str, message: str) -> None:
    import ledger_call

    ledger_call.tech_fail(ep, frame=int(item["frame"]), code=code,
                          message=message)


def self_test() -> None:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="scheduler core self test ") as td:
        ep = Path(td)
        assert load_queue(ep) == EMPTY_QUEUE
        q = empty_queue(max_parallel=3)
        save_queue(ep, q)
        assert load_queue(ep)["max_parallel"] == 3
        with queue_transaction(ep):
            assert load_queue(ep)["schema_version"] == 1
        try:
            with queue_transaction(ep):
                with queue_transaction(ep):
                    raise AssertionError("nested queue_transaction must fail")
        except QueueMutationBusy:
            pass
    print("SCHEDULER CORE SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
