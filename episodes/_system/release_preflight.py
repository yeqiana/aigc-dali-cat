#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.0.3.6 release-preflight hard gates.

Adds four P0 controls without adding an episode stage:
1) recent-5 evidence binding
2) optional/required series-lock SHA binding
3) final release semantic review bound to publish assets
4) AI/governance publication compliance evidence

Old episodes remain compatible unless explicitly enabled.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from story_os_contract import story_os_version
import caption_image_audit
import subtitle_layout
import visual_final_freeze
import runtime_router
import runtime_provenance
import product_review_adapter
import text_encoding_health
from fingerprint_semantics import (
    REVIEW_REL as RECENT5_SEMANTIC_REL,
    comparison_index as semantic_comparison_index,
    ensure_review as ensure_semantic_review,
    required as semantic_recent5_required,
    validate_review as validate_semantic_review,
    ProductReviewHostAction,
)

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
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

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

def recent5_history(current: dict, reg: dict) -> list[dict]:
    return [
        x for x in reg.get("episodes", [])
        if isinstance(x, dict) and x.get("episode_id") != current.get("episode_id")
    ][-5:]

def build_recent5(ep: Path, codex: str | None = None, timeout: int = 1800) -> dict:
    fp_path = ep / "meta/episode-fingerprint.json"
    if not fp_path.is_file():
        raise ValueError("meta/episode-fingerprint.json missing")
    current = read_json(fp_path)
    if not fingerprint_complete(current):
        raise ValueError("current episode fingerprint is incomplete")
    reg = load_registry()
    history = recent5_history(current, reg)
    if not history:
        raise ValueError(
            "account-pattern-registry has no historical fingerprints. "
            "Run bootstrap-registry and register real recent episodes; do not set recent5_checked=true manually."
        )

    contract_version = episode_contract_version(ep)
    semantic_required = semantic_recent5_required(contract_version)
    semantic_review = None
    semantic_by_id: dict[str, dict] = {}
    if semantic_required:
        registry_path = ROOT / REGISTRY_REL
        if not registry_path.is_file():
            raise ValueError("account-pattern-registry.json missing for semantic Recent-5 review")
        semantic_review = ensure_semantic_review(
            ROOT, ep, fp_path, registry_path, history, contract_version, codex, timeout
        )
        semantic_by_id = semantic_comparison_index(semantic_review)

    compared = []
    blocked = False
    max_score = 0
    for row in reversed(history):
        exact_score, exact_veto, exact_matched = similarity(current, row)
        sem = semantic_by_id.get(str(row.get("episode_id") or ""), {})
        semantic_score = int(sem.get("semantic_similarity_score") or 0) if semantic_required else 0
        semantic_veto = sem.get("semantic_mechanism_veto") is True if semantic_required else False
        semantic_matched = list(sem.get("semantic_matched_dimensions") or []) if semantic_required else []

        score = max(exact_score, semantic_score)
        veto = exact_veto or semantic_veto
        max_score = max(max_score, score)
        blocked = blocked or veto or score >= 55
        compared.append({
            "episode_id": row.get("episode_id"),
            "title": row.get("title"),
            "exact_similarity_score": exact_score,
            "semantic_similarity_score": semantic_score if semantic_required else None,
            "similarity_score": score,
            "exact_mechanism_veto": exact_veto,
            "semantic_mechanism_veto": semantic_veto if semantic_required else None,
            "mechanism_veto": veto,
            "exact_matched_dimensions": exact_matched,
            "semantic_matched_dimensions": semantic_matched,
            "matched_dimensions": sorted(set(exact_matched) | set(semantic_matched)),
        })

    result = {
        "schema_version": 2 if semantic_required else 1,
        "story_os_version": contract_version,
        "episode_id": current.get("episode_id"),
        "generated_at": now(),
        "candidate_fingerprint_path": repo_rel(fp_path),
        "candidate_fingerprint_sha256": sha256_file(fp_path),
        "registry_path": REGISTRY_REL.as_posix(),
        "registry_sha256": registry_sha(),
        "comparison_count": len(compared),
        "compared": compared,
        "max_similarity_score": max_score,
        "mechanism_veto": any(x["mechanism_veto"] for x in compared),
        "decision": "block_or_redesign" if blocked else "pass",
        "scoring_policy": "effective=max(exact_string,semantic_equivalence); veto=exact_veto OR semantic_veto",
        "note": (
            "V2.0.3.6 uses a fresh isolated semantic equivalence matrix so paraphrased/skin-swapped "
            "fingerprints cannot bypass Recent-5 by changing wording. Python, not the critic, computes scores."
        ),
    }
    if semantic_required and semantic_review is not None:
        semantic_path = ep / RECENT5_SEMANTIC_REL
        result["semantic_review_path"] = repo_rel(semantic_path)
        result["semantic_review_sha256"] = sha256_file(semantic_path)
    return result

