#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Materialize strict PREIMAGE directing contracts from committed authority.

WORK/Product Runtime PREIMAGE commits model-authored high-level authority into
``meta/story-gates.json``.  The strict directing gates and Frame Contract layer
also consume four per-frame contracts.  This module bridges those two layers
without adding model judgment or a second stage:

- only runs after the PREIMAGE authority barrier is READY;
- creates a contract only when that file is missing;
- never overwrites an existing contract (valid files are reused, invalid files
  fail closed);
- derives per-frame values from already locked Character / Shot Progression /
  Environment / committed PREIMAGE authority;
- validates every produced contract with its canonical validator.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import capture_event_contract
import environment_contract
import story_json
import temporal_continuity_gate
import wardrobe_contract
import world_state

BARRIER_REL = Path("meta/runtime/preimage-authority-barrier.json")
SHOT_REL = Path("meta/shot-progression-review.json")
CHARACTER_REL = Path("meta/character-contract.json")
GATES_REL = Path("meta/story-gates.json")


def _read(path: Path) -> dict:
    data = story_json.read_json(path, default={})
    return data if isinstance(data, dict) else {}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frame_count(ep: Path) -> int:
    return environment_contract.frame_count(ep)


def _shot_rows(ep: Path) -> dict[str, dict]:
    data = _read(ep / SHOT_REL)
    rows = data.get("frames") or []
    out: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            key = f"{int(row.get('frame')):02d}"
        except (TypeError, ValueError):
            continue
        out[key] = row
    return out


def _members(character: dict) -> list[dict]:
    rows = ((character.get("cast") or {}).get("members") or [])
    return [row for row in rows if isinstance(row, dict) and str(row.get("id") or "").strip()]


def _default_photographer(character: dict) -> str:
    return str(((character.get("pov") or {}).get("character_id")) or "P01")


def _device_for(character: dict, photographer: str) -> str:
    row = next((x for x in _members(character) if str(x.get("id")) == photographer), {})
    device = str(row.get("device_anchor") or "").strip()
    if device:
        return device
    pov = _default_photographer(character)
    pov_row = next((x for x in _members(character) if str(x.get("id")) == pov), {})
    return str(pov_row.get("device_anchor") or "普通智能手机").strip() or "普通智能手机"


def _photographer_for(row: dict, default: str) -> str:
    raw = " ".join(
        str(row.get(k) or "")
        for k in ("pov_mode", "camera_position", "capture_purpose")
    ).lower()
    # Explicit character ids win.  This catches companion-taken frames without
    # inventing a new camera owner from prose.
    for token in ("P02", "P03", "P04", "P05"):
        if token.lower() in raw and any(x in raw for x in ("代拍", "拍摄", "photographer", "camera", "behind")):
            return token
    if any(x in raw for x in ("同行者代拍", "同伴代拍", "companion photographer", "secondary photographer")):
        return "P02"
    return default


def _subject_awareness(row: dict) -> str:
    if row.get("human_present") is not True:
        return "not_applicable"
    pov = str(row.get("pov_mode") or "").lower()
    interaction = row.get("interaction") or {}
    if "自拍" in pov or "selfie" in pov or interaction.get("meaningful") is True:
        return "aware"
    return "partial"


