#!/usr/bin/env python3
"""Resolve the sequence-level capture grammar without changing Episode state."""
from __future__ import annotations

import json
from pathlib import Path

import storyos_config

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]
_CONFIG = storyos_config.load_config()
DEFAULT_ID = str(storyos_config.get_path(_CONFIG, "visual.default_sequence_grammar_id"))
DEFAULT_PATH = Path(str(storyos_config.get_path(_CONFIG, "visual.sequence_grammar_path")))
EPISODE_REL = Path("meta/sequence-grammar.json")


def _read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return data


def _inside_repo(path: Path) -> Path:
    path = path.resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(f"sequence grammar escapes repository: {path}") from exc
    return path


def _resolved(*, selection: str, grammar_id: str, grammar_path: Path, authority_source: str, reason: str | None = None) -> dict:
    path = _inside_repo(ROOT / grammar_path)
    if not path.is_file():
        raise SystemExit(f"SEQUENCE_GRAMMAR_MISSING: {grammar_path.as_posix()}")
    data = _read(path)
    canonical_id = str(data.get("sequence_grammar_id") or "").strip()
    if canonical_id != grammar_id:
        raise SystemExit(f"SEQUENCE_GRAMMAR_ID_MISMATCH: requested={grammar_id} canonical={canonical_id}")
    result = {
        "selection": selection,
        "sequence_grammar_id": grammar_id,
        "sequence_grammar_path": grammar_path.as_posix(),
        "authority_source": authority_source,
        "data": data,
    }
    if reason:
        result["override_reason"] = reason
    return result


def default_grammar() -> dict:
    return _resolved(
        selection="global_default",
        grammar_id=DEFAULT_ID,
        grammar_path=DEFAULT_PATH,
        authority_source="global_default_sequence_grammar",
    )


def resolve_grammar(ep: Path) -> dict:
    config_path = Path(ep) / EPISODE_REL
    if not config_path.is_file():
        return default_grammar()
    cfg = _read(config_path)
    mode = str(cfg.get("mode") or "default").strip().lower()
    if mode == "default":
        return default_grammar()
    if mode != "override":
        raise SystemExit(f"invalid sequence grammar mode={mode!r}; expected default|override")
    grammar_id = str(cfg.get("sequence_grammar_id") or "").strip()
    grammar_path = Path(str(cfg.get("sequence_grammar_path") or "").strip())
    reason = str(cfg.get("override_reason") or "").strip()
    if not grammar_id or not str(grammar_path) or not reason:
        raise SystemExit("sequence grammar override requires sequence_grammar_id + sequence_grammar_path + override_reason")
    return _resolved(
        selection="episode_override",
        grammar_id=grammar_id,
        grammar_path=grammar_path,
        authority_source=EPISODE_REL.as_posix(),
        reason=reason,
    )


if __name__ == "__main__":
    resolved = default_grammar()
    assert resolved["sequence_grammar_id"] == DEFAULT_ID
    assert (resolved["data"].get("camera_roster") or {}).get("primary_photographer_required") is True
    print("SEQUENCE GRAMMAR SELF-TEST PASS")
