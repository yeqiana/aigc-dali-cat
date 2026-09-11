#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS P1-1 Identity Pixel Continuity evidence contract.

The EP003 Production Exposure Audit proved Story OS could show a reference image
reached the provider (W-21) but could not show that the same person was kept
across frames. This module owns the frame-level evidence contract that closes
that gap. It is evidence plumbing only: no CLIP, no FaceNet, no third-party
vision service, no scoring model. Identity is judged by an auto/human/delegated
reviewer and the judgement is recorded with provenance.

Recorded inside meta/frame-reviews/{frame}.json::

    "identity_evidence": {
      "required": true,
      "characters": [
        {
          "character_id": "P01",
          "reference_anchor": {"path": "<repo-relative>", "sha256": "<64 hex>"},
          "evaluation": {
            "identity_consistent": true,
            "confidence": 1.0,
            "method": "auto_review|human_review|delegated_review detail"
          }
        }
      ],
      "provenance": {
        "source": "auto_review|human_review|delegated_review",
        "reviewer": "<who>",
        "reviewed_at": "<iso>"
      }
    }

A single-character shorthand (character_id / reference_anchor / evaluation at the
top level) is also accepted so the literal audit shape keeps working.

The gate never accepts "character-contract.json exists" as evidence. It reads the
frame review and cross-checks the anchor SHA-256 against both the frame declared
identity reference and the story-gates reference registry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import story_json

ROOT = Path(__file__).resolve().parents[2]
GATES_REL = Path("meta/story-gates.json")
LEDGER_REL = Path("meta/production-ledger.json")
REVIEW_DIR = Path("meta/frame-reviews")
CHARACTER_CONTRACT_REL = Path("meta/character-contract.json")
CHARACTER_CROPS_REL = Path("meta/character-master-crops.json")
PIXEL_MASTER_REL = Path("meta/character-pixel-master.json")
PROVENANCE_SOURCES = ("auto_review", "human_review", "delegated_review")
# A character id must stand alone (P01, "...:P01", "P02_face"); a bare
# substring like the "p00" inside "ep001-couple-selfie" must not qualify.
P_ID_RE = re.compile(r"(?<![A-Za-z0-9])(P\d{2})(?![0-9])", re.I)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path, default=None):
    # Lenient read preserving the original fail-soft contract (any parse error ->
    # default); the shared canonical implementation owns the actual parsing.
    return story_json.read_json(path, default=default, require_object=False)


def write_json(path, data) -> None:
    story_json.write_json(path, data)


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_rel(path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def repo_abs(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw.strip())
    candidate = candidate.resolve() if candidate.is_absolute() else (ROOT / candidate).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def protagonist_id(ep) -> str:
    data = read_json(Path(ep) / CHARACTER_CONTRACT_REL, {}) or {}
    pov = data.get("pov") if isinstance(data.get("pov"), dict) else {}
    return str(pov.get("character_id") or "P01")


def identity_reference_items(gates) -> list:
    visual = gates.get("visual") if isinstance(gates, dict) and isinstance(gates.get("visual"), dict) else {}
    refs = visual.get("references") if isinstance(visual.get("references"), dict) else {}
    items = []
    for item in refs.get("items") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("reference_kind") or item.get("kind") or "") != "identity":
            continue
        items.append(item)
    return items


def anchor_of(item) -> dict | None:
    path = repo_abs(item.get("path"))
    if path is None or not path.is_file():
        return None
    return {"path": repo_rel(path), "sha256": sha256_file(path)}


