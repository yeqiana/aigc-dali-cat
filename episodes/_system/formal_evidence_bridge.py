#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a stable bridge from Episode formal evidence to Platform Artifact indexing.

This module never moves or deletes evidence. It keeps the real file under the
Episode authority boundary and emits registration-ready metadata that a Platform
ArtifactObserver can consume later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import runtime_asset_policy
import runtime_portability
import episode_identity

INDEX_REL = Path("meta/formal-evidence-index.json")
SCHEMA_VERSION = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _episode_id(ep: Path) -> str:
    return episode_identity.storage_episode_id(ep)


def evidence_rows(ep: Path) -> list[dict]:
    ep = Path(ep).resolve()
    rows: list[dict] = []
    for path in sorted((p for p in ep.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
        rel = path.relative_to(ep).as_posix()
        if rel == INDEX_REL.as_posix():
            continue
        policy = runtime_asset_policy.classify(rel)
        if policy.category != runtime_asset_policy.FORMAL_EVIDENCE:
            continue
        rows.append({
            "path": rel,
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
            "category": runtime_asset_policy.FORMAL_EVIDENCE,
            "git_disposition": policy.git_disposition,
        })
    return rows


def build_index(ep: Path) -> dict:
    ep = Path(ep).resolve()
    owner_id = _episode_id(ep)
    evidence = evidence_rows(ep)
    return {
        "schema_version": SCHEMA_VERSION,
        "owner_type": "EPISODE",
        "owner_id": owner_id,
        "artifact_type": "EVIDENCE",
        "evidence": evidence,
        "artifact_registration_rows": [
            {
                "artifact_type": "EVIDENCE",
                "path": row["path"],
                "sha256": row["sha256"],
                "owner_type": "EPISODE",
                "owner_id": owner_id,
                "metadata": {
                    "bytes": row["bytes"],
                    "lifecycle_category": runtime_asset_policy.FORMAL_EVIDENCE,
                    "source": "storyos_formal_evidence_bridge",
                },
            }
            for row in evidence
        ],
        "policy": "index only; real evidence stays under the Episode unless an explicit archival workflow copies it",
    }


def write_index(ep: Path) -> dict:
    ep = Path(ep).resolve()
    runtime_portability.assert_episode_directory(ep)
    data = build_index(ep)
    path = ep / INDEX_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_dir")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    ep = Path(args.episode_dir).resolve()
    data = write_index(ep) if args.write else build_index(ep)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