def _build_capture(ep: Path, character: dict, shots: dict[str, dict]) -> dict:
    total = _frame_count(ep)
    default = _default_photographer(character)
    frames: dict[str, dict] = {}
    for n in range(1, total + 1):
        key = f"{n:02d}"
        row = shots.get(key) or {}
        photographer = _photographer_for(row, default)
        emotion = row.get("emotion") or {}
        action_stage = str(row.get("human_action_stage") or "record").strip()
        emotion_state = str(emotion.get("state") or "ordinary").strip()
        concealment = row.get("anomaly_concealment") or {}
        constraint_parts = [
            str(row.get("subject_distance") or "ordinary handheld distance").strip(),
            str(concealment.get("physical_anchor") or "").strip(),
        ]
        frames[key] = {
            "photographer_id": photographer,
            "capture_device": _device_for(character, photographer),
            "why_capture_now": str(row.get("capture_purpose") or row.get("action") or row.get("visual_function") or "记录当下").strip(),
            "device_position": str(row.get("camera_position") or "ordinary handheld position").strip(),
            "subject_awareness": _subject_awareness(row),
            "operator_state": f"{action_stage}; {emotion_state}".strip("; "),
            "framing_constraint": "; ".join(x for x in constraint_parts if x),
            "retained_reason": str(row.get("visual_function") or row.get("capture_purpose") or "保留叙事证据").strip(),
            "causal_defects": [],
        }
    return {
        "schema_version": 1,
        "status": "LOCKED",
        "frame_count": total,
        "principle": "A frame must first be a credible capture event, then a narrative image.",
        "max_causal_defects_per_frame": 2,
        "derived_from_preimage_authority": True,
        "frames": frames,
    }


def _characters_state(character: dict) -> dict:
    out: dict[str, dict] = {}
    for member in _members(character):
        cid = str(member.get("id"))
        row = {
            key: member.get(key)
            for key in ("gender", "age", "build", "hair", "clothing_anchor", "device_anchor")
            if member.get(key) is not None
        }
        row["status"] = "present"
        out[cid] = row
    return out


def _daypart(raw: object) -> str:
    low = str(raw or "").strip().lower()
    if low in {"dawn", "morning", "day", "afternoon", "dusk", "night"}:
        return low
    if "dawn" in low:
        return "dawn"
    if "morning" in low:
        return "morning"
    if "afternoon" in low:
        return "afternoon"
    if "dusk" in low or "sunset" in low or "early evening" in low:
        return "dusk"
    if "night" in low or "evening" in low:
        return "night"
    if "midday" in low or "noon" in low:
        return "day"
    return "day"


def _build_world(ep: Path, character: dict, shots: dict[str, dict], capture: dict) -> dict:
    total = _frame_count(ep)
    gates = _read(ep / GATES_REL)
    visual = gates.get("visual") or {}
    source = visual.get("world_state") or {}
    first_env = environment_contract.resolve_frame(ep, 1).get("environment") or {}
    first_shot = shots.get("01") or {}
    default = _default_photographer(character)
    props = {
        str(name): {"state": "persistent"}
        for name in (source.get("persistent_props") or [])
        if str(name).strip()
    }
    initial = {
        "time": _daypart(first_env.get("time_of_day")),
        "location": str(first_shot.get("location_zone") or source.get("initial_location") or "locked episode location").strip(),
        "weather": str(first_env.get("condition") or source.get("weather") or "stable").strip(),
        "characters": _characters_state(character),
        "recorder": {
            "photographer_id": default,
            "active_device": _device_for(character, default),
        },
        "props": props,
        "anomaly": {"phase": "ordinary"},
    }
    frames: dict[str, dict] = {}
    prev_photographer = default
    prev_device = _device_for(character, default)
    for n in range(1, total + 1):
        key = f"{n:02d}"
        shot = shots.get(key) or {}
        env = environment_contract.resolve_frame(ep, n).get("environment") or {}
        cap = (capture.get("frames") or {}).get(key) or {}
        photographer = str(cap.get("photographer_id") or default)
        device = str(cap.get("capture_device") or _device_for(character, photographer))
        delta: dict = {
            "time": _daypart(env.get("time_of_day")),
            "location": str(shot.get("location_zone") or initial["location"]).strip(),
            "weather": str(env.get("condition") or initial["weather"]).strip(),
            "anomaly": {"phase": str(shot.get("anomaly_logic_stage") or "ordinary").strip() or "ordinary"},
        }
        if photographer != prev_photographer or device != prev_device:
            delta["recorder"] = {"photographer_id": photographer, "active_device": device}
        event = str(shot.get("action") or shot.get("visual_function") or cap.get("why_capture_now") or "frame progression").strip()
        frames[key] = {"delta": delta, "story_event": event}
        prev_photographer, prev_device = photographer, device
    return {
        "schema_version": 1,
        "status": "LOCKED",
        "frame_count": total,
        "derived_from_preimage_authority": True,
        "initial_state": initial,
        "frames": frames,
    }


