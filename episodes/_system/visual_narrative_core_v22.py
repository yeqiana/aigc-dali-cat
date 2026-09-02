#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.2 Visual Narrative Core R2.

Formal activation is version-based, never file-presence based.

Modes:
- production: Episode tool_version >= 2.2.0; canonical schema-2 LOCKED
  meta/shot-progression-review.json is mandatory.
- legacy: Episode tool_version < 2.2.0; core is NOT_APPLICABLE.
- regression: legacy Episode may explicitly opt into a
  NON_AUTHORITY_REGRESSION_ONLY test input. Regression input can never satisfy
  Production / Visual Lock / release authority.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import capture_grammar_v228
import shot_progression_gate

ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_REL = Path("meta/shot-progression-review.json")
CONFIG_REL = Path("meta/visual-narrative-core.json")
REGRESSION_INPUT_REL = Path("meta/tests/visual-narrative-regression/shot-progression-review.json")
CORE_ID = "VISUAL_NARRATIVE_CORE_V2.2"
FORMAL_MIN_VERSION = (2, 2, 0)
FORBIDDEN_POV_TOKENS = {
    "omniscient", "god_view", "god-view", "floating", "director",
    "impossible_third_person",
}
RECAP_FUNCTIONS = {"recap", "repeat", "duplicate", "same_evidence"}


