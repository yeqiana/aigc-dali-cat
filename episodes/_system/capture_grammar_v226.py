#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

SYSTEM = Path(__file__).resolve().parent
ROOT = SYSTEM.parents[1]
DEFAULT_ID = "FIRST_PERSON_CASUAL_SNAPSHOT_V1"
DEFAULT_PATH = Path("standards/capture_grammars/FIRST_PERSON_CASUAL_SNAPSHOT_V1.json")
EPISODE_REL = Path("meta/capture-grammar.json")


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return data


def _inside_repo(path: Path) -> Path:
    p = path.resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit(f"capture grammar escapes repository: {path}")
    return p


def default_grammar() -> dict:
    p = ROOT / DEFAULT_PATH
    if not p.is_file():
        raise SystemExit(f"DEFAULT_CAPTURE_GRAMMAR_MISSING: {DEFAULT_PATH.as_posix()}")
    data = load_json(p)
    return {
        "selection": "global_default",
        "grammar_id": data.get("grammar_id") or DEFAULT_ID,
        "grammar_path": DEFAULT_PATH.as_posix(),
        "authority_source": "global_default_capture_grammar",
        "data": data,
    }


def resolve_grammar(ep: Path) -> dict:
    cfg_path = ep / EPISODE_REL
    if not cfg_path.is_file():
        return default_grammar()

    cfg = load_json(cfg_path)
    mode = str(cfg.get("mode") or "default").strip().lower()
    if mode == "default":
        return default_grammar()
    if mode != "override":
        raise SystemExit(f"invalid capture grammar mode={mode!r}; expected default|override")

    grammar_id = str(cfg.get("grammar_id") or "").strip()
    grammar_path = str(cfg.get("grammar_path") or "").strip()
    reason = str(cfg.get("override_reason") or "").strip()
    if not grammar_id or not grammar_path or not reason:
        raise SystemExit("capture grammar override requires grammar_id + grammar_path + override_reason")

    rel = Path(grammar_path)
    p = _inside_repo(ROOT / rel)
    if not p.is_file():
        raise SystemExit(f"capture grammar override missing: {rel.as_posix()}")
    data = load_json(p)
    canonical_id = str(data.get("grammar_id") or "").strip()
    if canonical_id and canonical_id != grammar_id:
        raise SystemExit(
            f"CAPTURE_GRAMMAR_ID_MISMATCH: episode={grammar_id} canonical={canonical_id}"
        )
    return {
        "selection": "episode_override",
        "grammar_id": grammar_id,
        "grammar_path": rel.as_posix(),
        "authority_source": EPISODE_REL.as_posix(),
        "override_reason": reason,
        "data": data,
    }


def compile_capture_contract(ep: Path) -> dict:
    resolved = resolve_grammar(ep)
    data = resolved["data"]
    authorship = data.get("camera_authorship") or {}
    snap = data.get("snapshot_language") or {}
    interop = data.get("visual_profile_interop") or {}
    forbidden = data.get("forbidden") or []

    lines = [
        f"capture_grammar={resolved['grammar_id']}",
        "CAPTURE GRAMMAR HAS HIGHER PRIORITY THAN VISUAL PROFILE composition/photography when they conflict.",
        f"principle={data.get('principle') or ''}",
        f"camera_operator={authorship.get('operator', 'participant_or_companion_inside_event')}",
        f"viewpoint={authorship.get('viewpoint', 'first_person_or_companion_eye')}",
        f"camera_position={authorship.get('distance', 'physically_plausible_human_position')}",
        "floating_omniscient_camera=false",
        f"handheld={str(bool(snap.get('handheld', True))).lower()}",
        f"unposed={str(bool(snap.get('unposed', True))).lower()}",
        f"imperfect_framing={str(bool(snap.get('imperfect_framing', True))).lower()}",
        "subjects do not need to face camera; avoid arranging people for the image",
        "allow partial occlusion and foreground body/hand/doorframe/vehicle edge when physically natural",
        f"subject_visibility_rule={data.get('subject_visibility_rule') or ''}",
        f"selfie_rule={data.get('selfie_rule') or ''}",
        "visual profile supplies texture/era/color/light; capture grammar supplies camera authorship and framing behavior",
        "do not convert film/cinematic texture into staged movie-still blocking",
    ]
    if forbidden:
        lines.append("capture_forbidden=" + "; ".join(map(str, forbidden)))

    return {
        **{k: v for k, v in resolved.items() if k != "data"},
        "text": "\n".join(lines),
        "interop": interop,
    }


if __name__ == "__main__":
    d = default_grammar()
    assert d["grammar_id"] == DEFAULT_ID
    print("CAPTURE GRAMMAR V2.2.6 SELF-TEST PASS")
