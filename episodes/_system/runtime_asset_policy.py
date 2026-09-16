#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lifecycle classification for Story OS Episode/runtime files.

Policy only: this module never moves, deletes, ignores or rewrites assets.
It makes Git/storage lifecycle decisions explicit while the Production Kernel
continues to read the current paths.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Iterable

AUTHORITY = "AUTHORITY"
FORMAL_EVIDENCE = "FORMAL_EVIDENCE"
OPERATIONAL_STATE = "OPERATIONAL_STATE"
DERIVED_CACHE = "DERIVED_CACHE"
LOCAL_STAGING = "LOCAL_STAGING"
CONTENT_ASSET = "CONTENT_ASSET"
UNKNOWN = "UNKNOWN"

TRACK = "TRACK"
PRESERVE_UNTIL_ARCHIVED = "PRESERVE_UNTIL_ARCHIVED"
MIGRATION_CANDIDATE = "MIGRATION_CANDIDATE"
LOCAL_ONLY = "LOCAL_ONLY"


@dataclass(frozen=True)
class RuntimeAssetPolicy:
    category: str
    git_disposition: str
    rationale: str
    may_delete_automatically: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _norm(path: str | PurePosixPath) -> str:
    text = str(path).replace("\\", "/").strip()
    while text.startswith("./"):
        text = text[2:]
    return text.strip("/")


def classify(path: str | PurePosixPath) -> RuntimeAssetPolicy:
    """Classify one repository-relative or Episode-relative path conservatively."""
    p = _norm(path)
    if p.startswith("runtime/requests/"):
        return RuntimeAssetPolicy(
            LOCAL_STAGING,
            LOCAL_ONLY,
            "pre-bind Runtime Request staging copy; the bound Episode request is provenance authority",
            True,
        )

    marker = "/meta/"
    rel = p[p.index(marker) + 1:] if marker in p else p

    if rel in {"meta/episode-state.json", "meta/runtime-request.json", "meta/story-gates.json"}:
        return RuntimeAssetPolicy(AUTHORITY, TRACK, "canonical Episode/intent/gate authority")

    if rel.startswith("meta/provider-receipts/"):
        return RuntimeAssetPolicy(
            FORMAL_EVIDENCE,
            TRACK,
            "provider execution receipt with actual reference/canvas evidence",
        )

    if rel in {
        "meta/production-ledger.json",
        "meta/frame-semantic-audit.json",
        "meta/story-dna-trace.json",
        "meta/runtime/runtime-evidence-contract.json",
    } or rel.startswith("meta/frame-reviews/"):
        return RuntimeAssetPolicy(
            FORMAL_EVIDENCE,
            TRACK,
            "production/review evidence used to prove what actually happened",
        )

    if rel.startswith("meta/runtime/contracts/") or rel.startswith("meta/runtime/prompt-packages/"):
        return RuntimeAssetPolicy(
            DERIVED_CACHE,
            MIGRATION_CANDIDATE,
            "SHA-bound derived compilation output; regenerable, but current readers still use this path",
        )

    if rel.startswith("meta/runtime/") and rel.endswith("effective-config.json"):
        return RuntimeAssetPolicy(
            DERIVED_CACHE,
            MIGRATION_CANDIDATE,
            "effective runtime configuration projection regenerated from config and request",
        )

    if rel in {
        "meta/production-queue.json",
        "meta/runtime-checkpoint.json",
        "meta/runtime-dag-state.json",
        "meta/runtime-runner-state.json",
        "meta/runtime-resume-token.json",
        "meta/runtime/next-action.json",
        "meta/runtime/circuit-breaker.json",
        "meta/runtime/production-commit-journal.json",
        "meta/runtime/production-reconciliation.json",
        "meta/runtime/raw-candidate-budget.json",
        "meta/runtime/raw-candidate-budget-override.json",
    }:
        return RuntimeAssetPolicy(
            OPERATIONAL_STATE,
            PRESERVE_UNTIL_ARCHIVED,
            "mutable resume/recovery state; separate storage is desirable but current readers depend on it",
        )

    if rel.startswith("media/") or rel.startswith("assets/") or rel.startswith("prompts/"):
        return RuntimeAssetPolicy(
            CONTENT_ASSET,
            TRACK,
            "Episode content/source asset with an independent lifecycle from transient runtime state",
        )

    return RuntimeAssetPolicy(
        UNKNOWN,
        TRACK,
        "unclassified paths remain trackable until an explicit lifecycle rule proves otherwise",
    )


def inventory(paths: Iterable[str | PurePosixPath]) -> list[dict]:
    rows = []
    for path in paths:
        policy = classify(path)
        rows.append({"path": _norm(path), **policy.to_dict()})
    return rows
