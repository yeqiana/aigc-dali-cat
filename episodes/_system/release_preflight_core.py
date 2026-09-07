#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_preflight shared core (B4 split): constants, path helpers, registry primitives and the bootstrap-registry command."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from story_os_contract import story_os_version
import text_encoding_health
import story_json

ROOT = Path(__file__).resolve().parents[2]

MIN_CONTRACT = (2, 0, 3, 5)

WEIGHTS = {
    "core_anomaly_mechanism": 25,
    "story_engine": 15,
    "entry_mode": 10,
    "anomaly_carrier": 10,
    "primary_visual_space": 10,
    "middle_escalation": 10,
    "climax_form": 10,
    "relationship": 5,
    "reality_residue": 5,
}

FINGERPRINT_KEYS = tuple(WEIGHTS)

RECENT5_REL = Path("meta/recent5-review.json")

ENABLE_REL = Path("meta/release-guard-enabled.json")

RELEASE_REVIEW_REL = Path("meta/release-semantic-review.json")

RELEASE_CANDIDATE_REL = Path("meta/.release-semantic-review.candidate.json")

COMPLIANCE_REL = Path("meta/publish-compliance.json")

REGISTRY_REL = Path("reports/account-pattern-registry.json")

SERIES_CONTINUITY_NAME = "series-continuity.json"

RELEASE_CHECKS = (
    "cover_title_match",
    "cover_frame01_handoff",
    "first3_coherence",
    "climax_upgrade",
    "payoff_honesty",
    "description_consistency",
    "no_caption_invented_core_evidence",
    "subtitle_left_middle_and_unobstructed",
    "caption_conversational_hook_quality",
)

GOV_CHECKS = (
    "ai_generated_declared",
    "platform_ai_label_planned",
    "fiction_context_not_misrepresented_as_official_fact",
    "no_unverifiable_real_group_accusation",
    "real_location_handled_as_fictional_story_context",
)

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

def read_json(path: Path) -> dict:
    return story_json.read_json(path)

def write_json(path: Path, data: dict) -> None:
    story_json.write_json(path, data)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def sha256_json(data: object) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:
        return (0,)

def episode_contract_version(ep: Path) -> str:
    versions: list[tuple[tuple[int, ...], str]] = []
    for rel in ("meta/episode-state.json", "meta/release-manifest.json", "meta/story-gates.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            raw = str(read_json(p).get("tool_version") or "")
            vt = version_tuple(raw)
            if vt != (0,):
                versions.append((vt, raw))
        except Exception:
            continue
    if versions:
        return max(versions, key=lambda x: x[0])[1]
    return story_os_version()

def guard_required(ep: Path) -> bool:
    if (ep / ENABLE_REL).is_file():
        return True
    return version_tuple(episode_contract_version(ep)) >= MIN_CONTRACT

def repo_file(raw: object, where: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{where} missing")
    rel = Path(raw.strip())
    p = rel.resolve() if rel.is_absolute() else (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{where} escapes repository: {raw}") from exc
    if not p.is_file():
        raise ValueError(f"{where} missing: {raw}")
    return p

def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()

def ep_path(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    return ep

def fingerprint_complete(data: dict) -> bool:
    dims = data.get("dimensions")
    structurally_complete = (
        isinstance(data.get("episode_id"), str)
        and bool(data.get("episode_id").strip())
        and isinstance(data.get("title"), str)
        and bool(data.get("title").strip())
        and isinstance(dims, dict)
        and all(isinstance(dims.get(k), str) and dims.get(k).strip() for k in FINGERPRINT_KEYS)
    )
    return bool(structurally_complete and not text_encoding_health.json_text_errors(data, label="episode-fingerprint"))

def normalized(value: object) -> str:
    return " ".join(str(value or "").strip().lower().split())

def similarity(a: dict, b: dict) -> tuple[int, bool, list[str]]:
    da = a.get("dimensions") or {}
    db = b.get("dimensions") or {}
    matched = []
    score = 0
    for key, weight in WEIGHTS.items():
        x, y = normalized(da.get(key)), normalized(db.get(key))
        if x and x == y:
            score += weight
            matched.append(key)
    veto_keys = ("core_anomaly_mechanism", "middle_escalation", "climax_form")
    veto = all(normalized(da.get(k)) and normalized(da.get(k)) == normalized(db.get(k)) for k in veto_keys)
    return score, veto, matched

def load_registry() -> dict:
    p = ROOT / REGISTRY_REL
    if not p.is_file():
        return {"schema_version": 1, "story_os_version": story_os_version(), "episodes": []}
    data = read_json(p)
    encoding_errors = text_encoding_health.json_text_errors(data, label="account-pattern-registry")
    if encoding_errors:
        raise ValueError("account-pattern-registry text encoding invalid: " + "; ".join(encoding_errors[:8]))
    return data

def registry_sha() -> str:
    p = ROOT / REGISTRY_REL
    return sha256_file(p) if p.is_file() else sha256_json({"episodes": []})

def cmd_bootstrap_registry(_args: argparse.Namespace) -> int:
    reg = load_registry()
    existing = {str(x.get("episode_id")): x for x in reg.get("episodes", []) if isinstance(x, dict)}
    import episode_discovery
    candidates = []
    for fp_path in episode_discovery.iter_fingerprint_paths(ROOT / "episodes"):
        try:
            fp = read_json(fp_path)
        except Exception:
            continue
        if not fingerprint_complete(fp):
            continue
        ep = fp_path.parents[1]
        published_at = ""
        updated_at = ""
        try:
            manifest = read_json(ep / "meta/release-manifest.json")
            published_at = str(((manifest.get("publication") or {}).get("published_at")) or "")
        except Exception:
            pass
        try:
            state = read_json(ep / "meta/episode-state.json")
            updated_at = str(state.get("updated_at") or "")
        except Exception:
            pass
        candidates.append((published_at or updated_at, ep.as_posix(), fp))
    candidates.sort(key=lambda row: (row[0], row[1]))
    added = 0
    for _, _, fp in candidates:
        eid = fp["episode_id"]
        row = {
            "episode_id": eid,
            "title": fp["title"],
            "dimensions": fp["dimensions"],
            "source": "bootstrap_existing_real_fingerprint",
        }
        if eid not in existing:
            added += 1
        existing[eid] = row
    reg["story_os_version"] = story_os_version()
    reg["episodes"] = list(existing.values())
    write_json(ROOT / REGISTRY_REL, reg)
    print(f"REGISTRY BOOTSTRAP: real fingerprints={len(reg['episodes'])}, added={added}")
    if not reg["episodes"]:
        print("WARNING: no complete historical fingerprints found; do not invent them.")
    return 0

