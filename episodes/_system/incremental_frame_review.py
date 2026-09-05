#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import frame_semantic_review as base
# STORY_OS_V22_VISUAL_NARRATIVE_CORE
from story_os_contract import story_os_version
import runtime_router
import runtime_provenance

ROOT = Path(__file__).resolve().parents[2]
STATE_REL = Path("meta/incremental-frame-review.json")
AUDIT_REL = Path("meta/incremental-frame-audit.json")
CANDIDATE_REL = Path("meta/.incremental-frame-review.candidate.json")
TARGET = (2, 0, 3, 4)
PATCH_LIMIT_RATIO = 0.25


def now() -> str:
    return base.now()


def read_json(path: Path) -> dict:
    return base.read_json(path)


def write_json(path: Path, data: dict) -> None:
    base.write_json(path, data)


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except ValueError:
        return (0,)


def review_required(ep: Path) -> bool:
    return base.review_required(ep)


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _manifest_caption_path(ep: Path) -> Path | None:
    manifest_path = ep / "meta/release-manifest.json"
    if manifest_path.is_file():
        try:
            manifest = read_json(manifest_path)
            artifacts = manifest.get("artifacts") or {}
            for key in ("captions", "subtitles", "caption_source", "subtitle_source"):
                raw = artifacts.get(key)
                if isinstance(raw, str) and raw.strip():
                    p = Path(raw)
                    p = p.resolve() if p.is_absolute() else (ROOT / p).resolve()
                    if p.is_file():
                        return p
        except Exception:
            pass
    for rel in (
        "text/subtitles.yaml", "text/subtitles.yml", "text/captions.yaml", "text/captions.yml",
        "text/subtitles.json", "text/captions.json", "subtitles.yaml", "captions.yaml",
    ):
        p = ep / rel
        if p.is_file():
            return p
    return None


def _extract_json_captions(data: object) -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(data, dict):
        for key in ("captions", "subtitles", "frames"):
            nested = data.get(key)
            if nested is not None:
                found = _extract_json_captions(nested)
                if found:
                    return found
        for k, v in data.items():
            ks = str(k).strip().zfill(2) if str(k).strip().isdigit() else ""
            if ks and len(ks) == 2:
                if isinstance(v, str):
                    out[ks] = v
                elif isinstance(v, dict):
                    text = v.get("text") or v.get("caption") or v.get("subtitle")
                    if isinstance(text, str):
                        out[ks] = text
    elif isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            raw = item.get("frame") or item.get("number") or item.get("id")
            if str(raw).isdigit():
                text = item.get("text") or item.get("caption") or item.get("subtitle")
                if isinstance(text, str):
                    out[str(int(raw)).zfill(2)] = text
    return out


