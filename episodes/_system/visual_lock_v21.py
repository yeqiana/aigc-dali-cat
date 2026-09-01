#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.1 Phase 5 unified four-admission Visual Lock.

V2.1 roles:
1 ordinary_baseline
2 worst_capture_condition
3 first_major_anomaly
4 high_impact_admission

The review judges actual pixels and binds each image to the current Resolved Frame Contract.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from story_os_contract import story_os_version
from visual_profile import compile_prompt_contract
import environment_contract
import frame_contract
import character_visual_contract
import visual_lock_baseline_gate
import critic_runtime_v211  # STORY_OS_V211_PERF_RECOVERY

ROOT = Path(__file__).resolve().parents[2]
GATES_REL = Path("meta/story-gates.json")
REVIEW_REL = Path("meta/visual-profile-review.json")
PLAN_REL = Path("meta/visual-lock-plan.json")
CANDIDATE_REL = Path("meta/.visual-lock-review.candidate.json")
MIN_VERSION = (2, 1, 0)
ROLES = (
    "ordinary_baseline",
    "worst_capture_condition",
    "first_major_anomaly",
    "high_impact_admission",
)
CHECKS = (
    "visual_profile_match",
    "reality_first",
    "ordinary_life_density",
    "available_light",
    "unposed_capture",
    "not_cinematic",
    "causal_imperfection",
    "environment_physics_fidelity",
    "capture_credibility",
    "anomaly_scale_delivery",
    "scale_reference_fidelity",
)


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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except Exception:
        return (0,)


def episode_version(ep: Path) -> str:
    versions = []
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
    return max(versions, key=lambda x: x[0])[1] if versions else ""


def required(ep: Path) -> bool:
    if version_tuple(episode_version(ep)) < MIN_VERSION:
        return False
    p = ep / GATES_REL
    if not p.is_file():
        return False
    try:
        calibration = ((read_json(p).get("visual") or {}).get("calibration") or {})
        return calibration.get("policy") == "four_admission_v21"
    except Exception:
        return False


def resolve_ep(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    try:
        ep.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit("episode must be inside repository")
    return ep


def repo_file(raw: object) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("calibration asset_path missing")
    p = Path(raw.strip())
    p = p.resolve() if p.is_absolute() else (ROOT / p).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"calibration path escapes repository: {raw}") from exc
    if not p.is_file():
        raise ValueError(f"calibration image missing: {raw}")
    return p


def repo_rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _severity(env: dict) -> int:
    score = 0
    condition = str(env.get("condition") or "").lower()
    visibility = str(env.get("visibility") or "").lower()
    wind = str(env.get("wind") or "").lower()
    precipitation = str(env.get("precipitation") or "").lower()
    difficult = ("storm","rain","snow","fog","mist","dust","sand","night","dark","low","poor","strong","heavy","暴","雨","雪","雾","沙","夜","暗")
    score += sum(2 for token in difficult if token in condition)
    score += sum(2 for token in difficult if token in visibility)
    score += sum(1 for token in difficult if token in wind)
    score += sum(2 for token in difficult if token in precipitation)
    score += min(5, len(env.get("physical_cues") or []))
    score += min(3, len(env.get("conditional_effects") or []))
    return score


def _rows(ep: Path) -> list[dict]:
    total = frame_contract.frame_count(ep)
    rows = []
    for n in range(1, total + 1):
        resolved = environment_contract.resolve_frame(ep, n)
        d = resolved.get("directive") or {}
        rows.append({
            "frame": n,
            "mode": str(d.get("frame_mode") or ""),
            "role": str(d.get("narrative_role") or ""),
            "impact": int(d.get("impact_level") or 0),
            "scale_reference": str(d.get("scale_reference") or ""),
            "environment_severity": _severity(resolved.get("environment") or {}),
            "contract_sha256": frame_contract.compile_frame(ep, n, write_cache=True)["contract_sha256"],
        })
    return rows