def character_id_of(item, ep) -> str | None:
    explicit = item.get("character_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().upper()
    for field in ("role", "id", "anchor"):
        match = P_ID_RE.search(str(item.get(field) or ""))
        if match:
            return match.group(1).upper()
    anchor = str(item.get("anchor") or "").lower()
    if "protagonist" in anchor or "pov" in anchor:
        return protagonist_id(ep)
    return None


def frame_scope_of(item):
    scope = item.get("frames") or item.get("frame_scope")
    if not isinstance(scope, list):
        return None
    normalized = set()
    for value in scope:
        try:
            normalized.add(int(value))
        except Exception:
            pass
    return normalized or None


def identity_contract(ep) -> dict:
    """Episode-level identity authority derived from story-gates references."""
    ep = Path(ep)
    gates = read_json(ep / GATES_REL, {}) or {}
    visual = gates.get("visual") if isinstance(gates.get("visual"), dict) else {}
    refs = visual.get("references") if isinstance(visual.get("references"), dict) else {}
    declared = refs.get("required") is True
    items = identity_reference_items(gates)
    characters = {}
    for item in items:
        cid = character_id_of(item, ep)
        anchor = anchor_of(item)
        if cid and anchor:
            characters.setdefault(cid, anchor)
    return {
        "required": bool(declared and items and characters),
        "declared_required": declared,
        "characters": characters,
        "reference_count": len(items),
    }


def contract_requirements(ep, frame, refs=None) -> list:
    """Per-frame declared identity requirement for the Frame Contract (advisory).

    This is the identity scope the Frame Contract publishes; the gate still reads
    the frame review for execution evidence. It never changes contract_sha256.
    """
    ep = Path(ep)
    gates = read_json(ep / GATES_REL, {}) or {}
    out = []
    for item in identity_reference_items(gates):
        scope = frame_scope_of(item)
        if scope is not None and int(frame) not in scope:
            continue
        cid = character_id_of(item, ep)
        anchor = anchor_of(item)
        if not cid or not anchor:
            continue
        out.append({"character_id": cid, "reference_anchor": anchor})
    return out


def attempt_identity_requirements(attempt, ep) -> list:
    """Identity characters this generation attempt actually committed to."""
    if not isinstance(attempt, dict):
        return []
    request = attempt.get("request") if isinstance(attempt.get("request"), dict) else {}
    out = []
    for row in request.get("references") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("kind") or "") != "identity":
            continue
        cid = None
        for field in ("role", "id"):
            match = P_ID_RE.search(str(row.get(field) or ""))
            if match:
                cid = match.group(1).upper()
                break
        if cid is None:
            cid = character_id_of(row, ep)
        path = row.get("path")
        sha = row.get("sha256")
        if not cid or not path:
            continue
        out.append({"character_id": cid, "reference_anchor": {
            "path": str(path), "sha256": (str(sha).lower() if sha else None)}})
    return out


def accepted_attempt(frame) -> dict | None:
    """The generation attempt whose pixels the frame currently accepts."""
    if not isinstance(frame, dict):
        return None
    attempts = [a for a in (frame.get("attempts") or []) if isinstance(a, dict)]
    approved = frame.get("approved_asset") if isinstance(frame.get("approved_asset"), dict) else {}
    candidate = frame.get("current_candidate") if isinstance(frame.get("current_candidate"), dict) else {}
    for sha in (approved.get("source_sha256"), candidate.get("sha256")):
        token = str(sha or "")
        if not token:
            continue
        for attempt in reversed(attempts):
            if str((attempt.get("candidate") or {}).get("sha256") or "") == token:
                return attempt
    attempt_id = str(candidate.get("attempt_id") or "")
    if attempt_id:
        for attempt in reversed(attempts):
            if str(attempt.get("attempt_id") or "") == attempt_id:
                return attempt
    for attempt in reversed(attempts):
        if attempt.get("result") == "success":
            return attempt
    return None


def frame_requirements(ep, frame, ledger=None) -> list:
    ep = Path(ep)
    ledger = ledger if isinstance(ledger, dict) else (read_json(ep / LEDGER_REL, {}) or {})
    frames = ledger.get("frames") if isinstance(ledger.get("frames"), dict) else {}
    row = frames.get(f"{int(frame):02d}")
    if not isinstance(row, dict):
        return []
    return attempt_identity_requirements(accepted_attempt(row), ep)


def anchor_authority(ep) -> dict:
    """Repository authority SHA by anchor path (story-gates registry + identity masters)."""
    ep = Path(ep)
    out: dict[str, str] = {}
    for item in identity_reference_items(read_json(ep / GATES_REL, {}) or {}):
        anchor = anchor_of(item)
        if anchor:
            out[anchor["path"]] = anchor["sha256"]
    crops = read_json(ep / CHARACTER_CROPS_REL, {}) or {}
    for row in (crops.get("items") or {}).values():
        if isinstance(row, dict) and row.get("path") and row.get("sha256"):
            out.setdefault(str(row["path"]), str(row["sha256"]).lower())
    master = read_json(ep / PIXEL_MASTER_REL, {}) or {}
    if master.get("asset_path") and master.get("sha256"):
        out.setdefault(str(master["asset_path"]), str(master["sha256"]).lower())
    return out


