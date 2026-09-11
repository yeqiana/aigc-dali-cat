#!/usr/bin/env python3
"""Story OS Visual Profile Selector (Visual Profile Governance Phase 3.3).

A pure, deterministic rule engine that turns

    Story Intent + Episode Context + Audience Expectation

into a registered Visual Profile id plus auditable Selection Evidence.

Boundaries
----------
- Reads only the Visual Profile registry (standards/visual_profiles/index.json)
  and the selector schemas. It never reads or writes episode state,
  story-gates.json, frame contracts, the production ledger, or Runtime files.
- Never invents a profile id and never falls back to an unregistered id.
- Returns a plain dict. Persisting the choice (Visual Lock) is Phase 3.4 and is
  deliberately out of scope here.

Decision model
--------------
1. user_override.forced_profile_id        explicit user force
2. episode_context.previous_profile       series lock
3. semantic match (world / era / location / experience_type / fantasy_level)
4. default profile (registry default_profile)

The Phase 3.1 priority list (world > era > location > audience) is realised as
rule specificity inside the semantic layer: each rule declares the contract
signals it matches, and a rule that matches more signals outranks a rule that
matches fewer. Equal specificity across two profiles is genuine ambiguity, so
the selector returns needs_confirmation instead of guessing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import story_json
import visual_profile_registry as registry

ROOT = Path(__file__).resolve().parents[2]

SCHEMA_DIR_REL = Path("standards/visual_profiles/schema")
SELECTOR_SCHEMA_FILES = {
    "input": "selector-input.schema.json",
    "output": "selector-output.schema.json",
    "evidence": "selector-evidence.schema.json",
}

SELECTOR_VERSION = "1.0"
SOURCE = "rule_engine"

STATUS_SELECTED = "selected"
STATUS_NEEDS_CONFIRMATION = "needs_confirmation"
STATUS_DEFAULTED = "defaulted"
STATUS_REJECTED = "rejected"
STATUSES = (
    STATUS_SELECTED,
    STATUS_NEEDS_CONFIRMATION,
    STATUS_DEFAULTED,
    STATUS_REJECTED,
)

ERROR_SELECTION_INVALID = "VISUAL_PROFILE_SELECTION_INVALID"
ERROR_SELECTION_REJECTED = "VISUAL_PROFILE_SELECTION_REJECTED"

M00 = "M00_REAL_WORLD_DOCUMENTARY_V1"
M01 = "M01_ANCIENT_MUNDANE_LIFE_V1"
M02 = "M02_HEAVEN_MUNDANE_WORKER_V1"
M03 = "M03_JIANGNAN_IMMERSIVE_LIFE_V1"

JIANGNAN_TOKENS = ("jiangnan", "江南", "水乡")


class VisualProfileSelectionError(registry.VisualProfileError):
    """Fail-fast selector error (shares the registry SystemExit convention)."""

    code = ERROR_SELECTION_INVALID


def _story_root(story_root) -> Path:
    return Path(story_root) if story_root else ROOT


def _text(value) -> str:
    return str(value).strip() if value is not None else ""


def _si(data) -> dict:
    return data.get("story_intent") or {}


def _ctx(data) -> dict:
    return data.get("episode_context") or {}


def _aud(data) -> dict:
    return data.get("audience_expectation") or {}


def _ovr(data) -> dict:
    return data.get("user_override") or {}


# --------------------------------------------------------------------------- #
# selector schemas (Phase 3.2 contracts)
# --------------------------------------------------------------------------- #

def selector_schema_path(kind: str, story_root=None) -> Path:
    if kind not in SELECTOR_SCHEMA_FILES:
        raise VisualProfileSelectionError(f"unknown selector schema kind: {kind!r}")
    return _story_root(story_root) / SCHEMA_DIR_REL / SELECTOR_SCHEMA_FILES[kind]


def load_selector_schema(kind: str, story_root=None) -> dict:
    path = selector_schema_path(kind, story_root)
    if not path.is_file():
        raise VisualProfileSelectionError(f"selector schema missing: {path.as_posix()}")
    data = story_json.read_json(path)
    if not isinstance(data, dict):
        raise VisualProfileSelectionError(
            f"selector schema root must be an object: {path.as_posix()}"
        )
    return data


def validate_selector_input(data, story_root=None) -> list:
    return registry.validate_json(data, load_selector_schema("input", story_root))


def validate_selector_evidence(data, story_root=None) -> list:
    return registry.validate_json(data, load_selector_schema("evidence", story_root))


def validate_selector_output(data, story_root=None) -> list:
    errors = registry.validate_json(data, load_selector_schema("output", story_root))
    evidence = (data or {}).get("evidence") if isinstance(data, dict) else None
    if isinstance(evidence, dict):
        errors.extend(validate_selector_evidence(evidence, story_root))
    return errors


# --------------------------------------------------------------------------- #
# rule engine (Phase 3.3)
# --------------------------------------------------------------------------- #

def _match_m00(data):
    """Real-world documentary: any real-world story is eligible (base layer)."""
    if _text(_si(data).get("world")) != "real":
        return [], []
    notes = []
    theme = _text(_si(data).get("theme"))
    if theme:
        notes.append(f"theme={theme}")
    return ["world=real"], notes


def _match_m01(data):
    """Ancient ordinary life: historical real world in an ancient era."""
    si = _si(data)
    if _text(si.get("world")) != "historical_real" or _text(si.get("era")) != "ancient":
        return [], []
    notes = []
    theme = _text(si.get("theme"))
    if theme:
        notes.append(f"theme={theme}")
    return ["world=historical_real", "era=ancient"], notes


def _match_m02(data):
    """Heaven mundane worker: fictional world with a high fantasy level."""
    si = _si(data)
    if _text(si.get("world")) != "fictional" or _text(_aud(data).get("fantasy_level")) != "high":
        return [], []
    notes = []
    theme = _text(si.get("theme"))
    if theme:
        notes.append(f"theme={theme}")
    return ["world=fictional", "fantasy_level=high"], notes


def _match_m03(data):
    """Jiangnan immersive life: water-town location AND first-person immersion."""
    si = _si(data)
    location = _text(si.get("location")).lower()
    experience = _text(si.get("experience_type"))
    signals = []
    if any(token in location for token in JIANGNAN_TOKENS):
        signals.append("location=jiangnan")
    if experience == "immersive_first_person":
        signals.append("experience_type=immersive_first_person")
    if len(signals) < 2:
        return [], []
    return signals, []


def _rules() -> list:
    return [
        {"profile_id": M00, "signals": ("world=real",), "matcher": _match_m00},
        {"profile_id": M01, "signals": ("world=historical_real", "era=ancient"), "matcher": _match_m01},
        {"profile_id": M02, "signals": ("world=fictional", "fantasy_level=high"), "matcher": _match_m02},
        {"profile_id": M03, "signals": ("location=jiangnan", "experience_type=immersive_first_person"), "matcher": _match_m03},
    ]


def rule_coverage(story_root=None) -> dict:
    """Which rule targets are registered (governance drift check, read-only)."""
    root = _story_root(story_root)
    registered, unregistered = [], []
    for rule in _rules():
        pid = rule["profile_id"]
        if registry.registry_entry(pid, root) is None:
            unregistered.append(pid)
        else:
            registered.append(pid)
    return {"registered": registered, "unregistered": unregistered}


# --------------------------------------------------------------------------- #
# evidence + output builders
# --------------------------------------------------------------------------- #

def inputs_summary(data: dict) -> dict:
    si, ctx, aud, ovr = _si(data), _ctx(data), _aud(data), _ovr(data)
    return {
        "world": _text(si.get("world")),
        "era": _text(si.get("era")),
        "theme": _text(si.get("theme")),
        "genre": _text(si.get("genre")),
        "location": _text(si.get("location")),
        "experience_type": _text(si.get("experience_type")),
        "series": _text(ctx.get("series")),
        "previous_profile": _text(ctx.get("previous_profile")),
        "realism": _text(aud.get("realism")),
        "immersion": _text(aud.get("immersion")),
        "fantasy_level": _text(aud.get("fantasy_level")),
        "forced_profile_id": _text(ovr.get("forced_profile_id")),
    }


def inputs_digest(summary: dict) -> str:
    blob = json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _evidence(data, *, matched_rules, rejected, reason, candidate_count=0, notes=None) -> dict:
    summary = inputs_summary(data)
    return {
        "selector_version": SELECTOR_VERSION,
        "source": SOURCE,
        "registry": registry.REGISTRY_REL.as_posix(),
        "inputs_digest": inputs_digest(summary),
        "inputs_summary": summary,
        "matched_rules": list(matched_rules),
        "rejected": list(rejected),
        "reason": list(reason),
        "candidate_count": int(candidate_count),
        "notes": list(notes or []),
    }


def _output(status: str, selected_profile, candidates, evidence) -> dict:
    return {
        "schema_version": 1,
        "status": status,
        "selected_profile": selected_profile,
        "candidates": candidates,
        "evidence": evidence,
    }


def _finalize(output: dict, story_root) -> dict:
    errors = validate_selector_output(output, story_root)
    if errors:
        raise VisualProfileSelectionError(
            "selector produced an invalid output: " + "; ".join(errors)
        )
    return output


# --------------------------------------------------------------------------- #
# public entry point
# --------------------------------------------------------------------------- #

def select(selector_input, *, story_root=None, strict: bool = True) -> dict:
    """Select a Visual Profile from a Selector Input and return a Selector Output.

    Pure function: no filesystem writes, no episode or Runtime state.
    strict=True (default) raises VisualProfileSelectionError for invalid input or
    an unregistered forced_profile_id; strict=False returns status='rejected'.
    """
    root = _story_root(story_root)
    data = selector_input if isinstance(selector_input, dict) else {}

    input_errors = validate_selector_input(data, root)
    if input_errors:
        if strict:
            raise VisualProfileSelectionError("invalid selector input: " + "; ".join(input_errors))
        return _finalize(
            _output(
                STATUS_REJECTED,
                None,
                [],
                _evidence(data, matched_rules=[], rejected=[],
                          reason=["invalid_input"] + input_errors),
            ),
            root,
        )

    forced = _text(_ovr(data).get("forced_profile_id"))
    if forced:
        try:
            registry.resolve_registered_profile(forced, story_root=root)
        except registry.VisualProfileError as exc:
            detail = (
                f"forced_profile_id={forced!r} is not a registered active Visual Profile"
                f" ({exc.code})"
            )
            if strict:
                raise VisualProfileSelectionError(detail, ERROR_SELECTION_REJECTED) from exc
            return _finalize(
                _output(
                    STATUS_REJECTED,
                    None,
                    [],
                    _evidence(data,
                              matched_rules=[f"forced_profile_id={forced}"],
                              rejected=[{"profile": forced, "reason": "not registered"}],
                              reason=["prio=user_override", "forced_profile_not_registered"]),
                ),
                root,
            )
        return _finalize(
            _output(
                STATUS_SELECTED,
                forced,
                [],
                _evidence(data,
                          matched_rules=[f"user_override={forced}"],
                          rejected=[],
                          reason=["prio=user_override"]),
            ),
            root,
        )

    notes: list = []
    previous = _text(_ctx(data).get("previous_profile"))
    if previous:
        try:
            registry.resolve_registered_profile(previous, story_root=root)
        except registry.VisualProfileError:
            notes.append(f"previous_profile={previous} ignored: not a registered active profile")
        else:
            return _finalize(
                _output(
                    STATUS_SELECTED,
                    previous,
                    [],
                    _evidence(data,
                              matched_rules=[f"series_lock={previous}"],
                              rejected=[],
                              reason=["prio=series_lock"],
                              notes=notes),
                ),
                root,
            )

    candidates = []
    rejected = []
    for rule in _rules():
        pid = rule["profile_id"]
        if registry.registry_entry(pid, root) is None:
            notes.append(f"rule {pid} skipped: not registered")
            continue
        signals, rule_notes = rule["matcher"](data)
        if signals:
            candidates.append({"profile": pid, "matched_rules": signals, "notes": rule_notes})
        else:
            rejected.append({"profile": pid, "reason": "not matched: " + ", ".join(rule["signals"])})

    if not candidates:
        default_id = registry.default_profile_id(root)
        return _finalize(
            _output(
                STATUS_DEFAULTED,
                default_id,
                [],
                _evidence(data, matched_rules=[], rejected=rejected,
                          reason=["no_rule_matched", f"default={default_id}"],
                          notes=notes),
            ),
            root,
        )

    top = max(len(candidate["matched_rules"]) for candidate in candidates)
    ranked = [candidate for candidate in candidates if len(candidate["matched_rules"]) == top]

    if len(ranked) == 1:
        chosen = ranked[0]
        return _finalize(
            _output(
                STATUS_SELECTED,
                chosen["profile"],
                [],
                _evidence(data,
                          matched_rules=chosen["matched_rules"],
                          rejected=rejected,
                          reason=["prio=semantic"],
                          candidate_count=len(candidates),
                          notes=notes + chosen["notes"]),
            ),
            root,
        )

    return _finalize(
        _output(
            STATUS_NEEDS_CONFIRMATION,
            None,
            [{"profile": candidate["profile"], "matched_rules": candidate["matched_rules"]}
             for candidate in ranked],
            _evidence(data,
                      matched_rules=sorted({rule for candidate in ranked
                                            for rule in candidate["matched_rules"]}),
                      rejected=rejected,
                      reason=["prio=semantic", "ambiguous_conflict"],
                      candidate_count=len(candidates),
                      notes=notes),
        ),
        root,
    )