def _opening_social_baseline(ep: Path, rows: list[dict]) -> dict | None:
    p=ep/"meta/opening-social-anchor.json"
    if not p.is_file():return None
    try:d=read_json(p)
    except Exception:return None
    if d.get("applicable") is not True:return None
    preferred=[]
    for x in d.get("opening_frames") or []:
        if not isinstance(x,dict) or x.get("selfie") is not True:continue
        try:n=int(x.get("frame"))
        except Exception:continue
        if n not in {1,2}:continue
        if int(x.get("people_visible") or 0)<2:continue
        if x.get("relationship_anchor") is not True:continue
        preferred.append(n)
    by_frame={int(r["frame"]):r for r in rows}
    for n in preferred:
        row=by_frame.get(n)
        if row and row.get("mode")=="normal_record" and int(row.get("impact") or 0)<=1:return row
    return None

def _pixel_master_expected(assets: list[dict]) -> dict | None:
    row=next((x for x in assets if x.get("role")=="ordinary_baseline"),None)
    if not row:return None
    return {"frame":f"{int(row['frame']):02d}","asset_path":row["asset_path"],"sha256":row["sha256"],"frame_contract_sha256":row["frame_contract_sha256"]}


def choose_plan(ep: Path) -> dict:
    if not required(ep):
        raise ValueError("Visual Lock V2.1 is only required for V2.1+ episodes")
    env_errors = environment_contract.verify(ep)
    if env_errors:
        raise ValueError("Environment Contract must PASS first: " + "; ".join(env_errors[:8]))
    fc_errors = frame_contract.verify_all(ep)
    if fc_errors:
        raise ValueError("Resolved Frame Contract must PASS first: " + "; ".join(fc_errors[:8]))
    rows = _rows(ep)
    used: set[int] = set()

    def take(candidates: list[dict]) -> dict:
        for row in candidates:
            if row["frame"] not in used:
                used.add(row["frame"])
                return row
        raise ValueError("cannot select four distinct Visual Lock admission frames")

    preferred_baseline = _opening_social_baseline(ep, rows)
    baseline = take([preferred_baseline] if preferred_baseline else sorted(
        [r for r in rows if r["mode"] == "normal_record" and r["impact"] <= 1] or rows,
        key=lambda r: (r["impact"], r["frame"])
    ))
    baseline_selection = "opening_social_anchor" if preferred_baseline else "ordinary_fallback"
    worst = take(sorted(
        [r for r in rows if r["frame"] != baseline["frame"]],
        key=lambda r: (-r["environment_severity"], -r["impact"], r["frame"])
    ))
    first_anomaly = take(sorted(
        [r for r in rows if r["mode"] == "anomaly_reveal" or r["impact"] >= 2] or rows,
        key=lambda r: (r["frame"], -r["impact"])
    ))
    high = take(sorted(
        [r for r in rows if r["mode"] in {"climax_impact", "anomaly_amplified"} or r["impact"] >= 3] or rows,
        key=lambda r: (-r["impact"], r["mode"] != "climax_impact", -r["frame"])
    ))

    plan_rows = [
        {"id": "V-B", "role": ROLES[0], **baseline, "depends_on": []},
        {"id": "V-W", "role": ROLES[1], **worst, "depends_on": [baseline["frame"]]},
        {"id": "V-A", "role": ROLES[2], **first_anomaly, "depends_on": [baseline["frame"]]},
        {"id": "V-H", "role": ROLES[3], **high, "depends_on": [baseline["frame"]]},
    ]
    return {
        "schema_version": 1,
        "story_os_version": episode_version(ep),
        "generated_at": now(),
        "policy": {
            "baseline_first": True,
            "remaining_three_parallelizable": True,
            "calibration_count": 4,
            "baseline_selection": baseline_selection,
            "baseline_frame": baseline["frame"],
            "opening_social_anchor_machine_priority": True,
        },
        "items": plan_rows,
    }