def _read(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sha(data: Any) -> str:
    raw = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:
        return (0,)


def episode_version(ep: Path) -> str:
    ep = Path(ep)
    versions: list[tuple[tuple[int, ...], str]] = []
    for rel in (
        "meta/episode-state.json",
        "meta/release-manifest.json",
        "meta/story-gates.json",
    ):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            raw = str(_read(p).get("tool_version") or "")
            vt = _version_tuple(raw)
            if vt != (0,):
                versions.append((vt, raw))
        except Exception:
            continue
    return max(versions, key=lambda x: x[0])[1] if versions else ""


def _config(ep: Path) -> dict | None:
    p = Path(ep) / CONFIG_REL
    return _read(p) if p.is_file() else None


def activation(ep: Path) -> dict:
    ep = Path(ep).resolve()
    version = episode_version(ep)
    cfg = _config(ep)

    if _version_tuple(version) >= FORMAL_MIN_VERSION:
        return {
            "active": True,
            "formal": True,
            "mode": "production",
            "reason": "episode_version_gte_2_2_0",
            "episode_version": version,
            "input_path": PRODUCTION_REL.as_posix(),
            "authority": "PREPRODUCTION_DERIVED_CONTRACT",
            "config_errors": [],
        }

    if cfg is not None and cfg.get("enabled") is True:
        mode = str(cfg.get("mode") or "").strip().lower()
        contract_version = str(cfg.get("contract_version") or "").strip()
        authority = str(cfg.get("authority") or "").strip()
        raw_input = str(
            cfg.get("input_path") or REGRESSION_INPUT_REL.as_posix()
        ).strip()
        errors: list[str] = []

        if mode != "regression":
            errors.append("legacy episodes may only use mode=regression")
        if not contract_version.startswith("2.2"):
            errors.append("regression contract_version must be 2.2.x")
        if authority != "NON_AUTHORITY_REGRESSION_ONLY":
            errors.append(
                "regression authority must be NON_AUTHORITY_REGRESSION_ONLY"
            )
        rel = Path(raw_input)
        if rel.is_absolute() or ".." in rel.parts:
            errors.append("regression input_path must be safe repository-relative")

        return {
            "active": mode == "regression" and not errors,
            "formal": False,
            "mode": mode or "invalid",
            "reason": (
                "explicit_legacy_regression_opt_in"
                if mode == "regression"
                else "invalid_legacy_opt_in"
            ),
            "episode_version": version,
            "input_path": raw_input,
            "authority": authority,
            "config_errors": errors,
        }

    return {
        "active": False,
        "formal": False,
        "mode": "legacy",
        "reason": "episode_version_lt_2_2_0",
        "episode_version": version,
        "input_path": None,
        "authority": None,
        "config_errors": [],
    }


def active(ep: Path) -> bool:
    return activation(ep).get("active") is True


def required(ep: Path) -> bool:
    """Formal production requirement only."""
    a = activation(ep)
    return a.get("active") is True and a.get("formal") is True


def regression_active(ep: Path) -> bool:
    a = activation(ep)
    return (
        a.get("active") is True
        and a.get("formal") is False
        and a.get("mode") == "regression"
    )


def input_path(ep: Path) -> Path | None:
    a = activation(ep)
    raw = a.get("input_path")
    if not raw:
        return None
    p = (Path(ep) / raw).resolve()
    try:
        p.relative_to(Path(ep).resolve())
    except ValueError as exc:
        raise ValueError("visual narrative input escapes episode") from exc
    return p


def activation_errors(ep: Path) -> list[str]:
    a = activation(ep)
    cfg_errors = list(a.get("config_errors") or [])
    if cfg_errors:
        return [
            "VISUAL_NARRATIVE_ACTIVATION_INVALID:" + x for x in cfg_errors
        ]
    if not a.get("active"):
        return []

    p = input_path(ep)
    if p is None or not p.is_file():
        return [
            f"VISUAL_NARRATIVE_INPUT_MISSING:"
            f"{a.get('mode')}:{a.get('input_path')}"
        ]

    try:
        data = _read(p)
    except Exception as exc:
        return [f"VISUAL_NARRATIVE_INPUT_INVALID:{exc}"]

    if int(data.get("schema_version") or 0) != 2:
        return ["VISUAL_NARRATIVE_INPUT_SCHEMA_MISMATCH:expected=2"]
    if data.get("status") != "LOCKED":
        return ["VISUAL_NARRATIVE_INPUT_NOT_LOCKED"]
    rows = data.get("frames")
    if not isinstance(rows, list) or not rows:
        return ["VISUAL_NARRATIVE_ZERO_FRAME_INPUT"]
    return []


def _input(ep: Path) -> dict:
    p = input_path(ep)
    if p is None or not p.is_file():
        raise ValueError("VISUAL_NARRATIVE_INPUT_MISSING")
    return _read(p)


def _frame_row(ep: Path, frame: int) -> dict:
    data = _input(ep)
    key = f"{frame:02d}"
    return next(
        (
            row
            for row in data.get("frames") or []
            if str(row.get("frame") or "").zfill(2) == key
        ),
        {},
    )


def _family(row: dict) -> str:
    raw = " ".join(
        str(row.get(k) or "").strip().lower()
        for k in (
            "camera_position",
            "subject_distance",
            "pov_mode",
            "location_zone",
        )
    )
    rules = [
        (
            "inside_vehicle",
            ("车内", "inside_vehicle", "driver", "passenger", "dashboard"),
        ),
        ("through_glass", ("隔窗", "through_glass", "windshield", "window")),
        ("over_shoulder", ("肩后", "over_shoulder", "over-shoulder")),
        ("doorway_edge", ("门框", "车门", "doorway", "vehicle_edge")),
        ("walking_capture", ("步行", "走路", "walking", "moving")),
        ("reaction_frame", ("反应", "reaction", "close", "medium")),
        ("object_detail", ("细节", "detail", "hand", "手部", "prop")),
        ("low_light_distance", ("远摄", "tele", "night", "夜")),
        (
            "reflection_occlusion",
            ("反射", "reflection", "occlusion", "遮挡"),
        ),
        ("selfie", ("selfie", "自拍")),
    ]
    for family, tokens in rules:
        if any(token in raw for token in tokens):
            return family
    pos = (
        str(row.get("camera_position") or "unknown")
        .strip()
        .lower()
        .replace(" ", "_")
    )
    return "other:" + pos


def _owner_class(row: dict) -> str:
    pov = str(row.get("pov_mode") or "").strip().lower()
    itype = str(
        ((row.get("interaction") or {}).get("type")) or ""
    ).strip().lower()
    if "selfie" in pov or itype == "group_selfie":
        return "selfie_operator"
    if any(
        x in pov for x in ("companion", "secondary", "同行", "同伴")
    ):
        return "secondary_or_companion_photographer"
    if any(
        x in pov for x in ("first", "pov", "primary", "第一", "主摄影")
    ):
        return "primary_photographer"
    if any(x in pov for x in FORBIDDEN_POV_TOKENS):
        return "FORBIDDEN_CAMERA_LOGIC"
    return "diegetic_operator_must_be_resolved"


def resolve_frame(ep: Path, frame: int | str) -> dict:
    ep = Path(ep).resolve()
    if not active(ep):
        raise ValueError("VISUAL_NARRATIVE_NOT_APPLICABLE")
    errors = activation_errors(ep)
    if errors:
        raise ValueError("; ".join(errors))

    n = int(frame)
    key = f"{n:02d}"
    row = _frame_row(ep, n)
    if not row:
        raise ValueError(f"VISUAL_NARRATIVE_MISSING:{key}")

    capture = capture_grammar_v228.compile_capture_contract(ep)
    act = activation(ep)

    contract = {
        "core_id": CORE_ID,
        "activation_mode": act["mode"],
        "authority": act["authority"],
        "frame": key,
        "camera_authorship": {
            "owner_class": _owner_class(row),
            "pov_mode": row.get("pov_mode"),
            "camera_position": row.get("camera_position"),
            "ghost_camera_forbidden": True,
            "camera_owner_must_be_physically_explainable": True,
        },
        "moment": {
            "action_in_progress": str(row.get("action") or "").strip(),
            "save_reason": str(row.get("capture_purpose") or "").strip(),
            "must_not_be_result_only_showcase": True,
        },
        "shot_grammar": {
            "family": _family(row),
            "subject_distance": row.get("subject_distance"),
            "location_zone": row.get("location_zone"),
            "first_person_is_logic_not_fixed_composition": True,
            "repeated_hand_phone_distant_anomaly_template_forbidden": True,
        },
        "narrative_evidence": {
            "new_information": row.get("new_information"),
            "new_information_this_frame": str(
                row.get("visual_function") or ""
            ).strip(),
            "anomaly_logic_stage": row.get("anomaly_logic_stage"),
            "human_action_stage": row.get("human_action_stage"),
            "narrative_redundancy_forbidden": True,
            "continuity_exception_reason": str(
                row.get("continuity_exception_reason") or ""
            ).strip(),
        },
        "human_response": {
            "human_present": row.get("human_present"),
            "emotion": row.get("emotion") or {},
            "interaction": row.get("interaction") or {},
        },
        "camera_roster_policy": capture.get("camera_roster") or {},
        "camera_defect_physics": capture.get("camera_defect_physics") or {},
        "visual_memory_continuity": (
            capture.get("visual_memory_continuity") or {}
        ),
        "screen_content_physics": (
            capture.get("screen_content_physics") or {}
        ),
    }

    return {
        "frame": key,
        "activation": act,
        "visual_narrative": contract,
        "visual_narrative_sha256": _sha(contract),
    }


def _validate_row(row: dict, n: int) -> list[str]:
    errors: list[str] = []
    for key in (
        "camera_position",
        "pov_mode",
        "action",
        "capture_purpose",
        "visual_function",
    ):
        if not str(row.get(key) or "").strip():
            errors.append(
                f"VISUAL_NARRATIVE_FIELD_MISSING:{n:02d}:{key}"
            )

    pov = str(row.get("pov_mode") or "").lower()
    if any(token in pov for token in FORBIDDEN_POV_TOKENS):
        errors.append(f"CAMERA_LOGIC_INVALID:{n:02d}:{pov}")

    exception = str(
        row.get("continuity_exception_reason") or ""
    ).strip()
    if n > 1 and row.get("new_information") is not True and not exception:
        errors.append(
            f"NARRATIVE_REDUNDANCY:{n:02d}:"
            "new_information must be true or deliberate repetition explained"
        )

    visual_function = str(
        row.get("visual_function") or ""
    ).strip().lower()
    if (
        n > 1
        and visual_function in RECAP_FUNCTIONS
        and not exception
    ):
        errors.append(
            f"NARRATIVE_EVIDENCE_REPEAT:{n:02d}:{visual_function}"
        )
    return errors


def _validate_sequence(data: dict) -> list[str]:
    errors: list[str] = []
    rows = data.get("frames")
    if not isinstance(rows, list) or not rows:
        return ["VISUAL_NARRATIVE_ZERO_FRAME_INPUT"]

    normalized: list[tuple[int, dict]] = []
    for row in rows:
        if not isinstance(row, dict):
            errors.append("VISUAL_NARRATIVE_FRAME_ROW_INVALID")
            continue
        try:
            n = int(row.get("frame"))
        except Exception:
            errors.append("VISUAL_NARRATIVE_FRAME_ID_INVALID")
            continue
        normalized.append((n, row))
        errors.extend(_validate_row(row, n))

    normalized.sort(key=lambda x: x[0])
    families = [(n, _family(row)) for n, row in normalized]
    if len(families) >= 5:
        window_size = 10 if len(families) >= 10 else len(families)
        for start in range(len(families) - window_size + 1):
            window = families[start : start + window_size]
            if len({family for _, family in window}) < 3:
                errors.append(
                    "SHOT_GRAMMAR_DIVERSITY_FAIL:"
                    f"{window[0][0]:02d}-{window[-1][0]:02d}"
                )
                break
    return errors


def verify_frame(ep: Path, frame: int | str) -> list[str]:
    ep = Path(ep).resolve()
    if not active(ep):
        return []
    errors = activation_errors(ep)
    if errors:
        return errors
    n = int(frame)
    row = _frame_row(ep, n)
    if not row:
        return [f"VISUAL_NARRATIVE_MISSING:{n:02d}"]
    return _validate_row(row, n)


def verify_all(ep: Path) -> list[str]:
    ep = Path(ep).resolve()
    if not active(ep):
        return []

    errors = activation_errors(ep)
    if errors:
        return errors

    data = _input(ep)
    if required(ep):
        errors.extend(
            shot_progression_gate.validate(ep, require_locked=True)
        )
    else:
        # Regression input is never passed to the formal production gate.
        errors.extend(_validate_sequence(data))
    return errors


def _frame_count_for_regression(ep: Path) -> int:
    p = Path(ep) / "meta/release-manifest.json"
    if not p.is_file():
        raise ValueError(
            "REGRESSION_FRAME_COUNT_UNRESOLVED:"
            "release-manifest.json missing"
        )
    data = _read(p)
    n = int(((data.get("release") or {}).get("body_frame_count")) or 0)
    if n <= 0:
        raise ValueError(
            "REGRESSION_FRAME_COUNT_UNRESOLVED:"
            "release.body_frame_count invalid"
        )
    return n


def prepare_regression(ep: Path, *, force: bool = False) -> dict:
    """Create a non-authority scaffold; never create production authority."""
    ep = Path(ep).resolve()
    if _version_tuple(episode_version(ep)) >= FORMAL_MIN_VERSION:
        raise ValueError(
            "REGRESSION_PREP_FORBIDDEN_ON_FORMAL_V22_EPISODE"
        )

    cfg_path = ep / CONFIG_REL
    input_p = ep / REGRESSION_INPUT_REL
    if (cfg_path.exists() or input_p.exists()) and not force:
        raise ValueError(
            "REGRESSION_SCAFFOLD_EXISTS:"
            "use --force only for explicit test reset"
        )

    total = _frame_count_for_regression(ep)
    rows = []
    for n in range(1, total + 1):
        rows.append(
            {
                "frame": f"{n:02d}",
                "camera_position": "",
                "subject_distance": "",
                "primary_subject": "",
                "action": "",
                "visual_function": "",
                "capture_purpose": "",
                "pov_mode": "",
                "location_zone": "",
                "anomaly_logic_stage": "ordinary",
                "human_action_stage": "ordinary",
                "human_present": False,
                "emotion": {
                    "state": "ordinary",
                    "intensity": 0,
                    "trigger": "",
                    "response_sync": "not_applicable",
                },
                "interaction": {
                    "type": "none",
                    "actor": "",
                    "target": "",
                    "action": "",
                    "meaningful": False,
                },
                "new_information": False,
                "continuity_exception_reason": "",
            }
        )

    scaffold = {
        "schema_version": 2,
        "status": "DRAFT",
        "authority": "NON_AUTHORITY_REGRESSION_ONLY",
        "created_at": dt.datetime.now().isoformat(timespec="seconds"),
        "anomaly_applicable": True,
        "interaction_applicable": False,
        "interaction_exception_reason": "fill during regression",
        "frames": rows,
    }
    cfg = {
        "schema_version": 1,
        "enabled": True,
        "mode": "regression",
        "contract_version": "2.2.0",
        "authority": "NON_AUTHORITY_REGRESSION_ONLY",
        "input_path": REGRESSION_INPUT_REL.as_posix(),
        "production_promotion_forbidden": True,
        "note": (
            "Regression-only migration. "
            "Never use this as Production Authority."
        ),
    }
    _write(input_p, scaffold)
    _write(cfg_path, cfg)

    return {
        "status": "REGRESSION_SCAFFOLD_CREATED",
        "authority": "NON_AUTHORITY_REGRESSION_ONLY",
        "config": CONFIG_REL.as_posix(),
        "input": REGRESSION_INPUT_REL.as_posix(),
        "frame_count": total,
        "next": (
            "Populate from locked legacy Story/Storyboard, "
            "set status=LOCKED, then verify. Do not modify Story."
        ),
    }


def self_test() -> None:
    sample = {
        "camera_position": "inside_vehicle",
        "subject_distance": "medium",
        "pov_mode": "first_person",
        "location_zone": "road",
        "interaction": {"type": "none"},
    }
    assert _family(sample) == "inside_vehicle"
    assert _owner_class(sample) == "primary_photographer"
    assert (
        _owner_class({**sample, "pov_mode": "omniscient"})
        == "FORBIDDEN_CAMERA_LOGIC"
    )
    assert _version_tuple("2.2.0") >= FORMAL_MIN_VERSION
    print("VISUAL NARRATIVE CORE V2.2 R2 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status")
    p.add_argument("episode_dir")

    p = sub.add_parser("verify")
    p.add_argument("episode_dir")
    p.add_argument("--frame", type=int)

    p = sub.add_parser("show")
    p.add_argument("episode_dir")
    p.add_argument("--frame", type=int, required=True)

    p = sub.add_parser("prepare-regression")
    p.add_argument("episode_dir")
    p.add_argument("--force", action="store_true")

    sub.add_parser("self-test")
    args = ap.parse_args()

    if args.cmd == "self-test":
        self_test()
        return 0

    ep = Path(args.episode_dir).resolve()
    act = activation(ep)

    if args.cmd == "status":
        print(json.dumps(act, ensure_ascii=False, indent=2))
        return 0 if not act.get("config_errors") else 2

    if args.cmd == "prepare-regression":
        try:
            result = prepare_regression(ep, force=args.force)
        except Exception as exc:
            print("REGRESSION PREP FAIL:", exc)
            return 2
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if not act.get("active"):
        print(
            "VISUAL_NARRATIVE_NOT_APPLICABLE "
            f"episode_version={act.get('episode_version') or '<none>'} "
            f"reason={act.get('reason')}"
        )
        return 0

    if args.cmd == "show":
        errors = activation_errors(ep)
        if errors:
            for error in errors:
                print("FAIL:", error)
            return 2
        try:
            print(
                json.dumps(
                    resolve_frame(ep, args.frame),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        except Exception as exc:
            print("VISUAL NARRATIVE SHOW FAIL:", exc)
            return 2
        return 0

    errors = (
        verify_frame(ep, args.frame)
        if args.frame is not None
        else verify_all(ep)
    )
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2

    data = _input(ep)
    print(
        "VISUAL NARRATIVE CORE VERIFIED "
        f"mode={act.get('mode')} "
        f"frames={len(data.get('frames') or [])} "
        f"authority={act.get('authority')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