def cmd_build_recent5(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    try:
        data = build_recent5(ep, codex=args.codex, timeout=args.timeout)
    except ProductReviewHostAction as exc:
        print(json.dumps(exc.request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC
    write_json(ep / RECENT5_REL, data)
    print(f"RECENT5: {data['decision'].upper()} max={data['max_similarity_score']} count={data['comparison_count']}")
    return 0 if data["decision"] == "pass" else 3

def verify_recent5_evidence(ep: Path) -> list[str]:
    if not guard_required(ep):
        return []
    p = ep / RECENT5_REL
    if not p.is_file():
        return ["meta/recent5-review.json missing; run release_preflight.py build-recent5 <episode>"]
    try:
        data = read_json(p)
        fp = repo_file(data.get("candidate_fingerprint_path"), "recent5.candidate_fingerprint_path")
    except Exception as exc:
        return [str(exc)]

    contract_version = episode_contract_version(ep)
    semantic_required = semantic_recent5_required(contract_version)
    errors = []
    expected_schema = 2 if semantic_required else 1
    if data.get("schema_version") != expected_schema:
        errors.append(f"recent5 schema_version must be {expected_schema} for contract {contract_version}")
    if sha256_file(fp).lower() != str(data.get("candidate_fingerprint_sha256") or "").lower():
        errors.append("recent5 candidate fingerprint SHA drift")
    if registry_sha().lower() != str(data.get("registry_sha256") or "").lower():
        errors.append("recent5 registry SHA drift; rebuild recent5 evidence")

    compared = data.get("compared")
    if not isinstance(compared, list) or not compared:
        errors.append("recent5 must compare at least one real registered historical episode")
    if isinstance(compared, list) and len(compared) > 5:
        errors.append("recent5 compared more than five episodes")

    semantic_index: dict[str, dict] = {}
    if semantic_required:
        sem_raw = data.get("semantic_review_path")
        if not isinstance(sem_raw, str) or not sem_raw.strip():
            errors.append("recent5 semantic_review_path missing for V2.0.3.6+")
        else:
            try:
                sem_path = repo_file(sem_raw, "recent5.semantic_review_path")
                if sha256_file(sem_path).lower() != str(data.get("semantic_review_sha256") or "").lower():
                    errors.append("recent5 semantic review SHA drift")
                sem_data = read_json(sem_path)
                current = read_json(fp)
                history = recent5_history(current, load_registry())
                sem_errors = validate_semantic_review(
                    ROOT, ep, fp, ROOT / REGISTRY_REL, history, contract_version, sem_data
                )
                errors.extend(["semantic_review: " + x for x in sem_errors])
                semantic_index = semantic_comparison_index(sem_data)
            except Exception as exc:
                errors.append("semantic_review: " + str(exc))

    if isinstance(compared, list):
        for idx, row in enumerate(compared):
            if not isinstance(row, dict):
                errors.append(f"recent5 compared[{idx}] must be object")
                continue
            effective = row.get("similarity_score")
            veto = row.get("mechanism_veto")
            if semantic_required:
                eid = str(row.get("episode_id") or "")
                sem = semantic_index.get(eid)
                if sem is None:
                    errors.append(f"recent5 compared[{idx}] missing semantic comparison")
                    continue
                exact_score = row.get("exact_similarity_score")
                semantic_score = row.get("semantic_similarity_score")
                if not isinstance(exact_score, int) or not isinstance(semantic_score, int):
                    errors.append(f"recent5 compared[{idx}] exact/semantic scores must be ints")
                    continue
                expected_effective = max(exact_score, semantic_score)
                expected_veto = (row.get("exact_mechanism_veto") is True) or (row.get("semantic_mechanism_veto") is True)
                if semantic_score != sem.get("semantic_similarity_score"):
                    errors.append(f"recent5 compared[{idx}] semantic score drift")
                if (row.get("semantic_mechanism_veto") is True) != (sem.get("semantic_mechanism_veto") is True):
                    errors.append(f"recent5 compared[{idx}] semantic veto drift")
                if effective != expected_effective:
                    errors.append(f"recent5 compared[{idx}] effective score must be max(exact,semantic)")
                if (veto is True) != expected_veto:
                    errors.append(f"recent5 compared[{idx}] effective veto must OR exact+semantic")
            elif not isinstance(effective, int):
                errors.append(f"recent5 compared[{idx}] similarity_score must be int")

    if data.get("decision") != "pass":
        errors.append(f"recent5 decision is {data.get('decision')!r}; redesign before Story Lock")
    if data.get("mechanism_veto") is True:
        errors.append("recent5 mechanism skin-swap veto triggered")
    score = data.get("max_similarity_score")
    if not isinstance(score, int) or score >= 55:
        errors.append(f"recent5 max_similarity_score must be <55 for this strict guard; got {score!r}")
    return errors

def series_meta(ep: Path) -> Path:
    return ep.parent / "meta"

def series_lock_path(ep: Path) -> Path:
    return series_meta(ep) / "series-lock.json"

def series_continuity_path(ep: Path) -> Path:
    return series_meta(ep) / SERIES_CONTINUITY_NAME

def series_continuity_status(ep: Path) -> tuple[bool, list[str]]:
    """Return whether continuity is explicitly enabled plus declaration errors.

    Directory sibling count is intentionally NOT a signal. A content category may
    contain many unrelated episodes. Continuous-world semantics must be explicit.
    """
    p = series_continuity_path(ep)
    if not p.is_file():
        return False, []
    try:
        data = read_json(p)
    except Exception as exc:
        return True, [f"invalid series continuity declaration: {exc}"]
    enabled = data.get("enabled")
    if enabled is False:
        return False, []
    if enabled is not True:
        return True, ["series-continuity.json enabled must be true or false"]
    errors = []
    if not str(data.get("series_id") or "").strip():
        errors.append("series-continuity.json series_id required when enabled=true")
    return True, errors

def series_lock_required(ep: Path) -> bool:
    if not guard_required(ep):
        return False
    if series_lock_path(ep).is_file():
        return True
    enabled, _ = series_continuity_status(ep)
    return enabled

def write_series_continuity(series_dir: Path, series_id: str, source: str) -> Path:
    out = series_dir / "meta" / SERIES_CONTINUITY_NAME
    write_json(out, {
        "schema_version": 1,
        "story_os_version": story_os_version(),
        "enabled": True,
        "series_id": series_id.strip(),
        "declared_at": now(),
        "source": source,
    })
    return out

def cmd_declare_series(args: argparse.Namespace) -> int:
    series_dir = Path(args.series_dir).resolve()
    try:
        series_dir.relative_to((ROOT / "episodes").resolve())
    except ValueError:
        raise SystemExit("series_dir must be inside repository episodes/")
    if not series_dir.is_dir():
        raise SystemExit(f"series directory not found: {series_dir}")
    series_id = str(args.series_id or series_dir.name).strip()
    if not series_id:
        raise SystemExit("series_id must not be empty")
    out = write_series_continuity(series_dir, series_id, "explicit_declare_series")
    print(f"SERIES CONTINUITY: ENABLED {out.relative_to(ROOT)}")
    return 0

def cmd_init_series_lock(args: argparse.Namespace) -> int:
    series_dir = Path(args.series_dir).resolve()
    try:
        series_dir.relative_to((ROOT / "episodes").resolve())
    except ValueError:
        raise SystemExit("series_dir must be inside repository episodes/")
    source = Path(args.source).resolve()
    data = read_json(source)
    anchors = data.get("anchors")
    rules = data.get("world_rules")
    if not isinstance(anchors, list) or not anchors:
        raise SystemExit("series lock source requires non-empty anchors[]")
    if not isinstance(rules, list) or not rules:
        raise SystemExit("series lock source requires non-empty world_rules[]")
    data["schema_version"] = 1
    data["story_os_version"] = story_os_version()
    data["approved"] = True
    data["locked_at"] = now()
    series_id = str(data.get("series_id") or series_dir.name).strip()
    write_series_continuity(series_dir, series_id, "init_series_lock")
    out = series_dir / "meta/series-lock.json"
    write_json(out, data)
    print(f"SERIES LOCK: {out.relative_to(ROOT)} sha256={sha256_file(out)}")
    return 0

def cmd_bind_series(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    lock = series_lock_path(ep)
    if not lock.is_file():
        raise SystemExit("series-lock.json missing; run init-series-lock first")
    binding = {
        "schema_version": 1,
        "story_os_version": episode_contract_version(ep),
        "series_lock_path": repo_rel(lock),
        "series_lock_sha256": sha256_file(lock),
        "bound_at": now(),
    }
    write_json(ep / "meta/series-lock-binding.json", binding)
    print("SERIES BIND: PASS")
    return 0

def verify_series_lock(ep: Path) -> list[str]:
    if not guard_required(ep):
        return []
    declared, declaration_errors = series_continuity_status(ep)
    lock = series_lock_path(ep)
    if not lock.is_file() and not declared:
        return []
    errors = list(declaration_errors)
    binding = ep / "meta/series-lock-binding.json"
    if not lock.is_file():
        errors.append("explicit continuous series requires <series>/meta/series-lock.json")
        return errors
    if not binding.is_file():
        return ["meta/series-lock-binding.json missing; run bind-series"]
    try:
        ld = read_json(lock)
        bd = read_json(binding)
    except Exception as exc:
        return [str(exc)]
    if ld.get("approved") is not True:
        errors.append("series lock must be approved=true")
    if not isinstance(ld.get("world_rules"), list) or not ld.get("world_rules"):
        errors.append("series lock world_rules[] required")
    if not isinstance(ld.get("anchors"), list) or not ld.get("anchors"):
        errors.append("series lock anchors[] required")
    for idx, row in enumerate(ld.get("anchors") or []):
        if not isinstance(row, dict) or not str(row.get("id") or "").strip() or not str(row.get("contract") or "").strip():
            errors.append(f"series lock anchor[{idx}] requires id + contract")
    actual = sha256_file(lock)
    if str(bd.get("series_lock_sha256") or "").lower() != actual.lower():
        errors.append("series lock SHA drift; re-bind episode")
    if str(bd.get("series_lock_path") or "") != repo_rel(lock):
        errors.append("series lock binding path mismatch")
    return errors

def load_manifest(ep: Path) -> dict:
    return read_json(ep / "meta/release-manifest.json")

def release_artifacts(ep: Path) -> dict[str, Path]:
    manifest = load_manifest(ep)
    release = manifest.get("release") or {}
    artifacts = manifest.get("artifacts") or {}
    publish_dir_raw = release.get("publish_dir")
    if not isinstance(publish_dir_raw, str) or not publish_dir_raw.strip():
        raise ValueError("manifest.release.publish_dir missing")
    publish_dir = (ROOT / publish_dir_raw).resolve()
    body_glob = str(release.get("body_glob") or "").strip()
    if not body_glob:
        raise ValueError("manifest.release.body_glob missing")
    body = sorted(p for p in publish_dir.glob(body_glob) if p.is_file())
    if len(body) < 3:
        raise ValueError("release requires at least 3 final body images")
    cover = repo_file(release.get("cover_path"), "manifest.release.cover_path")
    captions = repo_file(artifacts.get("captions"), "manifest.artifacts.captions")
    publish_copy = repo_file(artifacts.get("publish_copy"), "manifest.artifacts.publish_copy")
    propagation = repo_file(artifacts.get("propagation_card"), "manifest.artifacts.propagation_card")
    gates = read_json(ep / "meta/story-gates.json")
    story = gates.get("story") or {}
    climax = story.get("climax_frame")
    payoff = story.get("payoff_frame")
    def frame_for(n: object) -> Path:
        if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= len(body):
            raise ValueError(f"invalid story frame reference: {n!r}")
        return body[n - 1]
    rows = {"cover": cover}
    rows.update({f"body{i:02d}": path for i, path in enumerate(body, start=1)})
    rows.update({
        "climax": frame_for(climax),
        "payoff": frame_for(payoff),
        "captions": captions,
        "publish_copy": publish_copy,
        "propagation_card": propagation,
    })
    return rows

def release_hashes(ep: Path) -> dict[str, dict]:
    return {
        role: {"path": repo_rel(path), "sha256": sha256_file(path)}
        for role, path in release_artifacts(ep).items()
    }


def release_review_rows(rows: dict[str, dict]) -> dict[str, dict]:
    """Keep the final critic on release semantics; all-body subtitle pixels are chunk-audited separately."""
    roles = ("cover", "body01", "body02", "body03", "climax", "payoff", "captions", "publish_copy", "propagation_card")
    return {role: rows[role] for role in roles if role in rows}


def cmd_init_compliance(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    p = ep / COMPLIANCE_REL
    if p.is_file() and not args.force:
        print("publish-compliance.json already exists")
        return 0
    data = {
        "schema_version": 1,
        "story_os_version": episode_contract_version(ep),
        "ai_generated": True,
        "platform_ai_label_required": True,
        "platform_ai_label_method": "douyin_platform_declaration",
        "fiction_context_notice_required": True,
        "fiction_context_notice": "AI生成剧情内容；故事为虚构创作，真实地点仅作为故事背景。",
        "user_must_confirm_label_at_publish_time": True,
        "prepared_at": now(),
    }
    write_json(p, data)
    print("PUBLISH COMPLIANCE: initialized")
    return 0

def verify_governance(ep: Path) -> list[str]:
    if not guard_required(ep):
        return []
    p = ep / COMPLIANCE_REL
    if not p.is_file():
        return ["meta/publish-compliance.json missing; run init-compliance"]
    try:
        data = read_json(p)
    except Exception as exc:
        return [str(exc)]
    errors = []
    if data.get("ai_generated") is not True:
        errors.append("publish compliance must declare ai_generated=true")
    if data.get("platform_ai_label_required") is not True:
        errors.append("platform_ai_label_required must be true")
    if data.get("platform_ai_label_method") != "douyin_platform_declaration":
        errors.append("platform_ai_label_method must be douyin_platform_declaration")
    if data.get("fiction_context_notice_required") is not True:
        errors.append("fiction_context_notice_required must be true for realistic fictional Story OS releases")
    if not str(data.get("fiction_context_notice") or "").strip():
        errors.append("fiction_context_notice missing")
    if data.get("user_must_confirm_label_at_publish_time") is not True:
        errors.append("publish-time AI label confirmation flag missing")
    return errors

def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value:
        raise RuntimeError("Codex CLI not found")
    return Path(value).expanduser().resolve()

def prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]

def release_critic_prompt(ep: Path, candidate: Path, rows: dict[str, dict]) -> str:
    manifest = load_manifest(ep)
    publication = manifest.get("publication") or {}
    title = str(publication.get("actual_title") or "")
    description = str(publication.get("description") or "")
    topics = publication.get("topics") or []
    review_rows = release_review_rows(rows)
    mapping = "\n".join(f"- {role}: {row['path']}" for role, row in review_rows.items())
    rel = ep.relative_to(ROOT).as_posix()
    out = candidate.relative_to(ROOT).as_posix()
    return f"""You are an adversarial FINAL RELEASE Semantic + Governance Critic in a fresh isolated session.
Do NOT edit any file except the requested candidate JSON.
Episode: {rel}

Inspect the ACTUAL final publish assets, not prompts:
{mapping}

Actual title:
{title}

Description:
{description}

Topics:
{json.dumps(topics, ensure_ascii=False)}

Read:
- standards/制作规范_正式版.md
- standards/release_preflight_guard_V2.0.3.5.md
- {rel}/meta/subtitle-layout-audit.json (deterministic all-frame placement/line-count/hash audit)
- {rel}/meta/caption-image-audit.json (all final publish frames reviewed in SHA-bound chunks of up to 5 for caption support + actual subtitle obstruction)
- the episode Story Lock / storyboard / captions / publish copy / propagation card.

Hard release checks:
1. cover_title_match: cover and actual title promise the same core story/anomaly.
2. cover_frame01_handoff: body01 immediately continues or concretely supports the cover promise; no bait-and-switch.
3. first3_coherence: body01-03 form one readable entry path, not three disconnected hooks.
4. climax_upgrade: the actual climax frame is meaningfully stronger/more irreversible than the first hook.
5. payoff_honesty: the payoff is earned by earlier evidence and does not add a brand-new mechanism.
6. description_consistency: description/topics do not claim official fact, real case, or evidence absent from the story.
7. no_caption_invented_core_evidence: final text may add context, but may not invent the core visual evidence.
8. subtitle_left_middle_and_unobstructed: require BOTH SHA-bound all-frame audits above to PASS. subtitle-layout-audit proves left/middle geometry, line count and current publish-output hashes; caption-image-audit proves every final publish frame was pixel-reviewed in chunks and subtitle_unobstructed=true. Do not reopen every body image here; fail if either audit is missing/stale/failed.
9. caption_conversational_hook_quality: captions must sound like a real first-person immediate record, stay concise/eye-catching, avoid novel narration/AI boilerplate, and perform one clear narrative function per frame. Two rendered lines is the hard maximum.

Governance checks:
- This is AI-generated realistic fictional story content.
- Real locations may be used as story backgrounds, but the release must not present invented events as official/verified real incidents.
- No unverifiable dangerous accusation against a real region, ethnicity, religion, organization, or identifiable person.
- Platform AI-generation declaration/label must be planned and not intentionally stripped.
- A fiction-context notice is appropriate for this Story OS format.

PASS only when every release and governance check is true.
Write ONLY valid JSON to {out}:
{{
  "release_checks": {{
    "cover_title_match": true,
    "cover_frame01_handoff": true,
    "first3_coherence": true,
    "climax_upgrade": true,
    "payoff_honesty": true,
    "description_consistency": true,
    "no_caption_invented_core_evidence": true,
    "subtitle_left_middle_and_unobstructed": true,
    "caption_conversational_hook_quality": true
  }},
  "governance_checks": {{
    "ai_generated_declared": true,
    "platform_ai_label_planned": true,
    "fiction_context_not_misrepresented_as_official_fact": true,
    "no_unverifiable_real_group_accusation": true,
    "real_location_handled_as_fictional_story_context": true
  }},
  "issue_codes": [],
  "notes": ["specific final-release evidence"],
  "summary": {{"passed": true}}
}}
"""

def validate_release_review(ep: Path, data: dict) -> list[str]:
    errors = []
    if data.get("schema_version") != 1:
        errors.append("release semantic schema_version must be 1")
    if data.get("story_os_version") != episode_contract_version(ep):
        errors.append("release semantic story_os_version mismatch")
    current = release_hashes(ep)
    if data.get("artifacts") != current:
        errors.append("release semantic artifact SHA set is stale or mismatched")
    prov = data.get("critic_provenance") or {}
    errors.extend(runtime_provenance.validate_critic_provenance(prov))
    checks = data.get("release_checks") or {}
    for key in RELEASE_CHECKS:
        if checks.get(key) is not True:
            errors.append(f"release_checks.{key} must be true")
    gov = data.get("governance_checks") or {}
    for key in GOV_CHECKS:
        if gov.get(key) is not True:
            errors.append(f"governance_checks.{key} must be true")
    if data.get("issue_codes") not in ([], None):
        errors.append(f"release semantic issue_codes not empty: {data.get('issue_codes')}")
    if (data.get("summary") or {}).get("passed") is not True:
        errors.append("release semantic summary.passed must be true")
    return errors

def _finalize_release_review(ep: Path, data: dict, provenance: dict) -> int:
    data["schema_version"] = 1
    data["story_os_version"] = episode_contract_version(ep)
    data["artifacts"] = release_hashes(ep)
    data["critic_provenance"] = provenance
    write_json(ep / RELEASE_REVIEW_REL, data)
    (ep / RELEASE_CANDIDATE_REL).unlink(missing_ok=True)
    errors = validate_release_review(ep, data)
    if errors:
        print("RELEASE SEMANTIC REVIEW FAIL")
        for e in errors:
            print("FAIL:", e)
        return 2
    print("RELEASE SEMANTIC REVIEW PASS")
    return 0


def finalize_product_release_review(ep: Path, runtime: str) -> int:
    candidate = ep / RELEASE_CANDIDATE_REL
    data, provenance = product_review_adapter.finalize_candidate(
        ep,
        kind="release-semantic",
        runtime=runtime,
        attempt=1,
        candidate_path=candidate,
    )
    rc = _finalize_release_review(ep, data, provenance)
    if rc == 0:
        product_review_adapter.mark_complete(ep, "release-semantic", attempt=1, final_path=ep / RELEASE_REVIEW_REL)
    return rc


def cmd_run_release_critic(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    rows = release_hashes(ep)
    candidate = ep / RELEASE_CANDIDATE_REL
    candidate.unlink(missing_ok=True)
    active_runtime, _ = runtime_router.detect()
    if active_runtime in {"WORK", "WEB"} and not args.codex:
        review_rows = release_review_rows(rows)
        source_paths = list(dict.fromkeys(ROOT / row["path"] for row in review_rows.values()))
        source_paths += [
            ep / subtitle_layout.REPORT_REL,
            ep / caption_image_audit.REL,
            ROOT / "standards/制作规范_正式版.md",
            ROOT / "standards/release_preflight_guard_V2.0.3.5.md",
        ]
        request = product_review_adapter.prepare(
            ep,
            kind="release-semantic",
            runtime=active_runtime,
            attempt=1,
            prompt=release_critic_prompt(ep, candidate, rows),
            source_paths=source_paths,
            candidate_path=candidate,
        )
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC
    codex = resolve_codex(args.codex)
    cmd = prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="high"',
        "-s", "workspace-write", "-C", str(ROOT), "--json", "-"
    ]
    log = ep / "meta/release-critic.jsonl"
    before = {role: row["sha256"] for role, row in rows.items()}
    with log.open("w", encoding="utf-8", newline="\n") as handle:
        completed = subprocess.run(
            cmd,
            input=release_critic_prompt(ep, candidate, rows),
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=args.timeout,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"release critic failed rc={completed.returncode}; log={log}")
    after = {role: row["sha256"] for role, row in release_hashes(ep).items()}
    if before != after:
        raise RuntimeError("release critic changed final release assets; review invalid")
    if not candidate.is_file():
        raise RuntimeError("release critic did not produce candidate JSON")
    data = read_json(candidate)
    provenance = runtime_provenance.build_critic_provenance(
        "CODEX", attempt=1, log=repo_rel(log)
    )
    return _finalize_release_review(ep, data, provenance)

def verify_release_semantic(ep: Path) -> list[str]:
    if not guard_required(ep):
        return []
    p = ep / RELEASE_REVIEW_REL
    if not p.is_file():
        return ["meta/release-semantic-review.json missing; run run-release-critic"]
    try:
        return validate_release_review(ep, read_json(p))
    except Exception as exc:
        return [str(exc)]

def cmd_enable(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    write_json(ep / ENABLE_REL, {
        "schema_version": 1,
        "enabled": True,
        "story_os_version": story_os_version(),
        "enabled_at": now(),
        "reason": args.reason,
    })
    print("RELEASE GUARD ENABLED")
    return 0

def cmd_verify(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    groups = [
        ("recent5", verify_recent5_evidence(ep)),
        ("series_lock", verify_series_lock(ep)),
        ("visual_final_freeze", visual_final_freeze.verify(ep)),
        ("caption_image_audit", caption_image_audit.verify(ep)),
        ("release_semantic", verify_release_semantic(ep)),
        ("governance", verify_governance(ep)),
    ]
    failed = False
    for name, errors in groups:
        if errors:
            failed = True
            for e in errors:
                print(f"FAIL {name}: {e}")
        else:
            print(f"PASS {name}")
    return 2 if failed else 0

def cmd_prepare_auto(args: argparse.Namespace) -> int:
    ep = ep_path(args.episode_dir)
    if not guard_required(ep):
        cmd_enable(argparse.Namespace(episode_dir=str(ep), reason=f"full-auto postflight on V{story_os_version()}"))
    try:
        data = build_recent5(ep, codex=args.codex, timeout=args.timeout)
        write_json(ep / RECENT5_REL, data)
        if data["decision"] != "pass":
            print(f"FAIL recent5: max={data['max_similarity_score']} decision={data['decision']}")
            return 3
    except ProductReviewHostAction as exc:
        print(json.dumps(exc.request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC
    except Exception as exc:
        print("FAIL recent5:", exc)
        return 3

    if series_lock_required(ep):
        errors = verify_series_lock(ep)
        if errors:
            for e in errors:
                print("FAIL series_lock:", e)
            return 3

    cmd_init_compliance(argparse.Namespace(episode_dir=str(ep), force=False))
    try:
        visual_final_freeze.ensure(ep)
    except Exception as exc:
        print("FAIL visual_final_freeze:", exc)
        return 3
    try:
        caption_ok,_caption_data=caption_image_audit.ensure(ep,codex_raw=args.codex,timeout=min(args.timeout,900))
        if not caption_ok:
            print("FAIL caption_image_audit: unsupported caption/image pair")
            return 3
    except caption_image_audit.ProductReviewHostAction as exc:
        print(json.dumps(exc.request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC
    except Exception as exc:
        print("FAIL caption_image_audit:", exc)
        return 3
    if verify_release_semantic(ep):
        rc = cmd_run_release_critic(argparse.Namespace(
            episode_dir=str(ep), codex=args.codex, timeout=args.timeout
        ))
        if rc != 0:
            return rc
    return cmd_verify(argparse.Namespace(episode_dir=str(ep)))

def self_test() -> int:
    import tempfile

    score, veto, _ = similarity(
        {"dimensions": {k: "x" for k in FINGERPRINT_KEYS}},
        {"dimensions": {k: "x" for k in FINGERPRINT_KEYS}},
    )
    assert score == 100 and veto
    assert version_tuple("2.0.3.6") >= MIN_CONTRACT

    # Regression: sibling episode count must never imply shared continuity.
    with tempfile.TemporaryDirectory() as raw:
        parent = Path(raw) / "category"
        ep1 = parent / "01"
        ep2 = parent / "02"
        for ep in (ep1, ep2):
            (ep / "meta").mkdir(parents=True, exist_ok=True)
            write_json(ep / "meta/episode-state.json", {"tool_version": "2.0.3.5.1"})
        assert series_lock_required(ep1) is False
        write_json(parent / "meta/series-continuity.json", {
            "schema_version": 1,
            "enabled": True,
            "series_id": "self-test-series",
        })
        assert series_lock_required(ep1) is True

    print("RELEASE PREFLIGHT SELF-TEST PASS")
    return 0

def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("bootstrap-registry")

    p = sub.add_parser("enable")
    p.add_argument("episode_dir")
    p.add_argument("--reason", default="manual enable")

    p = sub.add_parser("build-recent5")
    p.add_argument("episode_dir")
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=1800)

    p = sub.add_parser("declare-series")
    p.add_argument("series_dir")
    p.add_argument("--series-id")

    p = sub.add_parser("init-series-lock")
    p.add_argument("series_dir")
    p.add_argument("--source", required=True)

    p = sub.add_parser("bind-series")
    p.add_argument("episode_dir")

    p = sub.add_parser("init-compliance")
    p.add_argument("episode_dir")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("run-release-critic")
    p.add_argument("episode_dir")
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=1800)

    p = sub.add_parser("finalize-review")
    p.add_argument("episode_dir")
    p.add_argument("--runtime", choices=["WORK", "WEB"], default="WORK")

    p = sub.add_parser("prepare-auto")
    p.add_argument("episode_dir")
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=1800)

    p = sub.add_parser("verify")
    p.add_argument("episode_dir")

    sub.add_parser("self-test")

    args = ap.parse_args()
    if args.cmd == "bootstrap-registry":
        return cmd_bootstrap_registry(args)
    if args.cmd == "enable":
        return cmd_enable(args)
    if args.cmd == "build-recent5":
        return cmd_build_recent5(args)
    if args.cmd == "declare-series":
        return cmd_declare_series(args)
    if args.cmd == "init-series-lock":
        return cmd_init_series_lock(args)
    if args.cmd == "bind-series":
        return cmd_bind_series(args)
    if args.cmd == "init-compliance":
        return cmd_init_compliance(args)
    if args.cmd == "run-release-critic":
        return cmd_run_release_critic(args)
    if args.cmd == "finalize-review":
        return finalize_product_release_review(ep_path(args.episode_dir), args.runtime)
    if args.cmd == "prepare-auto":
        return cmd_prepare_auto(args)
    if args.cmd == "verify":
        return cmd_verify(args)
    return self_test()

if __name__ == "__main__":
    raise SystemExit(main())

# STORY_OS_V2_6_0_PERFORMANCE_RUNTIME