def prepare(ep: Path) -> dict:
    plan = choose_plan(ep)
    write_json(ep / PLAN_REL, plan)
    gates_path = ep / GATES_REL
    g = read_json(gates_path)
    visual = g.setdefault("visual", {})
    calibration = visual.setdefault("calibration", {})
    calibration["schema_version"] = 2
    calibration["policy"] = "four_admission_v21"
    calibration["items"] = [
        {
            "id": row["id"],
            "role": row["role"],
            "frame": row["frame"],
            "asset_path": None,
            "sha256": None,
            "decision": "pending",
            "frame_contract_sha256": row["contract_sha256"],
            "note": "",
        }
        for row in plan["items"]
    ]
    write_json(gates_path, g)
    return plan


def _find_attempt_binding(ep: Path, frame: int, asset_sha: str) -> list[str]:
    if not frame_contract.required(ep):
        return []
    ledger_path = ep / "meta/production-ledger.json"
    if not ledger_path.is_file():
        return [f"frame {frame:02d} production ledger missing"]
    ledger = read_json(ledger_path)
    row = (ledger.get("frames") or {}).get(f"{frame:02d}")
    if not isinstance(row, dict):
        return [f"frame {frame:02d} production ledger row missing"]
    for attempt in reversed(row.get("attempts") or []):
        candidate = attempt.get("candidate") or {}
        if str(candidate.get("sha256") or "").lower() == asset_sha.lower():
            return frame_contract.verify_recorded_provenance(
                ep, frame, (attempt.get("request") or {}).get("frame_contract")
            )
    return [f"frame {frame:02d} calibration image has no matching generation attempt"]


def calibration_assets(ep: Path) -> list[dict]:
    g = read_json(ep / GATES_REL)
    calibration = ((g.get("visual") or {}).get("calibration") or {})
    items = calibration.get("items")
    if not isinstance(items, list) or len(items) != 4:
        raise ValueError("V2.1 Visual Lock requires exactly 4 calibration items; run visual_lock_v21.py prepare")
    by_role = {}
    out = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("calibration item must be object")
        role = str(item.get("role") or "")
        if role not in ROLES:
            raise ValueError(f"unexpected Visual Lock role: {role}")
        if role in by_role:
            raise ValueError(f"duplicate Visual Lock role: {role}")
        frame = int(item.get("frame"))
        p = repo_file(item.get("asset_path"))
        asset_sha = sha256_file(p)
        current = frame_contract.compile_frame(ep, frame, write_cache=True)
        recorded_fc = str(item.get("frame_contract_sha256") or "")
        if recorded_fc and recorded_fc != current["contract_sha256"]:
            raise ValueError(f"{role} frame contract stale")
        binding_errors = _find_attempt_binding(ep, frame, asset_sha)
        if binding_errors:
            raise ValueError("; ".join(binding_errors))
        row = {
            "id": str(item.get("id") or role),
            "role": role,
            "frame": frame,
            "path": p,
            "asset_path": repo_rel(p),
            "sha256": asset_sha,
            "frame_contract_sha256": current["contract_sha256"],
            "impact_level": current["hash_material"]["frame_directive"].get("impact_level"),
            "frame_mode": current["hash_material"]["frame_directive"].get("frame_mode"),
            "scale_reference": current["hash_material"]["frame_directive"].get("scale_reference"),
        }
        by_role[role] = row
        out.append(row)
    if set(by_role) != set(ROLES):
        raise ValueError("Visual Lock role set incomplete")
    return [by_role[x] for x in ROLES]