def evidence_characters(evidence) -> list:
    if not isinstance(evidence, dict):
        return []
    rows = evidence.get("characters")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    if evidence.get("character_id"):
        return [evidence]
    return []


def evidence_from_review(review) -> dict | None:
    if not isinstance(review, dict):
        return None
    evidence = review.get("identity_evidence")
    return evidence if isinstance(evidence, dict) else None


def validate_frame(evidence, requirements, authority) -> list:
    """Return (code, message) findings proving frame-level identity continuity."""
    findings = []
    if not isinstance(evidence, dict):
        return [("identity_continuity_evidence_missing",
                 "frame requires an identity anchor but the frame review has no identity_evidence")]
    if evidence.get("required") is not True:
        findings.append(("identity_continuity_not_required",
                         "identity_evidence.required must be true"))
    presented = {}
    for row in evidence_characters(evidence):
        cid = str(row.get("character_id") or "").upper()
        if cid:
            presented[cid] = row
    for requirement in requirements:
        cid = str(requirement["character_id"]).upper()
        row = presented.get(cid)
        if row is None:
            findings.append(("identity_continuity_missing_character",
                             f"identity_evidence has no evaluation for {cid}"))
            continue
        anchor = row.get("reference_anchor")
        if not isinstance(anchor, dict) or not anchor.get("path") or not anchor.get("sha256"):
            findings.append(("identity_continuity_anchor_missing",
                             f"{cid}: identity_evidence.reference_anchor needs path and sha256"))
            continue
        want = requirement["reference_anchor"]
        got_path = str(anchor.get("path"))
        got_sha = str(anchor.get("sha256") or "").lower()
        want_path = str(want.get("path") or "")
        want_sha = str(want.get("sha256") or "").lower()
        if got_path != want_path:
            findings.append(("identity_continuity_anchor_mismatch",
                             f"{cid}: evidence anchor {got_path} != declared {want_path}"))
        if want_sha and got_sha != want_sha:
            findings.append(("identity_continuity_hash_drift",
                             f"{cid}: evidence sha {got_sha[:12]} != declared sha {want_sha[:12]}"))
        authority_sha = authority.get(got_path) or authority.get(want_path)
        if authority_sha and str(authority_sha).lower() != got_sha:
            findings.append(("identity_continuity_authority_drift",
                             f"{cid}: current authority sha {str(authority_sha)[:12]} != evidence sha {got_sha[:12]}"))
        evaluation = row.get("evaluation")
        if not isinstance(evaluation, dict):
            findings.append(("identity_continuity_evaluation_missing",
                             f"{cid}: identity_evidence.evaluation is required"))
            continue
        if evaluation.get("identity_consistent") is not True:
            findings.append(("identity_continuity_not_consistent",
                             f"{cid}: evaluation.identity_consistent must be true"))
        confidence = evaluation.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            findings.append(("identity_continuity_confidence_missing",
                             f"{cid}: evaluation.confidence must be a number"))
        if not str(evaluation.get("method") or "").strip():
            findings.append(("identity_continuity_method_missing",
                             f"{cid}: evaluation.method must record how identity was judged"))
    provenance = evidence.get("provenance")
    if not isinstance(provenance, dict) or str(provenance.get("source") or "") not in PROVENANCE_SOURCES:
        findings.append(("identity_continuity_provenance_missing",
                         "identity_evidence.provenance.source must be one of " + "/".join(PROVENANCE_SOURCES)))
    return findings


def review_path(ep, frame) -> Path:
    return Path(ep).resolve() / REVIEW_DIR / f"{int(frame):02d}.json"


def verify(ep, *, ledger=None, metadata_only=False) -> list:
    ep = Path(ep).resolve()
    if metadata_only:
        return []
    contract = identity_contract(ep)
    if not contract.get("required"):
        return []
    ledger = ledger if isinstance(ledger, dict) else (read_json(ep / LEDGER_REL, {}) or {})
    marker = ledger.get("identity_continuity_evidence")
    if not isinstance(marker, dict) or marker.get("schema_version") != 1:
        # Ledger produced before identity continuity evidence existed: legacy scope.
        return []
    enforced_from = str(marker.get("enforced_from") or "")
    authority = anchor_authority(ep)
    errors = []
    frames = ledger.get("frames") if isinstance(ledger.get("frames"), dict) else {}
    for key in sorted(frames):
        attempt = accepted_attempt(frames.get(key))
        if not isinstance(attempt, dict):
            continue
        requirements = attempt_identity_requirements(attempt, ep)
        if not requirements:
            continue
        started_at = str(attempt.get("started_at") or "")
        if enforced_from and started_at and started_at < enforced_from:
            continue
        review = read_json(review_path(ep, int(key)), {}) or {}
        for code, message in validate_frame(evidence_from_review(review), requirements, authority):
            errors.append(f"frame {key}: {code}: {message}")
    return errors


