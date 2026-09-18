from __future__ import annotations

from pathlib import Path

import review_record_persistence


REVIEW_TYPE = "VISUAL_PROFILE"
LEGACY_REL = Path("meta/visual-profile-review.json")
EXPORT_NAME = "visual-profile.json"


def load(ep: Path) -> dict | None:
    ep = Path(ep).resolve()
    return review_record_persistence.load_latest(
        ep,
        REVIEW_TYPE,
        legacy_path=ep / LEGACY_REL,
    )


def _decision(payload: dict, explicit: str | None = None) -> str:
    if explicit:
        return str(explicit)
    if (payload.get("summary") or {}).get("passed") is True and not (
        payload.get("issue_codes") or []
    ):
        return "PASS"
    return "FAIL"


def save(
    ep: Path,
    payload: dict,
    *,
    decision: str | None = None,
    source_sha256: str | None = None,
) -> dict:
    ep = Path(ep).resolve()
    provenance = payload.get("critic_provenance") or {}
    return review_record_persistence.save(
        ep,
        REVIEW_TYPE,
        LEGACY_REL,
        payload,
        decision=_decision(payload, decision),
        reviewer_type=str(provenance.get("runtime") or "") or None,
        source_sha256=source_sha256,
    )


def authority_sha256(ep: Path) -> str | None:
    ep = Path(ep).resolve()
    return review_record_persistence.authority_sha256(
        ep,
        REVIEW_TYPE,
        legacy_path=ep / LEGACY_REL,
    )


def materialize_export(ep: Path, payload: dict | None = None) -> Path | None:
    return review_record_persistence.materialize_export(
        Path(ep).resolve(),
        REVIEW_TYPE,
        payload=payload,
        filename=EXPORT_NAME,
    )
