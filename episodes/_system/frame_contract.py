#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 4 Resolved Frame Contract compiler.

Authority stays in Story / Storyboard / story-gates / Visual Profile.
Files under meta/runtime/contracts are derived caches only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from story_os_contract import story_os_version
from visual_profile import compile_prompt_contract
import environment_contract
import character_contract

ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = Path("meta/runtime/contracts/frames")
INDEX_REL = Path("meta/runtime/contracts/frame-contract-index.json")
MIN_VERSION = (2, 1, 0)
SCHEMA_VERSION = 1
MAX_EXCERPT = 2200


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_json(data: Any) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:
        return (0,)


def episode_version(ep: Path) -> str:
    versions: list[tuple[tuple[int, ...], str]] = []
    for rel in ("meta/episode-state.json", "meta/release-manifest.json", "meta/story-gates.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            raw = str(read_json(p).get("tool_version") or "")
            vt = version_tuple(raw)
            if vt != (0,):
                versions.append((vt, raw))
        except Exception:
            continue
    # Directories without any version evidence (legacy / test fixtures) are not
    # V2.1 episodes; do not force Resolved Frame Contract binding on them.
    return max(versions, key=lambda x: x[0])[1] if versions else ""


def required(ep: Path) -> bool:
    return version_tuple(episode_version(ep)) >= MIN_VERSION


def resolve_ep(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    return ep


def repo_path(raw: object, where: str, *, must_exist: bool = True) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{where} missing")
    p = Path(raw.strip())
    p = p.resolve() if p.is_absolute() else (ROOT / p).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{where} escapes repository") from exc
    if must_exist and not p.is_file():
        raise ValueError(f"{where} missing: {raw}")
    return p


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def manifest(ep: Path) -> dict:
    return read_json(ep / "meta/release-manifest.json")


def gates(ep: Path) -> dict:
    return read_json(ep / "meta/story-gates.json")


def artifact_paths(ep: Path) -> tuple[Path, Path]:
    artifacts = manifest(ep).get("artifacts") or {}
    return (
        repo_path(artifacts.get("story"), "manifest.artifacts.story"),
        repo_path(artifacts.get("storyboard"), "manifest.artifacts.storyboard"),
    )


def frame_count(ep: Path) -> int:
    n = ((manifest(ep).get("release") or {}).get("body_frame_count"))
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("release.body_frame_count must be > 0")
    return n


def _frame_from_json(value: Any, frame: int) -> Any | None:
    if isinstance(value, dict):
        # Direct frame-number keys.
        for key in (str(frame), f"{frame:02d}"):
            if key in value:
                return value[key]
        # Common collections.
        for key in ("frames", "storyboard", "shots", "images", "beats"):
            if key in value:
                found = _frame_from_json(value[key], frame)
                if found is not None:
                    return found
        # Rows carrying a frame identifier.
        raw = value.get("frame") or value.get("number") or value.get("image") or value.get("shot")
        try:
            if raw is not None and int(str(raw).strip()) == frame:
                return value
        except Exception:
            pass
        for child in value.values():
            if isinstance(child, (dict, list)):
                found = _frame_from_json(child, frame)
                if found is not None:
                    return found
    elif isinstance(value, list):
        for item in value:
            found = _frame_from_json(item, frame)
            if found is not None:
                return found
    return None


def extract_frame_excerpt(path: Path, frame: int) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
            found = _frame_from_json(data, frame)
            if found is not None:
                text = json.dumps(found, ensure_ascii=False, sort_keys=True)
                return {"mode": "json_frame", "text": text[:MAX_EXCERPT], "sha256": sha256_bytes(text.encode("utf-8"))}
        except Exception:
            pass

    lines = raw.splitlines()
    # Supports "图 01", "Frame 01", "镜头01", bare numbered headings.
    start = None
    marker = re.compile(
        rf"^\s*(?:#{{1,6}}\s*)?(?:(?:图|镜头|画面|frame|shot)\s*)?0*{frame}(?:\s|[：:、.｜|]|$)",
        re.I,
    )
    any_marker = re.compile(
        r"^\s*(?:#{1,6}\s*)?(?:(?:图|镜头|画面|frame|shot)\s*)?0*\d{1,3}(?:\s|[：:、.｜|]|$)",
        re.I,
    )
    for i, line in enumerate(lines):
        if marker.search(line):
            start = i
            break
    if start is not None:
        end = min(len(lines), start + 40)
        for j in range(start + 1, min(len(lines), start + 60)):
            if any_marker.search(lines[j]):
                end = j
                break
        text = "\n".join(lines[start:end]).strip()[:MAX_EXCERPT]
        if text:
            return {"mode": "text_frame", "text": text, "sha256": sha256_bytes(text.encode("utf-8"))}

    # Safe fallback: broad invalidation if the storyboard format cannot be localized.
    return {
        "mode": "whole_storyboard_fallback",
        "text": "",
        "sha256": sha256_file(path),
    }


def resolved_references(ep: Path, frame: int) -> list[dict]:
    visual = (gates(ep).get("visual") or {})
    out: list[dict] = []
    for item in ((visual.get("references") or {}).get("items") or []):
        if not isinstance(item, dict):
            continue
        applies = item.get("frames") or item.get("frame_scope")
        if isinstance(applies, list):
            normalized = set()
            for x in applies:
                try:
                    normalized.add(int(x))
                except Exception:
                    pass
            if normalized and frame not in normalized:
                continue
        raw = item.get("path")
        row = {
            "id": item.get("id"),
            "role": item.get("role"),
            "kind": item.get("reference_kind") or item.get("kind"),
            "decision": item.get("decision"),
            "path": raw,
        }
        if isinstance(raw, str) and raw.strip():
            try:
                p = repo_path(raw, "visual.references.items.path")
                row["path"] = repo_rel(p)
                row["sha256"] = sha256_file(p)
            except Exception:
                row["sha256"] = None
        out.append(row)
    return out


def _compact_json(value: object, limit: int = 1800) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text if len(text) <= limit else text[:limit] + "…"


def compile_frame(ep: Path, frame: int | str, *, write_cache: bool = True) -> dict:
    total = frame_count(ep)
    try:
        n = int(frame)
    except Exception as exc:
        raise ValueError(f"invalid frame: {frame}") from exc
    if not 1 <= n <= total:
        raise ValueError(f"frame out of range: {n}/{total}")
    key = f"{n:02d}"

    story_path, storyboard_path = artifact_paths(ep)
    g = gates(ep)
    visual = g.get("visual") or {}
    character = read_json(ep / character_contract.REL) if (ep / character_contract.REL).is_file() else {}
    visual_profile = compile_prompt_contract(ep)
    env = environment_contract.resolve_frame(ep, n)
    directive = env.get("directive") or {}
    excerpt = extract_frame_excerpt(storyboard_path, n)
    refs = resolved_references(ep, n)

    source_trace = {
        "story": {"path": repo_rel(story_path), "sha256": sha256_file(story_path)},
        "storyboard": {"path": repo_rel(storyboard_path), "sha256": sha256_file(storyboard_path)},
        "story_gates": {"path": repo_rel(ep / "meta/story-gates.json"), "sha256": sha256_file(ep / "meta/story-gates.json")},
        "visual_profile": {
            "path": visual_profile["profile_path"],
            "sha256": visual_profile["profile_sha256"],
        },
        "character_contract": {
            "path": character_contract.REL.as_posix(),
            "sha256": sha256_file(ep / character_contract.REL) if (ep / character_contract.REL).is_file() else None,
        },
    }

    # Hash material is deliberately per-frame where possible.
    # storyboard source SHA is trace-only; localized excerpt SHA avoids all-frame invalidation.
    hash_material = {
        "schema_version": SCHEMA_VERSION,
        "frame": key,
        "story_sha256": source_trace["story"]["sha256"],
        "storyboard_frame_sha256": excerpt["sha256"],
        "storyboard_extraction_mode": excerpt["mode"],
        "visual_profile": {
            "profile_id": visual_profile["profile_id"],
            "profile_path": visual_profile["profile_path"],
            "profile_sha256": visual_profile["profile_sha256"],
            "capture_profile": visual_profile["capture_profile"],
        },
        "authenticity_card": visual.get("authenticity_card") or {},
        "character_contract": character,
        "continuity": visual.get("continuity") or {},
        "environment": env.get("environment") or {},
        "active_environment_segments": env.get("active_segments") or [],
        "environment_frame_sha256": env["environment_frame_sha256"],
        "frame_directive": directive,
        "frame_directive_sha256": env["frame_directive_sha256"],
        "references": refs,
    }
    contract_sha = sha256_json(hash_material)

    prompt_lines = [
        f"RESOLVED FRAME CONTRACT | frame={key} | sha256={contract_sha}",
        "This derived contract is mandatory. Locked sources outrank ad-hoc prompt wording.",
        "",
        "[STORYBOARD FRAME]",
        excerpt["text"] or f"localized excerpt unavailable; bind storyboard frame hash={excerpt['sha256']}",
        "",
        "[VISUAL DNA]",
        visual_profile["text"],
        "",
        "[CAPTURE / AUTHENTICITY]",
        _compact_json(visual.get("authenticity_card") or {}),
        "",
        "[CHARACTER / POV CONTRACT]",
        _compact_json(character, 2800),
        "",
        "[CONTINUITY]",
        _compact_json(visual.get("continuity") or {}),
        "",
        "[ENVIRONMENT PHYSICS]",
        _compact_json(env.get("environment") or {}),
        "",
        "[FRAME DIRECTIVE]",
        _compact_json(directive),
        "",
        "[REFERENCES CONTRACT]",
        _compact_json(refs),
        "",
        "Hard rule: reality constrains capture physics, not anomaly scale. "
        "Do not weaken impact_level or remove required scale references to make the scene easier.",
    ]

    result = {
        "schema_version": SCHEMA_VERSION,
        "story_os_version": episode_version(ep),
        "frame": key,
        "derived_cache": True,
        "authority": "Story + Storyboard + Character Contract + story-gates + Visual Profile",
        "generated_at": now(),
        "source_trace": source_trace,
        "storyboard_frame": excerpt,
        "hash_material": hash_material,
        "contract_sha256": contract_sha,
        "prompt_contract": "\n".join(prompt_lines),
    }
    if write_cache:
        path = ep / CACHE_ROOT / f"{key}.json"
        write_json(path, result)
    return result


def compile_all(ep: Path) -> dict:
    if required(ep):
        errors = environment_contract.verify(ep)
        if errors:
            raise ValueError("Phase 3 Environment Contract must PASS before Frame Contract compile: " + "; ".join(errors[:8]))
    rows = []
    for n in range(1, frame_count(ep) + 1):
        row = compile_frame(ep, n, write_cache=True)
        rows.append({
            "frame": row["frame"],
            "path": (CACHE_ROOT / f"{row['frame']}.json").as_posix(),
            "contract_sha256": row["contract_sha256"],
            "storyboard_frame_sha256": row["hash_material"]["storyboard_frame_sha256"],
            "environment_frame_sha256": row["hash_material"]["environment_frame_sha256"],
            "frame_directive_sha256": row["hash_material"]["frame_directive_sha256"],
        })
    index = {
        "schema_version": 1,
        "story_os_version": episode_version(ep),
        "derived_cache": True,
        "compiled_at": now(),
        "frame_count": len(rows),
        "frames": rows,
        "index_sha256": sha256_json(rows),
    }
    write_json(ep / INDEX_REL, index)
    return index


def cache_path(ep: Path, frame: int | str) -> Path:
    return ep / CACHE_ROOT / f"{int(frame):02d}.json"


def provenance(ep: Path, frame: int | str) -> dict | None:
    if not required(ep):
        return None
    row = compile_frame(ep, frame, write_cache=True)
    return {
        "schema_version": SCHEMA_VERSION,
        "path": (CACHE_ROOT / f"{row['frame']}.json").as_posix(),
        "contract_sha256": row["contract_sha256"],
    }


def verify_frame(ep: Path, frame: int | str) -> list[str]:
    if not required(ep):
        return []
    current = compile_frame(ep, frame, write_cache=False)
    path = cache_path(ep, frame)
    if not path.is_file():
        return [f"resolved frame contract cache missing: {path.relative_to(ep)}"]
    try:
        cached = read_json(path)
    except Exception as exc:
        return [str(exc)]
    errors = []
    if cached.get("derived_cache") is not True:
        errors.append(f"frame {int(frame):02d} cache must declare derived_cache=true")
    if cached.get("contract_sha256") != current["contract_sha256"]:
        errors.append(f"frame {int(frame):02d} resolved contract stale")
    if cached.get("frame") != current["frame"]:
        errors.append(f"frame {int(frame):02d} cache frame mismatch")
    return errors


def verify_all(ep: Path) -> list[str]:
    if not required(ep):
        return []
    errors = []
    try:
        total = frame_count(ep)
        env_errors = environment_contract.verify(ep)
        if env_errors:
            errors.extend(env_errors)
            return errors
        for n in range(1, total + 1):
            errors.extend(verify_frame(ep, n))
        index_path = ep / INDEX_REL
        if not index_path.is_file():
            errors.append("frame-contract-index.json missing; run compile-all")
        else:
            idx = read_json(index_path)
            rows = idx.get("frames")
            if not isinstance(rows, list) or len(rows) != total:
                errors.append("frame contract index frame count mismatch")
            else:
                expected = []
                for n in range(1, total + 1):
                    row = compile_frame(ep, n, write_cache=False)
                    expected.append({
                        "frame": row["frame"],
                        "path": (CACHE_ROOT / f"{row['frame']}.json").as_posix(),
                        "contract_sha256": row["contract_sha256"],
                        "storyboard_frame_sha256": row["hash_material"]["storyboard_frame_sha256"],
                        "environment_frame_sha256": row["hash_material"]["environment_frame_sha256"],
                        "frame_directive_sha256": row["hash_material"]["frame_directive_sha256"],
                    })
                if idx.get("index_sha256") != sha256_json(expected):
                    errors.append("frame contract index stale")
    except Exception as exc:
        errors.append(str(exc))
    return errors


def verify_recorded_provenance(ep: Path, frame: int | str, recorded: object) -> list[str]:
    if not required(ep):
        return []
    if not isinstance(recorded, dict):
        return [f"frame {int(frame):02d} generation request missing frame_contract provenance"]
    current = compile_frame(ep, frame, write_cache=True)
    errors = []
    if str(recorded.get("contract_sha256") or "").lower() != current["contract_sha256"].lower():
        errors.append(f"frame {int(frame):02d} generation frame_contract_sha256 stale")
    expected_path = (CACHE_ROOT / f"{int(frame):02d}.json").as_posix()
    if str(recorded.get("path") or "") != expected_path:
        errors.append(f"frame {int(frame):02d} generation frame_contract path mismatch")
    return errors


def verify_approved_asset_binding(ep: Path, frame: int | str, asset_sha256: str) -> list[str]:
    """Prove the approved pixels came from an attempt bound to the current frame contract."""
    if not required(ep):
        return []
    key = f"{int(frame):02d}"
    ledger_path = ep / "meta/production-ledger.json"
    if not ledger_path.is_file():
        return [f"frame {key} production ledger missing for frame-contract binding"]
    try:
        ledger = read_json(ledger_path)
        row = (ledger.get("frames") or {}).get(key)
        if not isinstance(row, dict):
            return [f"frame {key} production ledger row missing"]
        approved = row.get("approved_asset") or {}
        if str(approved.get("sha256") or "").lower() != str(asset_sha256 or "").lower():
            return [f"frame {key} approved asset SHA not bound by production ledger"]
        matched = None
        for attempt in reversed(row.get("attempts") or []):
            candidate = attempt.get("candidate") or {}
            if str(candidate.get("sha256") or "").lower() == str(asset_sha256 or "").lower():
                matched = attempt
                break
        if not isinstance(matched, dict):
            return [f"frame {key} no generation attempt matches approved asset SHA"]
        return verify_recorded_provenance(ep, key, (matched.get("request") or {}).get("frame_contract"))
    except Exception as exc:
        return [f"frame {key} frame-contract ledger verification failed: {exc}"]


def self_test() -> None:
    assert version_tuple("2.1.0") >= MIN_VERSION
    assert sha256_json({"b": 2, "a": 1}) == sha256_json({"a": 1, "b": 2})
    sample = {"frames": [{"frame": 2, "beat": "x"}, {"frame": 3, "beat": "y"}]}
    assert (_frame_from_json(sample, 2) or {}).get("beat") == "x"
    print("RESOLVED FRAME CONTRACT V2.1 PHASE4 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("compile-all"); p.add_argument("episode_dir")
    p = sub.add_parser("compile"); p.add_argument("episode_dir"); p.add_argument("--frame", type=int, required=True)
    p = sub.add_parser("verify"); p.add_argument("episode_dir"); p.add_argument("--frame", type=int)
    p = sub.add_parser("show"); p.add_argument("episode_dir"); p.add_argument("--frame", type=int, required=True); p.add_argument("--prompt", action="store_true")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    ep = resolve_ep(args.episode_dir)
    try:
        if args.cmd == "compile-all":
            idx = compile_all(ep)
            print(f"FRAME CONTRACT COMPILE PASS: {idx['frame_count']} frames index_sha256={idx['index_sha256']}")
            return 0
        if args.cmd == "compile":
            row = compile_frame(ep, args.frame, write_cache=True)
            print(json.dumps({"frame": row["frame"], "contract_sha256": row["contract_sha256"], "path": (CACHE_ROOT / f"{row['frame']}.json").as_posix()}, ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "show":
            row = compile_frame(ep, args.frame, write_cache=False)
            print(row["prompt_contract"] if args.prompt else json.dumps(row, ensure_ascii=False, indent=2))
            return 0
        errors = verify_frame(ep, args.frame) if args.frame else verify_all(ep)
        if errors:
            for error in errors:
                print("FAIL:", error)
            return 2
        print("RESOLVED FRAME CONTRACT VERIFIED")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("FRAME CONTRACT ERROR:", exc)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