def bind_from_queue(ep: Path) -> dict:
    qpath = ep / "meta/production-queue.json"
    if not qpath.is_file():
        raise ValueError("meta/production-queue.json missing")
    q = read_json(qpath)
    ledger_path = ep / "meta/production-ledger.json"
    ledger = read_json(ledger_path) if ledger_path.is_file() else {"frames": {}}
    generated = {}
    for item in q.get("items") or []:
        if item.get("scope") not in {"visual_lock", "repair"}:
            continue
        key = f"{int(item['frame']):02d}"
        if item.get("status") == "generated":
            generated[key] = item
            continue
        # A Fast Scout result is triage only. It may enter Visual Lock solely
        # after a direct-user exception acceptance of the identical candidate.
        if item.get("status") != "scout_repair":
            continue
        frame = (ledger.get("frames") or {}).get(key) or {}
        candidate = frame.get("current_candidate") or {}
        acceptance = (frame.get("user_exception_acceptances") or [])[-1:]
        if (
            frame.get("status") == "PASSED"
            and candidate.get("sha256") == ((item.get("lineage") or {}).get("sha256"))
            and acceptance
            and acceptance[0].get("approval_basis") == "direct_user_review_exception_acceptance"
            and acceptance[0].get("candidate_sha256") == candidate.get("sha256")
        ):
            generated[key] = item
    gates_path = ep / GATES_REL
    g = read_json(gates_path)
    items = (((g.get("visual") or {}).get("calibration") or {}).get("items") or [])
    if len(items) != 4:
        raise ValueError("Visual Lock plan missing; run prepare first")
    for item in items:
        key = f"{int(item['frame']):02d}"
        qrow = generated.get(key)
        if not qrow:
            raise ValueError(f"Visual Lock frame {key} not generated by scheduler")
        output = repo_file(qrow.get("output_path"))
        item["asset_path"] = repo_rel(output)
        item["sha256"] = sha256_file(output)
        item["decision"] = "candidate"
        item["frame_contract_sha256"] = frame_contract.compile_frame(ep, int(key), write_cache=True)["contract_sha256"]
    write_json(gates_path, g)
    return {"bound": [f"{int(x['frame']):02d}" for x in items]}


def validate_payload(data: dict, *, contract: dict, assets: list[dict], version: str) -> list[str]:
    errors = []
    if data.get("schema_version") != 2:
        errors.append("schema_version must be 2")
    if data.get("story_os_version") != version:
        errors.append("story_os_version mismatch")
    if data.get("profile_id") != contract["profile_id"]:
        errors.append("profile_id mismatch")
    if str(data.get("profile_sha256") or "").lower() != contract["profile_sha256"].lower():
        errors.append("profile_sha256 mismatch")
    prov = data.get("critic_provenance") or {}
    if prov.get("runtime") != "CODEX_ISOLATED" or prov.get("isolated_session") is not True:
        errors.append("Visual Lock critic must be fresh CODEX_ISOLATED")
    if prov.get("attempt") not in {1, 2}:
        errors.append("critic attempt must be 1 or 2")

    expected = {row["id"]: row for row in assets}
    rows = data.get("calibration")
    if not isinstance(rows, list) or len(rows) != 4:
        errors.append("Visual Lock review must contain exactly 4 rows")
        rows = []
    seen = set()
    for row in rows:
        rid = str(row.get("id") or "")
        seen.add(rid)
        exp = expected.get(rid)
        if exp is None:
            errors.append(f"unexpected calibration id: {rid}")
            continue
        if str(row.get("sha256") or "").lower() != exp["sha256"].lower():
            errors.append(f"{rid} sha mismatch")
        if str(row.get("frame_contract_sha256") or "").lower() != exp["frame_contract_sha256"].lower():
            errors.append(f"{rid} frame_contract_sha mismatch")
        checks = row.get("checks") or {}
        for key in CHECKS:
            if checks.get(key) is not True:
                errors.append(f"{rid}.checks.{key} must be true")
        if row.get("issues") not in ([], None):
            errors.append(f"{rid}.issues must be empty for PASS")
    if seen != set(expected):
        errors.append("review ids do not match 4 Visual Lock assets")
    if data.get("issue_codes") not in ([], None):
        errors.append("issue_codes must be empty for PASS")
    if (data.get("summary") or {}).get("passed") is not True:
        errors.append("summary.passed must be true")
    return errors


def verify(ep: Path) -> list[str]:
    if not required(ep):
        return []
    path = ep / REVIEW_REL
    if not path.is_file():
        return ["meta/visual-profile-review.json missing"]
    try:
        contract = compile_prompt_contract(ep)
        assets = calibration_assets(ep)
        data = read_json(path)
        errors = validate_payload(data, contract=contract, assets=assets, version=episode_version(ep))
        if not errors:
            errors.extend("BASELINE_GATE:"+x for x in visual_lock_baseline_gate.validate_final_requirement(ep))
        if not errors and character_visual_contract.pixel_master_required(ep):
            expected=_pixel_master_expected(assets)
            errors.extend(character_visual_contract.validate_pixel_master(ep,expected))
        return errors
    except Exception as exc:
        return [str(exc)]


