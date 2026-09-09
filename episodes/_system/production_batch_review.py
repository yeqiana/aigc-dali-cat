#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WORK/WEB actual-pixel review barrier for one generated Production logical batch.

This is an early content-repair gate, never final Production PASS authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import frame_contract
import image_scheduler
import product_review_adapter
import runtime_router
import story_json

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
QUEUE_REL = Path("meta/production-queue.json")
REVIEW_DIR = Path("meta/runtime/batch-reviews")
VALID = {"PASS_PREVIEW", "REPAIR_NOW", "UNCERTAIN"}


def read_json(path: Path) -> dict:
    data = story_json.read_json(path, require_object=False)
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)


def repo_file(raw: str) -> Path:
    p = (ROOT / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
    p.relative_to(ROOT.resolve())
    if not p.is_file():
        raise ValueError(f"batch review source missing: {raw}")
    return p


def kind(batch_id: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(batch_id)).strip("-")
    return f"production-batch-{safe}"


def candidate_path(ep: Path, batch_id: str) -> Path:
    return ep / "meta" / f".{kind(batch_id)}.candidate.json"


def final_path(ep: Path, batch_id: str) -> Path:
    return ep / REVIEW_DIR / f"{batch_id}.json"


def unit_binding(ep: Path, item: dict) -> dict:
    path = repo_file(str(item["output_path"]))
    contract = frame_contract.compile_frame(ep, int(item["frame"]), write_cache=False)
    return {"candidate_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "frame_contract_sha256": contract["contract_sha256"]}


def _valid_unit(unit: object) -> bool:
    if not isinstance(unit, dict):
        return False
    if str(unit.get("decision") or "") not in VALID:
        return False
    checks = unit.get("checks")
    if not isinstance(checks, dict) or not checks:
        return False
    if any(value not in ("pass", "fail", "uncertain") for value in checks.values()):
        return False
    if not isinstance(unit.get("unresolved"), list) or not isinstance(unit.get("issue_codes", []), list):
        return False
    if unit.get("unresolved") and unit["decision"] != "UNCERTAIN":
        return False
    if unit["decision"] == "PASS_PREVIEW" and (any(v != "pass" for v in checks.values()) or unit.get("issue_codes")):
        return False
    if unit["decision"] == "REPAIR_NOW" and not unit.get("issue_codes"):
        return False
    return True


def reusable_units(ep: Path, batch_id: str, rows: list[dict]) -> list[dict]:
    """Partial checks are evidence only; final isolated review still applies."""
    latest: dict[str, dict | None] = {}
    # Pending evidence supersedes the previous final, including invalid evidence.
    # Never fall back to an older PASS when a newer row is uncertain or malformed.
    for path in (final_path(ep, batch_id), candidate_path(ep, batch_id)):
        if not path.is_file():
            continue
        data = read_json(path)
        if data.get("batch_id") != batch_id or not isinstance(data.get("frames"), list):
            return []
        seen: set[str] = set()
        for unit in data["frames"]:
            if not isinstance(unit, dict) or not unit.get("frame"):
                return []
            key = str(unit["frame"]).zfill(2)
            latest[key] = unit if key not in seen else None
            seen.add(key)
    valid = []
    for item in rows:
        unit = latest.get(f"{int(item['frame']):02d}")
        if _valid_unit(unit) and all(unit.get(k) == v for k, v in unit_binding(ep, item).items()):
            valid.append(unit)
    return valid


def record_unit(ep: Path, batch_id: str, unit: dict) -> dict:
    """Persist one reviewed frame without granting ledger PASS or promotion."""
    with image_scheduler.queue_transaction(ep):
        rows = batch_items(ep, batch_id)
        key = str(unit.get("frame", "")).zfill(2)
        item = next((x for x in rows if f"{int(x['frame']):02d}" == key), None)
        if not item or not _valid_unit(unit):
            raise ValueError("review unit requires a batch frame, valid checks/decision/issues; unresolved checks must remain UNCERTAIN")
        if any(unit.get(k) != v for k, v in unit_binding(ep, item).items()):
            raise ValueError("review unit candidate/contract SHA drift")
        path = candidate_path(ep, batch_id)
        data = read_json(path) if path.is_file() else {"batch_id": batch_id, "frames": []}
        if data.get("batch_id") != batch_id or not isinstance(data.get("frames"), list):
            raise ValueError("invalid persisted batch review")
        if any(not isinstance(x, dict) for x in data["frames"]):
            raise ValueError("invalid persisted batch review frame")
        old = [x for x in data.get("frames") or [] if str(x.get("frame", "")).zfill(2) == key]
        data.setdefault("unit_history", []).extend(old)
        data["frames"] = [x for x in data.get("frames") or [] if x not in old] + [{**unit, "frame": key}]
        write_json(path, data)
        return data


def batch_items(ep: Path, batch_id: str) -> list[dict]:
    q = read_json(ep / QUEUE_REL)
    rows = [x for x in q.get("items") or [] if isinstance(x, dict) and x.get("batch_id") == batch_id and x.get("output_path")]
    return sorted(rows, key=lambda x: int(x.get("frame") or 0))


def review_contracts(ep: Path, rows: list[dict]) -> list[dict]:
    contracts = []
    for row in rows:
        frame = int(row["frame"])
        c = frame_contract.compile_frame(ep, frame, write_cache=False)
        contracts.append({"frame": f"{frame:02d}",
                          "candidate_sha256": hashlib.sha256(repo_file(str(row["output_path"])).read_bytes()).hexdigest(),
                          "frame_contract_sha256": c["contract_sha256"],
                          "source_binding": c.get("source_binding", {}),
                          "prompt_contract": c["prompt_contract"]})
    return contracts


def prompt(ep: Path, batch_id: str, rows: list[dict], candidate: Path, *, contracts: list[dict] | None = None) -> str:
    if contracts is None:
        contracts = review_contracts(ep, rows)
    return f"""You are a fresh WORK_ISOLATED actual-pixel reviewer for one Story OS Production logical batch.
This is an EARLY repair barrier, not final Production PASS authority.
Inspect every attached generated image against its locked Frame Contract and visible continuity.
Use REPAIR_NOW only for clear visible defects worth spending the one content repair on now.
Use PASS_PREVIEW when the frame is clearly usable so production may continue.
Use UNCERTAIN when final full-frame-set review should decide; UNCERTAIN must not trigger repair.
Check identity, wardrobe, props, weather/physics, POV/camera authorship, scene identity, anomaly readability/scale, and obvious continuity drift.
Do not penalize a large/impossible anomaly merely for being impossible; judge capture credibility and contract fidelity.
Batch: {batch_id}
The prepare result supplies reusable_units separately from this immutable review request.
Reuse verified checks; inspect the full image and key regions for remaining frames.
Persist each completed frame using production_batch_review.py record-unit with a JSON file containing
frame, candidate_sha256, frame_contract_sha256, checks, decision, unresolved, issue_codes, reason.
Unresolved checks must stay UNCERTAIN. These units never grant final PASS or user approval.
Frame contracts:
{json.dumps(contracts, ensure_ascii=False, indent=2)}
Write ONLY JSON to {candidate.relative_to(ROOT).as_posix()} with schema:
{{"batch_id":"{batch_id}","frames":[{{"frame":"01","candidate_sha256":"copy supplied SHA","frame_contract_sha256":"copy supplied SHA","checks":{{"whole_image":"pass|fail|uncertain","key_regions":"pass|fail|uncertain"}},"decision":"PASS_PREVIEW|REPAIR_NOW|UNCERTAIN","unresolved":[],"issue_codes":[],"reason":"visible evidence","confidence":0.0}}],"summary":"brief"}}
Return exactly one row for every supplied frame.
"""


def _prepare_locked(ep: Path, batch_id: str, *, attempt: int = 1) -> dict:
    ep = ep.resolve(); rows = batch_items(ep, batch_id)
    if not rows:
        raise ValueError(f"batch has no generated reviewable items: {batch_id}")
    runtime, _ = runtime_router.detect()
    if runtime not in {"WORK", "WEB"}:
        raise ValueError("production batch product review is for WORK/WEB only")
    candidate = candidate_path(ep, batch_id)
    contracts = review_contracts(ep, rows)
    sources = [repo_file(str(row["output_path"])) for row in rows]
    units = reusable_units(ep, batch_id, rows)
    request = product_review_adapter.prepare(
        ep, kind=kind(batch_id), runtime=runtime, attempt=attempt,
        prompt=prompt(ep, batch_id, rows, candidate, contracts=contracts), source_paths=sources,
        candidate_path=candidate, source_bindings={c["frame"]: c for c in contracts})
    done = {str(unit["frame"]).zfill(2) for unit in units}
    result = {**request, "reusable_units": units,
              "pending_frames": [f"{int(row['frame']):02d}" for row in rows if f"{int(row['frame']):02d}" not in done]}
    if request.get("status") == "FINALIZED":
        final = read_json(final_path(ep, batch_id))
        if result["pending_frames"] or (final.get("critic_provenance") or {}).get("request_fingerprint") != request.get("request_fingerprint"):
            raise ValueError("finalized batch evidence invalid; prepare a new review attempt")
        return result
    q = read_json(ep / QUEUE_REL)
    ids = {x.get("id") for x in rows}
    for row in q.get("items") or []:
        if row.get("id") in ids and row.get("status") == "generated":
            row["status"] = "review_pending"
            row["batch_review_request"] = request.get("request_path")
    write_json(ep / QUEUE_REL, q)
    return result


def prepare(ep: Path, batch_id: str, *, attempt: int = 1) -> dict:
    with image_scheduler.queue_transaction(ep):
        return _prepare_locked(ep, batch_id, attempt=attempt)


def _ledger_review(ep: Path, frame: int, decision: str, notes: str) -> None:
    cp = subprocess.run(
        [sys.executable, str(SYSTEM / "production_ledger.py"), "review", str(ep), "--frame", f"{frame:02d}",
         "--decision", decision, "--notes", notes[:500]],
        cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace")
    if cp.returncode != 0:
        raise RuntimeError(f"production ledger review failed frame={frame:02d}: {cp.stdout[-1000:]}")


def _finalize_locked(ep: Path, batch_id: str, *, runtime: str = "WORK", attempt: int = 1) -> dict:
    ep = ep.resolve(); candidate = candidate_path(ep, batch_id)
    rows = batch_items(ep, batch_id)
    contracts = review_contracts(ep, rows)
    data, provenance = product_review_adapter.finalize_candidate(
        ep, kind=kind(batch_id), runtime=runtime, attempt=attempt, candidate_path=candidate,
        source_bindings={c["frame"]: c for c in contracts})
    if str(data.get("batch_id") or "") != batch_id:
        raise ValueError("batch review batch_id mismatch")
    expected = {f"{int(x['frame']):02d}" for x in rows}
    reviewed = data.get("frames")
    if not isinstance(reviewed, list):
        raise ValueError("batch review frames must be list")
    by_frame = {str(x.get("frame") or "").zfill(2): x for x in reviewed if isinstance(x, dict)}
    if not expected or set(by_frame) != expected or len(reviewed) != len(expected):
        raise ValueError(f"batch review frame set mismatch: expected={sorted(expected)} got={sorted(by_frame)}")
    for frame, row in by_frame.items():
        if not _valid_unit(row):
            raise ValueError(f"invalid batch review unit frame {frame}: checks, decision or unresolved issues")
        item = next(x for x in rows if f"{int(x['frame']):02d}" == frame)
        if any(row.get(k) != v for k, v in unit_binding(ep, item).items()):
            raise ValueError(f"batch review unit SHA drift frame {frame}")
    q = read_json(ep / QUEUE_REL)
    previous = read_json(final_path(ep, batch_id)) if final_path(ep, batch_id).is_file() else {}
    history = [*(previous.get("unit_history") or []), *(previous.get("frames") or []), *(data.get("unit_history") or [])]
    item_by_frame = {f"{int(x.get('frame') or 0):02d}": x for x in q.get("items") or [] if x.get("batch_id") == batch_id}
    for frame, review in by_frame.items():
        item = item_by_frame.get(frame)
        if not item:
            continue
        decision = review["decision"]
        item["work_batch_review"] = {"decision": decision, "reason": review.get("reason"), "issue_codes": review.get("issue_codes") or []}
        if decision == "REPAIR_NOW":
            _ledger_review(ep, int(frame), "repair", "WORK batch actual-pixel review: " + str(review.get("reason") or "clear visible defect"))
            item["status"] = "scout_repair"
        else:
            item["status"] = "generated"
    final = {**data, "schema_version": 1, "batch_id": batch_id, "review_scope": "EARLY_BATCH_ACTUAL_PIXELS",
             "final_pass_authority": False, "critic_provenance": provenance, "unit_history": history}
    out = final_path(ep, batch_id); write_json(out, final); write_json(ep / QUEUE_REL, q)
    product_review_adapter.mark_complete(ep, kind(batch_id), attempt=attempt, final_path=out)
    candidate.unlink(missing_ok=True)
    return final


def finalize(ep: Path, batch_id: str, *, runtime: str = "WORK", attempt: int = 1) -> dict:
    with image_scheduler.queue_transaction(ep):
        return _finalize_locked(ep, batch_id, runtime=runtime, attempt=attempt)


def pending(ep: Path) -> list[str]:
    q = read_json(Path(ep) / QUEUE_REL)
    return sorted({str(x.get("batch_id")) for x in q.get("items") or [] if x.get("status") == "review_pending" and x.get("batch_id")})


def self_test() -> None:
    assert kind("BATCH-001") == "production-batch-batch-001"
    assert VALID == {"PASS_PREVIEW", "REPAIR_NOW", "UNCERTAIN"}
    print("PRODUCTION BATCH REVIEW V2.6.1 H1 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__); sub = ap.add_subparsers(dest="cmd", required=True)
    p=sub.add_parser("prepare");p.add_argument("episode_dir");p.add_argument("batch_id");p.add_argument("--attempt",type=int,default=1)
    p=sub.add_parser("finalize");p.add_argument("episode_dir");p.add_argument("batch_id");p.add_argument("--attempt",type=int,default=1);p.add_argument("--runtime",choices=["WORK","WEB"],default="WORK")
    p=sub.add_parser("pending");p.add_argument("episode_dir")
    p=sub.add_parser("record-unit");p.add_argument("episode_dir");p.add_argument("batch_id");p.add_argument("--file",required=True)
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="record-unit":print(json.dumps(record_unit(ep,a.batch_id,read_json(Path(a.file))),ensure_ascii=False,indent=2));return 0
    if a.cmd=="prepare":print(json.dumps(prepare(ep,a.batch_id,attempt=a.attempt),ensure_ascii=False,indent=2));return product_review_adapter.HOST_ACTION_REQUIRED_RC
    if a.cmd=="finalize":print(json.dumps(finalize(ep,a.batch_id,runtime=a.runtime,attempt=a.attempt),ensure_ascii=False,indent=2));return 0
    print(json.dumps({"pending_batches":pending(ep)},ensure_ascii=False,indent=2));return 0

if __name__=="__main__":raise SystemExit(main())
