#!/usr/bin/env python3
from __future__ import annotations

"""Production ownership guard consumed by the canonical Production Kernel.

``meta/runtime/runtime-primary.json`` is a control-plane decision record.  W-11
existed because production never read it.  This module is deliberately tiny so
``episodes/_system`` does not import the control plane: the kernel reads the
record itself and refuses V3 production work unless V3_RUNTIME is the recorded
owner.

This is not a second router and never mutates ownership.  The Phase9 switch
remains the only writer of the ownership record.
"""

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNERSHIP_REL = Path("meta/runtime/runtime-primary.json")
EXPECTED_PRODUCTION_OWNER = "V3_RUNTIME"
VALID_OWNERS = frozenset({"V2_RUNTIME", "V3_RUNTIME"})


class RuntimeOwnershipError(RuntimeError):
    code = "PRODUCTION_OWNERSHIP_MISMATCH"

    def __init__(self, detail: str) -> None:
        super().__init__(f"{self.code}: {detail}")
        self.detail = detail


@dataclass(frozen=True)
class OwnershipRecord:
    primary_runtime: str
    previous_runtime: str | None
    reason: str
    updated_at: str
    source: str

    @property
    def v3_effective(self) -> bool:
        return self.primary_runtime == EXPECTED_PRODUCTION_OWNER

    def as_dict(self) -> dict:
        return {
            "primary_runtime": self.primary_runtime,
            "previous_runtime": self.previous_runtime,
            "reason": self.reason,
            "updated_at": self.updated_at,
            "source": self.source,
            "v3_effective": self.v3_effective,
        }


def load(path: Path | None = None) -> OwnershipRecord:
    target = Path(path) if path is not None else ROOT / OWNERSHIP_REL
    if not target.is_file():
        # Same honest default as the control plane: no switch evidence means V2.
        return OwnershipRecord("V2_RUNTIME", None, "ownership_record_missing", "", str(target))
    try:
        data = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeOwnershipError(f"ownership record unreadable: {target}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeOwnershipError(f"ownership record root must be object: {target}")
    owner = str(data.get("primary_runtime") or "").strip()
    if owner not in VALID_OWNERS:
        raise RuntimeOwnershipError(f"invalid primary_runtime={owner!r}: {target}")
    return OwnershipRecord(
        primary_runtime=owner,
        previous_runtime=(str(data.get("previous_runtime")) if data.get("previous_runtime") else None),
        reason=str(data.get("reason") or ""),
        updated_at=str(data.get("updated_at") or ""),
        source=str(target),
    )


def assert_v3_owner(operation: str, *, path: Path | None = None) -> OwnershipRecord:
    record = load(path)
    if not record.v3_effective:
        raise RuntimeOwnershipError(
            f"{operation} belongs to {EXPECTED_PRODUCTION_OWNER}, but primary_runtime={record.primary_runtime}; "
            "production execution refused until the control-plane ownership record selects V3_RUNTIME"
        )
    return record


def status(path: Path | None = None) -> dict:
    try:
        record = load(path)
        return {"ok": True, **record.as_dict()}
    except RuntimeOwnershipError as exc:
        return {"ok": False, "code": exc.code, "detail": exc.detail}