def _extract_yaml_captions(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        m = re.match(r"^\s*['\"]?(\d{1,2})['\"]?\s*:\s*(.*?)\s*$", line)
        if m:
            key = str(int(m.group(1))).zfill(2)
            val = m.group(2).strip().strip("'\"")
            if val and val not in {"|", ">", "{}", "[]"}:
                out[key] = val
            current = key
            continue
        m = re.match(r"^\s*-?\s*frame\s*:\s*['\"]?(\d{1,2})['\"]?\s*$", line, re.I)
        if m:
            current = str(int(m.group(1))).zfill(2)
            continue
        if current:
            m = re.match(r"^\s*(?:text|caption|subtitle)\s*:\s*(.*?)\s*$", line, re.I)
            if m:
                out[current] = m.group(1).strip().strip("'\"")
                current = None
    return out


def caption_state(ep: Path, frames: list[dict]) -> dict:
    source = _manifest_caption_path(ep)
    frame_keys = [row["frame"] for row in frames]
    if source is None:
        empty = _sha_text("")
        return {
            "source_path": None,
            "source_sha256": empty,
            "mode": "none",
            "frame_sha256": {key: empty for key in frame_keys},
        }
    raw = source.read_text(encoding="utf-8", errors="replace")
    source_sha = _sha_text(raw)
    captions: dict[str, str] = {}
    if source.suffix.lower() == ".json":
        try:
            captions = _extract_json_captions(json.loads(raw))
        except Exception:
            captions = {}
    else:
        captions = _extract_yaml_captions(raw)
    if captions:
        hashes = {key: _sha_text(captions.get(key, "")) for key in frame_keys}
        mode = "per_frame"
    else:
        # Safe fallback: if parser cannot split the file, any caption edit invalidates every frame.
        hashes = {key: source_sha for key in frame_keys}
        mode = "whole_source_fallback"
    return {
        "source_path": _repo_rel(source),
        "source_sha256": source_sha,
        "mode": mode,
        "frame_sha256": hashes,
    }


def _review_path(ep: Path, frame: str) -> Path:
    return ep / base.REVIEW_DIR / f"{frame}.json"


def _review_data(ep: Path, frame: str) -> dict | None:
    p = _review_path(ep, frame)
    if not p.is_file():
        return None
    try:
        return read_json(p)
    except Exception:
        return None


def _context_match(data: dict, contexts: dict) -> bool:
    return all(str(data.get(k) or "").lower() == str(v).lower() for k, v in contexts.items())


def _scope_ok(data: dict) -> bool:
    p = data.get("critic_provenance") or {}
    return not runtime_provenance.validate_critic_provenance(p) and p.get("review_scope") in {
        "FULL_FRAME_SET", "INCREMENTAL_CONTEXT_SET"
    }


def _review_clean(ep: Path, data: dict | None, frame: dict, contexts: dict, caption_hash: str, version: str) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not isinstance(data, dict):
        return False, ["missing_review"]
    if str(data.get("story_os_version") or "") != version:
        reasons.append("review_version_changed")
    if str(data.get("asset_sha256") or "").lower() != frame["sha256"].lower():
        reasons.append("asset_sha_changed")
    if str(data.get("asset_path") or "") != frame["path_rel"]:
        reasons.append("asset_path_changed")
    if not _context_match(data, contexts):
        reasons.append("story_visual_context_changed")
    for field, expected in base.phase3_context_hashes(ep, frame["frame"]).items():
        if str(data.get(field) or "").lower() != str(expected).lower():
            reasons.append("phase3_frame_context_changed")
            break
    # STORY_OS_V2_6_0_PERFORMANCE_RUNTIME:
    # Caption changes are audited independently by caption_image_audit.py and MUST NOT dirty visual review.
    if not _scope_ok(data):
        reasons.append("review_scope_invalid")
    if data.get("decision") != "pass" or data.get("issue_codes") not in ([], None):
        reasons.append("review_not_pass")
    checks = data.get("checks") or {}
    for name in base.checks_for_version(version):
        if checks.get(name) is not True:
            reasons.append(f"check_failed:{name}")
    return not reasons, reasons


def _context_frames(keys: list[str], dirty: list[str]) -> list[str]:
    nums = sorted(int(k) for k in keys)
    allowed = set(nums)
    total = max(nums) if nums else 0
    chosen: set[int] = set()
    for raw in dirty:
        n = int(raw)
        radius = 2 if n >= max(1, total - 2) else 1
        for i in range(n - radius, n + radius + 1):
            if i in allowed:
                chosen.add(i)
    return [f"{n:02d}" for n in sorted(chosen)]


def build_plan(ep: Path) -> dict:
    if not review_required(ep):
        return {"action": "NOT_REQUIRED", "dirty_frames": [], "context_frames": [], "reasons": ["legacy_contract"]}
    frames = base.frame_records(ep, require_files=True)
    contexts = base.context_hashes(ep)
    captions = caption_state(ep, frames)
    version = base.episode_contract_version(ep)
    dirty: list[str] = []
    reasons: dict[str, list[str]] = {}
    context_change = False
    for frame in frames:
        data = _review_data(ep, frame["frame"])
        clean, why = _review_clean(ep, data, frame, contexts, captions["frame_sha256"][frame["frame"]], version)
        if not clean:
            dirty.append(frame["frame"])
            reasons[frame["frame"]] = why
            if "story_visual_context_changed" in why or "review_version_changed" in why:
                context_change = True
    if not dirty:
        return {
            "action": "NOOP",
            "dirty_frames": [],
            "context_frames": [],
            "reasons": {},
            "caption_mode": captions["mode"],
        }
    ratio = len(dirty) / max(1, len(frames))
    action = "FULL" if context_change or ratio > PATCH_LIMIT_RATIO else "PATCH"
    return {
        "action": action,
        "dirty_frames": dirty,
        "context_frames": [row["frame"] for row in frames] if action == "FULL" else _context_frames([r["frame"] for r in frames], dirty),
        "reasons": reasons,
        "dirty_ratio": round(ratio, 4),
        "caption_mode": captions["mode"],
    }


def _resolve_codex(raw: str | None) -> Path:
    return base.resolve_codex(raw)


def _command_prefix(codex: Path) -> list[str]:
    return base.command_prefix(codex)


def _prompt(ep: Path, selected: list[dict], dirty: list[str], candidate: Path, attempt: int, captions: dict) -> str:
    story, storyboard = base.episode_files(ep)
    rel_ep = ep.relative_to(ROOT).as_posix()
    mapping = "\n".join(f"- context frame {r['frame']}: {r['path_rel']}" for r in selected)
    dirty_text = ", ".join(dirty)
    caption_source = captions.get("source_path") or "<no caption source>"
    return f"""You are an adversarial Story OS incremental Production Frame Semantic Critic in a FRESH isolated session.
Do NOT generate or edit images. Do NOT trust previous PASS labels.
Review only the supplied CONTEXT SET for {rel_ep}. The true dirty roots are: {dirty_text}.
Neighbor frames are included only so continuity and information gain can be judged correctly.

Read:
- {story.relative_to(ROOT).as_posix()}
- {storyboard.relative_to(ROOT).as_posix()}
- {(ep / 'meta/story-gates.json').relative_to(ROOT).as_posix()}
- {caption_source}
- standards/制作规范_正式版.md
- standards/生产帧语义强制规范_V1.0.md

Attached mapping:
{mapping}

Attempt {attempt}. Judge ACTUAL pixels. Every supplied frame must pass all checks:
{', '.join(base.checks_for_version(base.episode_contract_version(ep)))}
Hard failures include wrong scene/beat/prop/person/wardrobe, illegal POV, ghost camera, broken space/time continuity, unreadable anomaly, caption inventing missing evidence, missing actual information gain, narrative redundancy, repeated shot grammar, unmotivated camera defects, impossible screen/UI physics, or broken visual memory.
Episode contract version: {base.episode_contract_version(ep)}. V2.2-only Visual Narrative checks and issue codes apply ONLY when version >= 2.2.0; legacy episodes must not fail on V2.2-only criteria.
Return one row for EVERY supplied context frame, not only dirty roots.
Use issue codes only from: {', '.join(sorted(base.ISSUE_CODES))}

Write ONLY JSON to {candidate.relative_to(ROOT).as_posix()} with shape:
{{"frames":[{{"frame":"01","checks":{{"scene_storyboard_fidelity":true,"story_beat_fidelity":true,"key_prop_fidelity":true,"character_identity":true,"wardrobe_continuity":true,"pov_photographer_legality":true,"spatial_continuity":true,"temporal_continuity":true,"anomaly_readability":true,"caption_image_support":true,"actual_information_gain":true,"environment_physics_fidelity":true,"anomaly_escalation_fidelity":true,"scale_reference_fidelity":true,"camera_authorship_physical":true,"moment_capture_credibility":true,"narrative_evidence_gain":true,"shot_grammar_diversity":true,"camera_defect_physics":true,"screen_content_physics":true,"visual_memory_continuity":true}},"issue_codes":[],"notes":"pixel-level evidence","decision":"pass"}}],"issue_codes":[],"summary":{{"passed":true,"notes":"incremental context judgment"}}}}
If any supplied frame fails, summary.passed=false.
"""


def _decorate_full(ep: Path) -> None:
    frames = base.frame_records(ep, require_files=True)
    captions = caption_state(ep, frames)
    for frame in frames:
        p = _review_path(ep, frame["frame"])
        data = read_json(p)
        data["caption_sha256"] = captions["frame_sha256"][frame["frame"]]
        write_json(p, data)
    summary_path = ep / base.SUMMARY_REL
    summary = read_json(summary_path)
    summary["caption_source"] = captions["source_path"]
    summary["caption_source_sha256"] = captions["source_sha256"]
    summary["caption_mode"] = captions["mode"]
    summary["caption_frame_sha256"] = captions["frame_sha256"]
    summary["incremental_contract"] = {"version": 1, "mode": "full_baseline"}
    write_json(summary_path, summary)


def _run_patch(ep: Path, plan: dict, *, attempt: int, codex_raw: str | None, timeout: int) -> int:
    all_frames = base.frame_records(ep, require_files=True)
    binding_errors = base.phase4_binding_errors(ep, all_frames)
    if binding_errors:
        print("INCREMENTAL FRAME REVIEW FAIL: stale/missing generation Frame Contract")
        for error in binding_errors:
            print("FAIL:", error)
        return 2
    by_key = {r["frame"]: r for r in all_frames}
    selected = [by_key[k] for k in plan["context_frames"]]
    contexts = base.context_hashes(ep)
    captions = caption_state(ep, all_frames)

    phashes = base.perceptual_rows(all_frames)
    duplicates = base.duplicate_pairs(phashes)
    if duplicates:
        write_json(ep / AUDIT_REL, {"checked_at": now(), "action": "PATCH", "errors": ["NEAR_DUPLICATE_ACTUAL_FRAMES"], "near_duplicate_pairs": duplicates, "summary": {"passed": False}})
        print("INCREMENTAL FRAME REVIEW FAIL: deterministic near-duplicate check")
        return 2

    candidate = ep / CANDIDATE_REL
    candidate.unlink(missing_ok=True)
    before = {r["frame"]: base.sha256_file(r["path"]) for r in all_frames}
    codex = _resolve_codex(codex_raw)
    cmd = _command_prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="medium"',
        "-s", "workspace-write", "-C", str(ROOT), "--json",
    ]
    for row in selected:
        cmd += ["-i", str(row["path"])]
    cmd += ["-"]
    log = ep / "meta" / f"incremental-frame-critic-attempt-{attempt}.jsonl"
    with log.open("w", encoding="utf-8", newline="\n") as handle:
        completed = subprocess.run(cmd, input=_prompt(ep, selected, plan["dirty_frames"], candidate, attempt, captions), text=True, encoding="utf-8", stdout=handle, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if completed.returncode != 0 or not candidate.is_file():
        raise RuntimeError(f"incremental critic failed rc={completed.returncode}; log={log}")

    current = base.frame_records(ep, require_files=True)
    if {r["frame"]: base.sha256_file(r["path"]) for r in current} != before:
        raise RuntimeError("incremental critic modified approved image assets")
    data = read_json(candidate)
    candidate_errors = base.validate_candidate_rows(data.get("frames"), selected, version=base.episode_contract_version(ep))
    global_codes = data.get("issue_codes")
    if not isinstance(global_codes, list):
        candidate_errors.append("global issue_codes must be list")
        global_codes = []
    elif global_codes:
        candidate_errors.append(f"global issue_codes must be empty for PASS: {global_codes}")
    if (data.get("summary") or {}).get("passed") is not True:
        candidate_errors.append("critic summary.passed must be true")

    rows_by_frame = {str(r.get("frame") or "").zfill(2): r for r in (data.get("frames") or []) if isinstance(r, dict)}
    version = base.episode_contract_version(ep)
    provenance = {
        "runtime": "CODEX_ISOLATED",
        "isolated_session": True,
        "review_scope": "INCREMENTAL_CONTEXT_SET",
        "attempt": attempt,
        "reviewed_at": now(),
        "log": _repo_rel(log),
        "dirty_roots": plan["dirty_frames"],
        "context_frames": plan["context_frames"],
    }
    for frame in selected:
        source = rows_by_frame.get(frame["frame"], {})
        bound = {
            "schema_version": base.SCHEMA_VERSION,
            "story_os_version": version,
            "frame": frame["frame"],
            "asset_path": frame["path_rel"],
            "asset_sha256": frame["sha256"],
            **contexts,
            **base.phase3_context_hashes(ep, frame["frame"]),
            "caption_sha256": captions["frame_sha256"][frame["frame"]],
            "critic_provenance": provenance,
            "checks": source.get("checks") or {},
            "issue_codes": source.get("issue_codes") if isinstance(source.get("issue_codes"), list) else ["FRAME_SCENE_MISMATCH"],
            "notes": source.get("notes") or "",
            "decision": source.get("decision") or "fail",
        }
        write_json(_review_path(ep, frame["frame"]), bound)

    summary = {
        "schema_version": base.SCHEMA_VERSION,
        "story_os_version": version,
        **contexts,
        "critic_provenance": {
            **provenance,
            "review_scope": "BASELINE_PLUS_PATCHES",
        },
        "frames": [{"frame": r["frame"], "asset_sha256": r["sha256"]} for r in current],
        "caption_source": captions["source_path"],
        "caption_source_sha256": captions["source_sha256"],
        "caption_mode": captions["mode"],
        "caption_frame_sha256": captions["frame_sha256"],
        "perceptual_hashes": phashes,
        "near_duplicate_pairs": [],
        "issue_codes": global_codes,
        "critic_summary": data.get("summary") or {},
        "incremental_contract": {
            "version": 1,
            "mode": "baseline_plus_patches",
            "dirty_roots": plan["dirty_frames"],
            "context_frames": plan["context_frames"],
        },
        "summary": {"passed": not candidate_errors},
    }
    write_json(ep / base.SUMMARY_REL, summary)
    candidate.unlink(missing_ok=True)

    errors = candidate_errors + [e for e in verify_episode(ep, metadata_only=False, write_audit=True) if e not in candidate_errors]
    if errors:
        print("INCREMENTAL FRAME REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        return 2
    print(f"INCREMENTAL FRAME REVIEW PASS: dirty={plan['dirty_frames']} context={plan['context_frames']}")
    return 0


def verify_episode(ep: Path, *, metadata_only: bool = False, write_audit: bool = False) -> list[str]:
    errors = list(base.verify_episode(ep, metadata_only=metadata_only, write_audit=False))
    if not review_required(ep):
        return errors
    version = base.episode_contract_version(ep)
    if version_tuple(version) < TARGET:
        if write_audit:
            write_json(ep / AUDIT_REL, {"checked_at": now(), "legacy_contract": version, "errors": errors, "summary": {"passed": not errors}})
        return errors
    try:
        frames = base.frame_records(ep, require_files=not metadata_only)
        captions = caption_state(ep, frames)
        for frame in frames:
            data = _review_data(ep, frame["frame"])
            if not isinstance(data, dict):
                errors.append(f"missing incremental-bound frame review: {frame['frame']}")
                continue
            expected = captions["frame_sha256"][frame["frame"]]
            if str(data.get("caption_sha256") or "").lower() != expected.lower():
                errors.append(f"frame {frame['frame']} caption_sha256 stale")
        summary_path = ep / base.SUMMARY_REL
        if summary_path.is_file():
            summary = read_json(summary_path)
            if summary.get("caption_source_sha256") != captions["source_sha256"]:
                errors.append("frame semantic summary caption source SHA stale")
            if summary.get("caption_frame_sha256") != captions["frame_sha256"]:
                errors.append("frame semantic summary caption frame hashes stale")
            if not isinstance(summary.get("incremental_contract"), dict):
                errors.append("frame semantic summary missing incremental_contract")
    except Exception as exc:
        errors.append(str(exc))
    if write_audit:
        write_json(ep / AUDIT_REL, {
            "schema_version": 1,
            "story_os_version": version,
            "checked_at": now(),
            "metadata_only": metadata_only,
            "errors": errors,
            "summary": {"passed": not errors},
        })
    return errors


def run_review(ep: Path, *, attempt: int, codex_raw: str | None, timeout: int) -> int:
    if attempt not in {1, 2}:
        raise RuntimeError("attempt must be 1 or 2")
    plan = build_plan(ep)
    write_json(ep / STATE_REL, {"schema_version": 1, "story_os_version": story_os_version(), "planned_at": now(), **plan})
    action = plan["action"]
    if action == "NOT_REQUIRED":
        print("INCREMENTAL FRAME REVIEW SKIP: legacy contract")
        return 0
    if action == "NOOP":
        errors = verify_episode(ep, metadata_only=False, write_audit=True)
        if errors:
            for e in errors:
                print("FAIL:", e)
            return 2
        print("INCREMENTAL FRAME REVIEW REUSE: 0 critic calls")
        return 0
    active_runtime, _ = runtime_router.detect()
    if action == "FULL" or (action == "PATCH" and active_runtime in {"WORK", "WEB"} and not codex_raw):
        reason = "product runtime avoids local Codex patch critic" if action == "PATCH" else "dirty/context threshold"
        print(f"INCREMENTAL FRAME REVIEW ESCALATE FULL: dirty={plan['dirty_frames']} reason={reason}")
        rc = base.run_critic(ep, attempt=attempt, codex_raw=codex_raw, timeout=timeout)
        if rc == 0:
            _decorate_full(ep)
            errors = verify_episode(ep, metadata_only=False, write_audit=True)
            if errors:
                for e in errors:
                    print("FAIL:", e)
                return 2
        return rc
    return _run_patch(ep, plan, attempt=attempt, codex_raw=codex_raw, timeout=timeout)


def self_test() -> None:
    assert _extract_yaml_captions('captions:\n  1: "a"\n  02: b\n') == {"01": "a", "02": "b"}
    assert _extract_json_captions({"captions": {"1": "x", "02": "y"}}) == {"01": "x", "02": "y"}
    keys = [f"{i:02d}" for i in range(1, 21)]
    assert _context_frames(keys, ["02"]) == ["01", "02", "03"]
    assert _context_frames(keys, ["19"]) == ["17", "18", "19", "20"]
    print("INCREMENTAL FRAME REVIEW SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description="Story OS V2.0.3.4 incremental actual-frame semantic review")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("episode_dir")
    p = sub.add_parser("review"); p.add_argument("episode_dir"); p.add_argument("--attempt", type=int, default=1); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=1800)
    p = sub.add_parser("verify"); p.add_argument("episode_dir"); p.add_argument("--metadata-only", action="store_true")
    p = sub.add_parser("audit"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    if args.cmd == "plan":
        print(json.dumps(build_plan(ep), ensure_ascii=False, indent=2)); return 0
    if args.cmd == "review":
        try:
            return run_review(ep, attempt=args.attempt, codex_raw=args.codex, timeout=args.timeout)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            print("INCREMENTAL FRAME REVIEW ERROR:", exc); return 3
    errors = verify_episode(ep, metadata_only=(args.cmd == "verify" and args.metadata_only), write_audit=(args.cmd == "audit"))
    if errors:
        for e in errors: print("FAIL:", e)
        return 2
    print("INCREMENTAL FRAME REVIEW VERIFY PASS" if args.cmd == "verify" else "INCREMENTAL FRAME AUDIT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