def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value:
        raise RuntimeError("Codex CLI not found")
    p = Path(value).expanduser().resolve()
    if not p.exists():
        raise RuntimeError(f"Codex CLI not found: {p}")
    return p


def prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]


def critic_prompt(ep: Path, contract: dict, assets: list[dict], candidate: Path, attempt: int) -> str:
    rel_out = candidate.relative_to(ROOT).as_posix()
    listed = "\n".join(
        f"- id={r['id']} role={r['role']} frame={r['frame']:02d} "
        f"mode={r['frame_mode']} impact={r['impact_level']} scale_reference={r['scale_reference']!r} "
        f"frame_contract_sha={r['frame_contract_sha256']}"
        for r in assets
    )
    return f"""You are the adversarial Story OS V2.1 Visual Lock Critic in a fresh isolated session.
Review exactly FOUR attached calibration/admission images in the listed order. Do not generate or edit images.

Resolved visual profile:
<visual_contract>
{contract['text']}
</visual_contract>

Rows:
{listed}

This gate deliberately allows huge/impossible anomalies. DO NOT fail an image merely because the supernatural event is large, impossible, cosmic, surreal or frightening.
Reality-first constrains HOW the event looks captured: optics, available light, atmosphere, occlusion, scale cues, device limitations, photographer behavior, ordinary-life context and causal imperfection.

Role expectations:
- ordinary_baseline: ordinary world must look convincingly real before anomaly spectacle.
- worst_capture_condition: difficult weather/light/capture state must obey physical causes; no blanket weather filter.
- first_major_anomaly: anomaly must be clearly readable yet embedded into believable reality rather than promo concept art.
- high_impact_admission: impact 3-4 must visibly deliver its promised abnormal scale/consequence, include readable real-world scale reference, and STILL look like an accidental/working record rather than a cinematic poster.

For every image judge ALL checks:
visual_profile_match, reality_first, ordinary_life_density, available_light, unposed_capture, not_cinematic, causal_imperfection,
environment_physics_fidelity, capture_credibility, anomaly_scale_delivery, scale_reference_fidelity.

Interpret anomaly_scale_delivery=true on ordinary/no-anomaly frames as "the frame correctly avoids unplanned spectacle and matches its locked impact level."
Interpret scale_reference_fidelity=true on low-impact frames as "no false/contradictory scale cue"; for high impact it MUST be visibly useful.

Write ONLY valid JSON to {rel_out}:
{{
  "calibration": [
    {{
      "id": "V-B",
      "checks": {{
        "visual_profile_match": true,
        "reality_first": true,
        "ordinary_life_density": true,
        "available_light": true,
        "unposed_capture": true,
        "not_cinematic": true,
        "causal_imperfection": true,
        "environment_physics_fidelity": true,
        "capture_credibility": true,
        "anomaly_scale_delivery": true,
        "scale_reference_fidelity": true
      }},
      "issues": [],
      "notes": "specific actual-pixel evidence"
    }}
  ],
  "issue_codes": [],
  "summary": {{"passed": true}}
}}
PASS only if all 11 checks are true on all 4 images. This is attempt {attempt}.
"""


def _mark_decisions(ep: Path, passed: bool) -> None:
    gates_path = ep / GATES_REL
    g = read_json(gates_path)
    items = (((g.get("visual") or {}).get("calibration") or {}).get("items") or [])
    for item in items:
        if isinstance(item, dict):
            item["decision"] = "passed" if passed else "failed"
    reviews = g.setdefault("reviews", {})
    reviews["visual_admission"] = "passed" if passed else "failed"
    write_json(gates_path, g)