def attach(ep, frame, *, character_id, method, source, confidence, anchor_path=None, anchor_sha256=None,
           reviewer=None, consistent=True, write=True) -> dict:
    """Merge one character identity evaluation into meta/frame-reviews/{frame}.json."""
    ep = Path(ep).resolve()
    path = review_path(ep, frame)
    review = read_json(path)
    if not isinstance(review, dict):
        raise ValueError(f"frame review missing or invalid: {path}")
    if anchor_path is None:
        raise ValueError("anchor_path is required")
    resolved = repo_abs(anchor_path)
    if resolved is not None and resolved.is_file():
        anchor_path = repo_rel(resolved)
        if anchor_sha256 is None:
            anchor_sha256 = sha256_file(resolved)
    if anchor_sha256 is None:
        raise ValueError(f"anchor_path not found in repository: {anchor_path}")
    evidence = evidence_from_review(review) or {"required": True, "characters": [], "provenance": {}}
    characters = evidence_characters(evidence)
    entry = {
        "character_id": str(character_id).upper(),
        "reference_anchor": {"path": str(anchor_path), "sha256": str(anchor_sha256).lower()},
        "evaluation": {
            "identity_consistent": bool(consistent),
            "confidence": float(confidence),
            "method": str(method),
        },
    }
    characters = [row for row in characters
                  if str(row.get("character_id") or "").upper() != entry["character_id"]] + [entry]
    evidence.update({
        "required": True,
        "characters": characters,
        "provenance": {"source": str(source), "reviewer": reviewer, "reviewed_at": now()},
    })
    review["identity_evidence"] = evidence
    if write:
        write_json(path, review)
    return review


def self_test() -> None:
    assert character_id_of({"anchor": "P02_face"}, ROOT) == "P02"
    assert character_id_of({"anchor": "protagonist_identity"}, ROOT) == protagonist_id(ROOT)
    assert character_id_of({"role": "series_character_identity:P01"}, ROOT) == "P01"
    assert frame_scope_of({"frames": ["1", "3"]}) == {1, 3}
    assert frame_scope_of({}) is None
    print("IDENTITY CONTINUITY EVIDENCE SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("contract"); p.add_argument("episode_dir")
    p = sub.add_parser("requirements"); p.add_argument("episode_dir"); p.add_argument("--frame", type=int)
    p = sub.add_parser("verify"); p.add_argument("episode_dir")
    p = sub.add_parser("attach")
    p.add_argument("episode_dir"); p.add_argument("--frame", type=int, required=True)
    p.add_argument("--character", required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--source", choices=list(PROVENANCE_SOURCES), required=True)
    p.add_argument("--confidence", type=float, required=True)
    p.add_argument("--anchor-path")
    p.add_argument("--anchor-sha256")
    p.add_argument("--reviewer")
    p.add_argument("--inconsistent", action="store_true")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    ep = Path(args.episode_dir).resolve()
    if args.cmd == "contract":
        print(json.dumps(identity_contract(ep), ensure_ascii=False, indent=2)); return 0
    if args.cmd == "requirements":
        if args.frame:
            print(json.dumps(frame_requirements(ep, args.frame), ensure_ascii=False, indent=2)); return 0
        ledger = read_json(ep / LEDGER_REL, {}) or {}
        rows = {key: frame_requirements(ep, int(key), ledger) for key in sorted((ledger.get("frames") or {}).keys())}
        print(json.dumps(rows, ensure_ascii=False, indent=2)); return 0
    if args.cmd == "attach":
        review = attach(ep, args.frame, character_id=args.character, method=args.method, source=args.source,
                        confidence=args.confidence, anchor_path=args.anchor_path,
                        anchor_sha256=args.anchor_sha256, reviewer=args.reviewer, consistent=not args.inconsistent)
        print(json.dumps(review.get("identity_evidence"), ensure_ascii=False, indent=2)); return 0
    errors = verify(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("IDENTITY CONTINUITY EVIDENCE VERIFIED"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