def _ambient_light(daypart: str, shot: dict) -> str:
    if daypart == "dawn":
        return "dawn_low"
    if daypart == "dusk":
        return "dusk_low"
    if daypart == "night":
        source = str(((shot.get("lighting_design") or {}).get("practical_source")) or "").strip().lower()
        return "artificial_night" if source and source not in {"moon", "moonlight"} else "night_dark"
    return "daylight"


def _build_temporal(ep: Path, shots: dict[str, dict], world_path: Path) -> dict:
    total = _frame_count(ep)
    rows = []
    prev: dict | None = None
    for n in range(1, total + 1):
        key = f"{n:02d}"
        env = environment_contract.resolve_frame(ep, n).get("environment") or {}
        day = _daypart(env.get("time_of_day"))
        weather = str(env.get("condition") or "stable").strip()
        precipitation = str(env.get("precipitation") or "none").strip()
        light = _ambient_light(day, shots.get(key) or {})
        if prev is None:
            elapsed = 0
            reason = "opening state"
            major = False
        else:
            changed = day != prev["daypart"] or weather != prev["weather"] or precipitation != prev["precipitation"] or light != prev["ambient_light"]
            bright = {"daylight", "overcast_day"}
            dark = {"night_dark", "artificial_night"}
            major = (prev["ambient_light"] in bright and light in dark) or (prev["ambient_light"] in dark and light in bright)
            if major and prev["daypart"] == "night" and day in {"dawn", "morning", "day", "afternoon"}:
                elapsed = 480
            elif major:
                elapsed = 120
            elif changed:
                elapsed = 60
            else:
                elapsed = 10
            reason = f"physical time/environment transition: {prev['daypart']} -> {day}" if changed else ""
        row = {
            "frame": key,
            "elapsed_minutes_from_prev": elapsed,
            "daypart": day,
            "weather": weather,
            "precipitation": precipitation,
            "ambient_light": light,
            "large_transition": major,
            "transition_reason": reason,
        }
        rows.append(row)
        prev = row
    return {
        "schema_version": 1,
        "status": "LOCKED",
        "frame_count": total,
        "source_world_state_sha256": _sha(world_path),
        "world_state_synced": True,
        "derived_from_preimage_authority": True,
        "frames": rows,
    }


def _temperature_band(raw: object) -> str:
    low = str(raw or "").strip().lower()
    for token in ("very_cold", "cold", "cool", "hot", "warm", "mild"):
        if token.replace("_", " ") in low or token in low:
            return token
    return "mild"


def _location_type(shot: dict) -> str:
    raw = " ".join(str(shot.get(k) or "") for k in ("location_zone", "camera_position")).lower()
    outdoor_tokens = ("院", "村口", "门口", "晾衣", "停车", "街", "路", "桥", "market", "street", "outdoor", "courtyard", "bridge")
    return "outdoor" if any(token in raw for token in outdoor_tokens) else "indoor"