def _record_failed_calibration_frames(ep: Path, data: dict) -> None:
    # A critic that could not access its image inputs has no content finding to
    # propagate into the production ledger.
    if "INPUT_IMAGES_UNAVAILABLE" in (data.get("issue_codes") or []):
        return
    for row in data.get("calibration") or []:
        checks = row.get("checks") or {}
        failed = row.get("issues") not in ([], None) or any(checks.get(k) is not True for k in CHECKS)
        if not failed:
            continue
        try:
            frame = int(row.get("frame"))
        except Exception:
            continue
        cp = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "production_ledger.py"),
             "review", str(ep), "--frame", f"{frame:02d}", "--decision", "repair",
             "--notes", "Phase5 Visual Lock critic failed actual-pixel admission"],
            cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace"
        )
        # Do not hide a state mismatch; leave it visible in the Visual Lock review notes.
        if cp.returncode != 0:
            row.setdefault("ledger_review_warnings", []).append(cp.stdout[-1200:])


def run_critic(ep: Path, *, attempt: int, codex_raw: str | None, timeout: int) -> int:
    if attempt not in {1, 2}:
        raise RuntimeError("attempt must be 1 or 2")
    baseline_errors=visual_lock_baseline_gate.validate_review(ep)
    if baseline_errors:raise RuntimeError("ordinary_baseline separate review must PASS before final Visual Lock critic: "+"; ".join(baseline_errors[:8]))
    contract = compile_prompt_contract(ep)
    assets = calibration_assets(ep)
    candidate = ep / CANDIDATE_REL
    candidate.unlink(missing_ok=True)
    before = {r["id"]: r["sha256"] for r in assets}
    codex = resolve_codex(codex_raw)
    # Codex's Windows image sidecar may not resolve Chinese workspace paths.
    # Supply byte-identical ASCII-only temporary attachments for this review.
    staging = Path(tempfile.mkdtemp(prefix="story-os-visual-lock-"))
    staged_assets = []
    for row in assets:
        staged = staging / f"{row['id']}-{int(row['frame']):02d}{Path(row['path']).suffix.lower()}"
        shutil.copy2(row["path"], staged)
        staged_assets.append(staged)
    cmd = prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="high"',
        "-s", "workspace-write", "-C", str(ROOT), "--json"
    ]
    for staged in staged_assets:
        cmd += ["-i", str(staged)]
    cmd += ["-"]
    log = ep / "meta" / f"visual-lock-critic-attempt-{attempt}.jsonl"
    try:
        with log.open("w", encoding="utf-8", newline="\n") as handle:
            done = subprocess.run(
                cmd,
                input=critic_prompt(ep, contract, assets, candidate, attempt).encode("utf-8"),
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    if done.returncode != 0:
        log_text = log.read_text(encoding="utf-8-sig", errors="replace") if log.is_file() else ""
        codes = critic_runtime_v211.classify_log_text(log_text) or ["CRITIC_PROCESS_ERROR"]
        health = critic_runtime_v211.record_technical_failure(
            ep, issue_codes=codes, attempt=attempt,
            log=log.relative_to(ROOT).as_posix(), source="visual_lock_critic_process")
        print("VISUAL LOCK CRITIC TECHNICAL FAIL:", ",".join(codes), "status="+health["status"])
        return 11
    if not candidate.is_file():
        health = critic_runtime_v211.record_technical_failure(
            ep, issue_codes=["CRITIC_OUTPUT_MISSING"], attempt=attempt,
            log=log.relative_to(ROOT).as_posix(), source="visual_lock_critic_output")
        print("VISUAL LOCK CRITIC TECHNICAL FAIL: CRITIC_OUTPUT_MISSING status="+health["status"])
        return 11
    current = calibration_assets(ep)
    if {r["id"]: r["sha256"] for r in current} != before:
        raise RuntimeError("Visual Lock critic modified calibration images")
    data = read_json(candidate)
    data["schema_version"] = 2
    data["story_os_version"] = episode_version(ep)
    data["profile_id"] = contract["profile_id"]
    data["profile_path"] = contract["profile_path"]
    data["profile_sha256"] = contract["profile_sha256"]
    data["critic_provenance"] = {
        "runtime": "CODEX_ISOLATED",
        "isolated_session": True,
        "attempt": attempt,
        "reviewed_at": now(),
        "log": log.relative_to(ROOT).as_posix(),
    }
    by_id = {r["id"]: r for r in current}
    for row in data.get("calibration") or []:
        rid = str(row.get("id") or "")
        if rid in by_id:
            row["sha256"] = by_id[rid]["sha256"]
            row["frame_contract_sha256"] = by_id[rid]["frame_contract_sha256"]
            row["frame"] = by_id[rid]["frame"]
            row["role"] = by_id[rid]["role"]
    # STORY_OS_V211_PERF_RECOVERY: infrastructure failure is not content failure.
    technical_codes = critic_runtime_v211.classify_issue_codes(data.get("issue_codes") or [])
    if technical_codes:
        write_json(ep / REVIEW_REL, data)
        candidate.unlink(missing_ok=True)
        health = critic_runtime_v211.record_technical_failure(
            ep, issue_codes=technical_codes, attempt=attempt,
            log=log.relative_to(ROOT).as_posix(), source="visual_lock_critic_payload")
        print("VISUAL LOCK CRITIC TECHNICAL FAIL:", ",".join(technical_codes), "status="+health["status"])
        return 11

    errors = validate_payload(data, contract=contract, assets=current, version=episode_version(ep))
    if errors:
        _record_failed_calibration_frames(ep, data)
    write_json(ep / REVIEW_REL, data)
    candidate.unlink(missing_ok=True)
    critic_runtime_v211.record_content_result(
        ep, passed=not errors, attempt=attempt,
        issue_codes=data.get("issue_codes") or [], log=log.relative_to(ROOT).as_posix())
    _mark_decisions(ep, not errors)
    if errors:
        print("VISUAL LOCK V2.1 REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        return 2
    if character_visual_contract.pixel_master_required(ep):
        expected=_pixel_master_expected(current)
        if expected is None:raise RuntimeError("ordinary_baseline asset missing for character pixel master")
        character_visual_contract.lock_pixel_master(ep,frame=expected["frame"],asset_path=expected["asset_path"],asset_sha256=expected["sha256"],frame_contract_sha256=expected["frame_contract_sha256"])
    print("VISUAL LOCK V2.1 REVIEW PASS")
    return 0


def self_test() -> None:
    assert len(ROLES) == 4
    assert len(CHECKS) == 11
    assert version_tuple("2.1.0") >= MIN_VERSION
    print("VISUAL LOCK V2.1 PHASE5 SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare"); p.add_argument("episode_dir")
    p = sub.add_parser("bind-from-queue"); p.add_argument("episode_dir")
    p = sub.add_parser("run-critic"); p.add_argument("episode_dir"); p.add_argument("--attempt", type=int, default=1); p.add_argument("--codex"); p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("verify"); p.add_argument("episode_dir")
    p = sub.add_parser("show-plan"); p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    ep = resolve_ep(args.episode_dir)
    try:
        if args.cmd == "prepare":
            print(json.dumps(prepare(ep), ensure_ascii=False, indent=2)); return 0
        if args.cmd == "bind-from-queue":
            print(json.dumps(bind_from_queue(ep), ensure_ascii=False, indent=2)); return 0
        if args.cmd == "show-plan":
            p = ep / PLAN_REL
            if not p.is_file():
                print(json.dumps(choose_plan(ep), ensure_ascii=False, indent=2))
            else:
                print(p.read_text(encoding="utf-8"))
            return 0
        if args.cmd == "run-critic":
            return run_critic(ep, attempt=args.attempt, codex_raw=args.codex, timeout=args.timeout)
        errors = verify(ep)
        if errors:
            for error in errors:
                print("FAIL:", error)
            return 2
        print("VISUAL LOCK V2.1 VERIFIED")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print("VISUAL LOCK ERROR:", exc)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())

# STORY_OS_V211_RUNTIME_CLOSURE_R31
