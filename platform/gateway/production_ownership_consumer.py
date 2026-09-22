"""Recorded production ownership vs. effective production ownership.

Two different facts hide behind the phrase "V3 owns production", and only one of
them is visible in the ownership record itself:

    recorded ownership  -- meta/runtime/runtime-primary.json says V3_RUNTIME.
    effective ownership -- production code reads that record and behaves
                           differently because of it.

The record was switched on 2026-09-11 and the switch is real. Step two never
happened. The production kernel (``episodes/_system``) imports no ``platform.*``
module and reads no ownership field, so production kept running on exactly the
engine it ran on before the switch. A gate that reads only the record cannot
separate those two states -- which is how "Production Ownership Migration
Complete" came to be reported over an unconsumed field, and why W-11 was reopened
on 2026-09-15.

The consumer set here is DERIVED by scanning the production roots, never read
from a hand-maintained allowlist. An allowlist would itself be a declaration, and
declarations are what this check exists to stop trusting.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# Frozen 2026-09-15 (架构收敛 3.1 / 3.2): the Production Kernel is
# episodes/_system. platform/ is the Control Plane -- so its modules reading this
# very record prove routing truth, but can never prove production takeover.
PRODUCTION_ROOTS = ("episodes",)
CONTROL_PLANE_ROOT = "platform"

# A file is a candidate consumer when it names the ownership record or its
# values. Substring matching rather than symbol resolution on purpose: the
# question is only "could production code act on ownership at all", and a false
# positive makes the gate MORE permissive -- so the token set stays narrow.
OWNERSHIP_TOKENS = (
    "runtime-primary",
    "runtime_primary",
    "primary_runtime",
    "runtime_ownership",
    "V3_RUNTIME",
    "V2_RUNTIME",
)

# Test code is not a runtime path: a test that names the record asserts about it
# rather than being driven by it.
_SKIP_DIRS = frozenset({"__pycache__", ".pytest_cache", "_tests", "_archive", ".storyos_cache", ".storyos-tmp"})
_SKIP_PREFIXES = ("test_", "conftest")


@dataclass(frozen=True)
class OwnershipEvidence:
    """What is recorded, and what actually consumes it."""

    recorded_runtime: str
    production_consumers: tuple[str, ...]
    control_plane_consumers: tuple[str, ...]

    @property
    def recorded_ownership(self) -> bool:
        return self.recorded_runtime == "V3_RUNTIME"

    @property
    def effective_ownership(self) -> bool:
        """True only when production code actually consumes the record."""
        return bool(self.production_consumers)

    @property
    def takeover_state(self) -> str:
        if self.effective_ownership:
            return "EFFECTIVE"
        if self.recorded_ownership:
            return "RECORDED_ONLY"
        return "NOT_SWITCHED"

    def as_dict(self) -> dict:
        return {
            "recorded_runtime": self.recorded_runtime,
            "recorded_ownership": self.recorded_ownership,
            "effective_ownership": self.effective_ownership,
            "takeover_state": self.takeover_state,
            "production_consumers": list(self.production_consumers),
            "control_plane_consumers": list(self.control_plane_consumers),
        }


def _iter_modules(base: Path) -> list[Path]:
    if not base.exists():
        return []
    found = []
    for path in sorted(base.rglob("*.py")):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.name.startswith(_SKIP_PREFIXES):
            continue
        found.append(path)
    return found


def _names_ownership(text: str) -> bool:
    return any(token in text for token in OWNERSHIP_TOKENS)


def _scan(base: Path, root: Path) -> tuple[str, ...]:
    hits = []
    for path in _iter_modules(base):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _names_ownership(text):
            try:
                hits.append(path.resolve().relative_to(root.resolve()).as_posix())
            except ValueError:
                continue
    return tuple(hits)


def assess(root: Path, recorded_runtime: str) -> OwnershipEvidence:
    """Scan the production roots for real consumers of the ownership record."""
    production: list[str] = []
    for rel in PRODUCTION_ROOTS:
        production.extend(_scan(root / rel, root))
    return OwnershipEvidence(
        recorded_runtime=recorded_runtime,
        production_consumers=tuple(sorted(production)),
        control_plane_consumers=_scan(root / CONTROL_PLANE_ROOT, root),
    )
