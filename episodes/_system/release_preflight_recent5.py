#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release_preflight recent5 history build/verify domain (B4 split)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import product_review_adapter
from fingerprint_semantics import (
    REVIEW_REL as RECENT5_SEMANTIC_REL,
    comparison_index as semantic_comparison_index,
    ensure_review as ensure_semantic_review,
    required as semantic_recent5_required,
    validate_review as validate_semantic_review,
    ProductReviewHostAction,
)
from release_preflight_core import *
import runtime_timeout_policy

def recent5_history(current: dict, reg: dict) -> list[dict]:
    return [
        x for x in reg.get("episodes", [])
        if isinstance(x, dict) and x.get("episode_id") != current.get("episode_id")
    ][-5:]

def build_recent5(ep: Path, codex: str | None = None, timeout: int | None = None) -> dict:
    if timeout is None:
        timeout = runtime_timeout_policy.seconds("release_semantic")
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