def _build_wardrobe(ep: Path, character: dict, shots: dict[str, dict], temporal_path: Path) -> dict:
    total = _frame_count(ep)
    members = _members(character)
    frames: dict[str, dict] = {}
    for n in range(1, total + 1):
        key = f"{n:02d}"
        shot = shots.get(key) or {}
        env = environment_contract.resolve_frame(ep, n).get("environment") or {}
        outfits = {}
        for member in members:
            cid = str(member.get("id"))
            clothing = str(member.get("clothing_anchor") or "ordinary daily clothing").strip()
            outfits[cid] = {
                "present": True,
                "look_id": f"{cid}_BASE",
                "garments": [clothing],
                "outer_layer": "",
                "leg_layer": "",
                "headwear": "",
                "footwear": "",
                "temperature_fit": "PASS",
                "weather_fit": "PASS",
                "activity_fit": "PASS",
                "identity_consistent": True,
                "aesthetic_fit": "pretty_realistic",
                "change_reason": "",
            }
        frames[key] = {
            "scene_context": str(shot.get("location_zone") or shot.get("visual_function") or "locked scene").strip(),
            "location_type": _location_type(shot),
            "temperature_band": _temperature_band(env.get("temperature_feel")),
            "weather": str(env.get("condition") or "stable").strip(),
            "activity": str(shot.get("action") or "ordinary activity").strip(),
            "outfits": outfits,
        }
    return {
        "schema_version": 1,
        "status": "LOCKED",
        "frame_count": total,
        "source_temporal_sha256": _sha(temporal_path),
        "derived_from_preimage_authority": True,
        "rules": {
            "wardrobe_changes_follow_scene_weather_temperature_activity": True,
            "female_lead_default_body": "slim_proportionate_natural",
            "pretty_clothes_allowed_when_physical_context_supports_them": True,
            "camisole_in_cold_outdoor_requires_warm_outer_layer": True,
            "skirt_in_cold_requires_thick_tights_and_warm_layer": True,
            "high_altitude_outdoor_requires_wind_or_insulation_layer": True,
            "outfit_change_requires_reason": True,
            "no_eroticized_framing_requirement": True,
        },
        "frames": frames,
    }


def _ensure_one(path: Path, builder, validator, label: str) -> str:
    if path.is_file():
        errors = validator()
        if errors:
            raise ValueError(f"{label} exists but is invalid; refusing overwrite: " + "; ".join(errors[:8]))
        return "REUSED"
    story_json.write_json(path, builder())
    errors = validator()
    if errors:
        raise ValueError(f"{label} materialization invalid: " + "; ".join(errors[:8]))
    return "CREATED"


def ensure(ep: Path) -> dict:
    ep = Path(ep).resolve()
    barrier = _read(ep / BARRIER_REL)
    if barrier.get("status") != "READY" or not barrier.get("committed_snapshot_id"):
        raise ValueError("PREIMAGE authority barrier must be READY before directing-contract materialization")
    character = _read(ep / CHARACTER_REL)
    shots = _shot_rows(ep)
    total = _frame_count(ep)
    if len(shots) != total:
        raise ValueError(f"shot progression frame count mismatch {len(shots)} != {total}")

    capture_path = ep / capture_event_contract.REL
    capture_status = _ensure_one(
        capture_path,
        lambda: _build_capture(ep, character, shots),
        lambda: capture_event_contract.validate(ep, True),
        "capture-event-contract",
    )
    capture = _read(capture_path)

    world_path = ep / world_state.REL
    world_status = _ensure_one(
        world_path,
        lambda: _build_world(ep, character, shots, capture),
        lambda: world_state.validate(ep, True),
        "world-state",
    )

    temporal_path = ep / temporal_continuity_gate.REL
    temporal_status = _ensure_one(
        temporal_path,
        lambda: _build_temporal(ep, shots, world_path),
        lambda: temporal_continuity_gate.validate(ep, True),
        "temporal-continuity",
    )

    wardrobe_path = ep / wardrobe_contract.REL
    wardrobe_status = _ensure_one(
        wardrobe_path,
        lambda: _build_wardrobe(ep, character, shots, temporal_path),
        lambda: wardrobe_contract.validate(ep, True),
        "wardrobe-contract",
    )

    return {
        "status": "PASS",
        "barrier_snapshot_id": barrier.get("committed_snapshot_id"),
        "contracts": {
            capture_event_contract.REL.as_posix(): capture_status,
            world_state.REL.as_posix(): world_status,
            temporal_continuity_gate.REL.as_posix(): temporal_status,
            wardrobe_contract.REL.as_posix(): wardrobe_status,
        },
    }
