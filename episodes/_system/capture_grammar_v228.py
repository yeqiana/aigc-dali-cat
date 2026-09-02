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


def _b(name, value, default=True):
    if value is None:
        value = default
    return f"{name}={str(bool(value)).lower()}"


def compile_capture_contract(ep: Path) -> dict:
    resolved = resolve_grammar(ep)
    data = resolved["data"]

    authorship = data.get("camera_authorship") or {}
    roster = data.get("camera_roster") or {}
    snap = data.get("snapshot_language") or {}
    moment = data.get("moment_contract") or {}
    opening = data.get("opening_memory") or {}
    diversity = data.get("shot_grammar_diversity") or {}
    defects = data.get("camera_defect_physics") or {}
    memory = data.get("visual_memory_continuity") or {}
    screen = data.get("screen_content_physics") or {}
    interop = data.get("visual_profile_interop") or {}
    forbidden = data.get("forbidden") or []
    review = data.get("review_questions") or []

    lines = [
        f"capture_grammar={resolved['grammar_id']}",
        "CAPTURE GRAMMAR HAS HIGHER PRIORITY THAN VISUAL PROFILE composition/photography when they conflict.",
        f"principle={data.get('principle') or ''}",

        "CAMERA AUTHORSHIP:",
        f"camera_operator={authorship.get('operator', 'participant_or_companion_inside_event')}",
        f"viewpoint={authorship.get('viewpoint', 'first_person_or_companion_eye')}",
        f"camera_position={authorship.get('distance', 'physically_plausible_human_position')}",
        _b("floating_omniscient_camera", authorship.get("floating_omniscient_camera"), False),
        _b("ghost_camera_forbidden", authorship.get("ghost_camera_forbidden"), True),
        _b("each_frame_must_resolve_camera_owner", authorship.get("each_frame_must_resolve_camera_owner"), True),

        "CAMERA ROSTER:",
        _b("primary_photographer_required", roster.get("primary_photographer_required"), True),
        f"primary_photographer_preferred_share={roster.get('primary_photographer_preferred_share', '70-80%')}",
        _b("secondary_requires_reason", roster.get("secondary_requires_reason"), True),
        f"all_participants_visible_rule={roster.get('all_known_participants_visible_rule') or 'all visible requires a real camera source; otherwise ghost camera'}",

        "SNAPSHOT LANGUAGE:",
        _b("handheld", snap.get("handheld"), True),
        _b("unposed", snap.get("unposed"), True),
        _b("imperfect_framing", snap.get("imperfect_framing"), True),
        _b("first_person_is_logic_not_fixed_composition", snap.get("first_person_is_logic_not_fixed_composition"), True),
        _b("phone_in_frame_not_required", snap.get("phone_in_frame_not_required"), True),
        "subjects do not need to face camera; avoid arranging people for the image",
        "allow partial occlusion and foreground body/hand/doorframe/vehicle edge when physically natural",

        "MOMENT:",
        _b("must_express_ongoing_action", moment.get("must_express_ongoing_action"), True),
        _b("must_have_save_reason", moment.get("must_have_save_reason"), True),
        _b("avoid_result_only_showcase", moment.get("avoid_result_only_showcase"), True),

        "OPENING MEMORY:",
        f"opening_goal={opening.get('goal') or 'establish relationship, ordinary life and emotional asset before anomaly'}",
        f"large_group_photo_rule={opening.get('large_group_photo_rule') or 'casual, unposed, physically sourced'}",

        "SHOT DIVERSITY:",
        f"shot_diversity_rule={diversity.get('rule') or 'first person is logic, not a repeated hand+phone template'}",
        f"avoid_same_shot_family_more_than_consecutive={diversity.get('avoid_same_shot_family_more_than_consecutive', 2)}",
        f"ten_frame_distinct_shot_families_min={diversity.get('ten_frame_window_recommended_distinct_families_min', 4)}",
        _b("repeated_hand_phone_distant_anomaly_template_forbidden", diversity.get("repeated_hand_phone_distant_anomaly_template_forbidden"), True),

        "CAMERA DEFECT PHYSICS:",
        _b("defects_must_have_physical_cause", defects.get("defects_must_have_physical_cause"), True),
        _b("forbid_decorative_fake_damage", defects.get("forbid_decorative_fake_damage"), True),
        _b("forbid_every_night_frame_equally_blurred", defects.get("forbid_every_night_frame_equally_blurred"), True),

        "VISUAL MEMORY:",
        _b("time_of_day_must_progress_plausibly", memory.get("time_of_day_must_progress_plausibly"), True),
        _b("time_reversal_requires_explicit_flashback_or_jump", memory.get("time_reversal_requires_explicit_flashback_or_jump"), True),
        _b("no_independent_beauty_time_selection_per_frame", memory.get("no_independent_beauty_time_selection_per_frame"), True),
        "persist_continuity=" + "; ".join(map(str, memory.get("persist") or [
            "character_appearance", "wardrobe", "vehicle", "carried_props",
            "route_and_location", "weather", "lighting", "anomaly_evidence"
        ])),

        "SCREEN CONTENT PHYSICS:",
        _b("screen_must_be_internally_consistent", screen.get("must_be_internally_consistent"), True),
        _b("screen_must_match_scene_when_story_critical", screen.get("must_match_scene_time_route_and_action_when_story_critical"), True),
        _b("screen_reflection_and_orientation_must_be_physical", screen.get("screen_reflection_and_orientation_must_be_physical"), True),
        _b("forbid_fake_impossible_camera_ui", screen.get("forbid_fake_impossible_camera_ui"), True),

        f"subject_visibility_rule={data.get('subject_visibility_rule') or ''}",
        f"selfie_rule={data.get('selfie_rule') or ''}",
        "visual profile supplies texture/era/color/light; capture grammar supplies camera authorship, moment, shot diversity and camera physics",
        "do not convert film/cinematic texture into staged movie-still blocking",
    ]

    if forbidden:
        lines.append("capture_forbidden=" + "; ".join(map(str, forbidden)))
    if review:
        lines.append("capture_review_questions=" + " | ".join(map(str, review)))

    return {
        **{k: v for k, v in resolved.items() if k != "data"},
        "text": "\n".join(lines),
        "interop": interop,
        "camera_roster": roster,
        "shot_grammar_diversity": diversity,
        "camera_defect_physics": defects,
        "visual_memory_continuity": memory,
        "screen_content_physics": screen,
    }


if __name__ == "__main__":
    d = default_grammar()
    assert d["grammar_id"] == DEFAULT_ID
    c = compile_capture_contract(ROOT)
    assert "ghost_camera_forbidden=true" in c["text"]
    assert "repeated_hand_phone_distant_anomaly_template_forbidden=true" in c["text"]
    print("CAPTURE GRAMMAR V2.2.8 SELF-TEST PASS")
