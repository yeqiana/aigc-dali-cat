#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WORK/WEB actual-pixel review barrier for one generated Production logical batch.

This is an early content-repair gate, never final Production PASS authority.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import frame_contract
import product_review_adapter
import runtime_router

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = Path(__file__).resolve().parent
QUEUE_REL = Path("meta/production-queue.json")
REVIEW_DIR = Path("meta/runtime/batch-reviews")
VALID = {"PASS_PREVIEW", "REPAIR_NOW", "UNCERTAIN"}


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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


def batch_items(ep: Path, batch_id: str) -> list[dict]:
    q = read_json(ep / QUEUE_REL)
    rows = [x for x in q.get("items") or [] if isinstance(x, dict) and x.get("batch_id") == batch_id and x.get("output_path")]
    return sorted(rows, key=lambda x: int(x.get("frame") or 0))


def prompt(ep: Path, batch_id: str, rows: list[dict], candidate: Path) -> str:
    contracts = []
    for row in rows:
        frame = int(row["frame"])
        c = frame_contract.compile_frame(ep, frame, write_cache=True)
        contracts.append({"frame": f"{frame:02d}", "contract_sha256": c["contract_sha256"], "prompt_contract": c["prompt_contract"]})
    return f"""You are a fresh WORK_ISOLATED actual-pixel reviewer for one Story OS Production logical batch.
This is an EARLY repair barrier, not final Production PASS authority.
Inspect every attached generated image against its locked Frame Contract and visible continuity.
Use REPAIR_NOW only for clear visible defects worth spending the one content repair on now.
Use PASS_PREVIEW when the frame is clearly usable so production may continue.
Use UNCERTAIN when final full-frame-set review should decide; UNCERTAIN must not trigger repair.
Check identity, wardrobe, props, weather/physics, POV/camera authorship, scene identity, anomaly readability/scale, and obvious continuity drift.
Do not penalize a large/impossible anomaly merely for being impossible; judge capture credibility and contract fidelity.
Batch: {batch_id}
Frame contracts:
{json.dumps(contracts, ensure_ascii=False, indent=2)}
Write ONLY JSON to {candidate.relative_to(ROOT).as_posix()} with schema:
{{"batch_id":"{batch_id}","frames":[{{"frame":"01","decision":"PASS_PREVIEW|REPAIR_NOW|UNCERTAIN","issue_codes":[],"reason":"visible evidence","confidence":0.0}}],"summary":"brief"}}
Return exactly one row for every supplied frame.
"""


def prepare(ep: Path, batch_id: str, *, attempt: int = 1) -> dict:
    ep = ep.resolve(); rows = batch_items(ep, batch_id)
    if not rows:
        raise ValueError(f"batch has no generated reviewable items: {batch_id}")
    runtime, _ = runtime_router.detect()
    if runtime not in {"WORK", "WEB"}:
        raise ValueError("production batch product review is for WORK/WEB only")
    candidate = candidate_path(ep, batch_id)
    sources: list[Path] = []
    for row in rows:
        sources.append(repo_file(str(row["output_path"])))
        prov = frame_contract.provenance(ep, int(row["frame"]))
        if prov and prov.get("path"):
            sources.append(repo_file(str(prov["path"])))
    request = product_review_adapter.prepare(
        ep, kind=kind(batch_id), runtime=runtime, attempt=attempt,
        prompt=prompt(ep, batch_id, rows, candidate), source_paths=sources, candidate_path=candidate)
    q = read_json(ep / QUEUE_REL)
    ids = {x.get("id") for x in rows}
    for row in q.get("items") or []:
        if row.get("id") in ids and row.get("status") == "generated":
            row["status"] = "review_pending"
            row["batch_review_request"] = request.get("request_path")
    write_json(ep / QUEUE_REL, q)
    return request


def _ledger_review(ep: Path, frame: int, decision: str, notes: str) -> None:
    cp = subprocess.run(
        [sys.executable, str(SYSTEM / "production_ledger.py"), "review", str(ep), "--frame", f"{frame:02d}",
         "--decision", decision, "--notes", notes[:500]],
        cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace")
    if cp.returncode != 0:
        raise RuntimeError(f"production ledger review failed frame={frame:02d}: {cp.stdout[-1000:]}")


def finalize(ep: Path, batch_id: str, *, runtime: str = "WORK", attempt: int = 1) -> dict:
    ep = ep.resolve(); candidate = candidate_path(ep, batch_id)
    data, provenance = product_review_adapter.finalize_candidate(
        ep, kind=kind(batch_id), runtime=runtime, attempt=attempt, candidate_path=candidate)
    if str(data.get("batch_id") or "") != batch_id:
        raise ValueError("batch review batch_id mismatch")
    rows = batch_items(ep, batch_id)
    expected = {f"{int(x['frame']):02d}" for x in rows}
    reviewed = data.get("frames")
    if not isinstance(reviewed, list):
        raise ValueError("batch review frames must be list")
    by_frame = {str(x.get("frame") or "").zfill(2): x for x in reviewed if isinstance(x, dict)}
    if set(by_frame) != expected:
        raise ValueError(f"batch review frame set mismatch: expected={sorted(expected)} got={sorted(by_frame)}")
    for frame, row in by_frame.items():
        if row.get("decision") not in VALID:
            raise ValueError(f"invalid batch review decision frame {frame}: {row.get('decision')}")
        if row.get("decision") == "REPAIR_NOW" and not (row.get("issue_codes") or []):
            raise ValueError(f"REPAIR_NOW requires issue_codes frame {frame}")
    q = read_json(ep / QUEUE_REL)
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
    final = {"schema_version": 1, "batch_id": batch_id, "review_scope": "EARLY_BATCH_ACTUAL_PIXELS",
             "final_pass_authority": False, "critic_provenance": provenance, **data}
    out = final_path(ep, batch_id); write_json(out, final); write_json(ep / QUEUE_REL, q)
    product_review_adapter.mark_complete(ep, kind(batch_id), attempt=attempt, final_path=out)
    candidate.unlink(missing_ok=True)
    return final


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
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    ep=Path(a.episode_dir).resolve()
    if a.cmd=="prepare":print(json.dumps(prepare(ep,a.batch_id,attempt=a.attempt),ensure_ascii=False,indent=2));return product_review_adapter.HOST_ACTION_REQUIRED_RC
    if a.cmd=="finalize":print(json.dumps(finalize(ep,a.batch_id,runtime=a.runtime,attempt=a.attempt),ensure_ascii=False,indent=2));return 0
    print(json.dumps({"pending_batches":pending(ep)},ensure_ascii=False,indent=2));return 0

if __name__=="__main__":raise SystemExit(main())
