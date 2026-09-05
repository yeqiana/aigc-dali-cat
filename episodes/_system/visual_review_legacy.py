#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from story_os_contract import story_os_version
from visual_profile import compile_prompt_contract
import runtime_router
import runtime_provenance
import product_review_adapter

ROOT = Path(__file__).resolve().parents[2]
REVIEW_REL = Path("meta/visual-profile-review.json")
CANDIDATE_REL = Path("meta/.visual-profile-review.candidate.json")
TARGET_CONTRACT = (2, 0, 3, 2)
CHECKS = [
    "visual_profile_match",
    "reality_first",
    "ordinary_life_density",
    "available_light",
    "unposed_capture",
    "not_cinematic",
    "causal_imperfection",
]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def version_tuple(raw: object) -> tuple[int, ...]:
    try:
        return tuple(int(x) for x in str(raw or "").split("."))
    except ValueError:
        return (0,)


def episode_contract_version(ep: Path) -> str:
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
    return max(versions, key=lambda x: x[0])[1] if versions else story_os_version()


def review_required(ep: Path) -> bool:
    for rel in ("meta/episode-state.json", "meta/release-manifest.json"):
        p = ep / rel
        if not p.is_file():
            continue
        try:
            if version_tuple(read_json(p).get("tool_version")) >= TARGET_CONTRACT:
                return True
        except Exception:
            continue
    return False


def repo_file(raw: object) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("calibration path missing")
    rel = Path(raw.strip())
    p = rel.resolve() if rel.is_absolute() else (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError("calibration path escapes repository") from exc
    if not p.is_file():
        raise ValueError(f"calibration image missing: {raw}")
    return p


def calibration_assets(ep: Path) -> list[dict]:
    gates = read_json(ep / "meta/story-gates.json")
    calibration = ((gates.get("visual") or {}).get("calibration") or {})
    rows: list[dict] = []

    if isinstance(calibration.get("items"), list):
        for item in calibration["items"]:
            if not isinstance(item, dict) or item.get("decision") not in {"passed", "pass"}:
                continue
            raw = item.get("path") or item.get("asset_path")
            p = repo_file(raw)
            rows.append({
                "id": str(item.get("id") or item.get("frame") or len(rows) + 1),
                "role": str(item.get("role") or ""),
                "path": p,
                "sha256": sha256_file(p),
            })
    else:
        for key, role in [
            ("baseline", "ordinary_baseline"),
            ("worst_condition", "worst_capture_condition"),
            ("first_major_anomaly", "first_major_anomaly"),
        ]:
            item = calibration.get(key) or {}
            if item.get("decision") not in {"passed", "pass"}:
                continue
            raw = item.get("asset_path") or item.get("path")
            p = repo_file(raw)
            rows.append({
                "id": str(item.get("frame") or key),
                "role": role,
                "path": p,
                "sha256": sha256_file(p),
            })
    if len(rows) != 3:
        raise ValueError(f"exactly 3 passed calibration images are required; found {len(rows)}")
    return rows


def validate_payload(data: dict, *, profile_id: str, profile_sha: str, assets: list[dict], version: str) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("story_os_version") != version:
        errors.append("story_os_version mismatch")
    if data.get("profile_id") != profile_id:
        errors.append("profile_id mismatch")
    if str(data.get("profile_sha256") or "").lower() != profile_sha.lower():
        errors.append("profile_sha256 mismatch")
    provenance = data.get("critic_provenance") or {}
    errors.extend(runtime_provenance.validate_critic_provenance(provenance))

    expected = {str(row["id"]): row for row in assets}
    actual_rows = data.get("calibration")
    if not isinstance(actual_rows, list) or len(actual_rows) != 3:
        errors.append("calibration review must contain exactly 3 rows")
    else:
        seen = set()
        for row in actual_rows:
            rid = str(row.get("id") or "")
            seen.add(rid)
            exp = expected.get(rid)
            if exp is None:
                errors.append(f"unexpected calibration id: {rid}")
                continue
            if str(row.get("sha256") or "").lower() != exp["sha256"].lower():
                errors.append(f"calibration sha mismatch: {rid}")
            checks = row.get("checks") or {}
            for key in CHECKS:
                if checks.get(key) is not True:
                    errors.append(f"{rid}.checks.{key} must be true")
            if row.get("issues") not in ([], None):
                errors.append(f"{rid}.issues must be empty for PASS")
        if seen != set(expected):
            errors.append("calibration review ids do not match passed calibration assets")

    if data.get("issue_codes") not in ([], None):
        errors.append("issue_codes must be empty for PASS")
    if (data.get("summary") or {}).get("passed") is not True:
        errors.append("summary.passed must be true")
    return errors


def verify(ep: Path) -> list[str]:
    if not review_required(ep):
        return []
    path = ep / REVIEW_REL
    if not path.is_file():
        return ["meta/visual-profile-review.json missing"]
    try:
        contract = compile_prompt_contract(ep)
        assets = calibration_assets(ep)
        data = read_json(path)
    except Exception as exc:
        return [str(exc)]
    return validate_payload(
        data,
        profile_id=contract["profile_id"],
        profile_sha=contract["profile_sha256"],
        assets=assets,
        version=episode_contract_version(ep),
    )


def resolve_codex(raw: str | None) -> Path:
    value = raw or shutil.which("codex") or shutil.which("codex.exe") or shutil.which("codex.cmd")
    if not value:
        raise RuntimeError("Codex CLI not found")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise RuntimeError(f"Codex CLI not found: {path}")
    return path


def prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]


def critic_prompt(ep: Path, contract: dict, assets: list[dict], candidate: Path, attempt: int) -> str:
    rel_out = candidate.relative_to(ROOT).as_posix()
    listed = "\n".join(
        f"- id={row['id']} role={row['role']} file={row['path'].name}" for row in assets
    )
    return f"""You are an adversarial Visual Profile Critic in a fresh isolated session.
You are reviewing exactly THREE attached calibration images. Do not generate images. Do not rewrite prompts.
The resolved visual profile is {contract['profile_id']}.
Its compact production contract is:
<visual_contract>
{contract['text']}
</visual_contract>

Calibration rows:
{listed}

A generic clean outdoor documentary look is NOT enough. For M00, actual images must feel like plausible personal/work records in real Chinese life, with scene-caused imperfection, available light, unposed composition, ordinary-life density where the scene allows it, non-commercial rendering, and anomaly embedded into reality rather than presented as spectacle.
Do not pass because the prompt says M00. Judge the ACTUAL attached images.
If any calibration image is polished/cinematic, staged, commercially clean, causally fake in its defects, or visually drifts from the resolved profile, fail it.

Write ONLY valid JSON to {rel_out}. Do not modify any other file.
Shape:
{{
  "calibration": [
    {{
      "id": "copy the exact id",
      "checks": {{
        "visual_profile_match": true,
        "reality_first": true,
        "ordinary_life_density": true,
        "available_light": true,
        "unposed_capture": true,
        "not_cinematic": true,
        "causal_imperfection": true
      }},
      "issues": [],
      "notes": "specific visual evidence"
    }}
  ],
  "issue_codes": [],
  "summary": {{"passed": true}}
}}
PASS only if ALL seven checks are true on ALL three images and issue_codes is empty.
This is attempt {attempt}.
"""


def run_critic(ep: Path, *, attempt: int, codex_raw: str | None, timeout: int) -> int:
    if attempt not in {1, 2}:
        raise RuntimeError("attempt must be 1 or 2")
    contract = compile_prompt_contract(ep)
    assets = calibration_assets(ep)
    candidate = ep / CANDIDATE_REL
    before = {str(row["id"]): row["sha256"] for row in assets}
    active_runtime, _ = runtime_router.detect()
    if active_runtime in {"WORK", "WEB"} and not codex_raw:
        kind = "visual-profile-legacy"
        request_file = product_review_adapter.request_path(ep, kind, attempt=attempt)
        if candidate.is_file() and request_file.is_file():
            return finalize_product_review(ep, attempt=attempt, runtime=active_runtime)
        candidate.unlink(missing_ok=True)
        request = product_review_adapter.prepare(
            ep,
            kind=kind,
            runtime=active_runtime,
            attempt=attempt,
            prompt=critic_prompt(ep, contract, assets, candidate, attempt),
            source_paths=[ep / "meta/story-gates.json", Path(contract["profile_path"]).resolve() if Path(contract["profile_path"]).is_absolute() else ROOT / contract["profile_path"], *[row["path"] for row in assets]],
            candidate_path=candidate,
        )
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return product_review_adapter.HOST_ACTION_REQUIRED_RC

    candidate.unlink(missing_ok=True)
    codex = resolve_codex(codex_raw)
    cmd = prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="high"',
        "-s", "workspace-write", "-C", str(ROOT), "--json"
    ]
    for row in assets:
        cmd += ["-i", str(row["path"])]
    cmd += ["-"]
    log = ep / "meta" / f"visual-critic-attempt-{attempt}.jsonl"
    with log.open("w", encoding="utf-8", newline="\n") as handle:
        completed = subprocess.run(
            cmd,
            input=critic_prompt(ep, contract, assets, candidate, attempt),
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"isolated visual critic failed rc={completed.returncode}; log={log}")
    if not candidate.is_file():
        raise RuntimeError(f"visual critic did not produce {candidate}")
    current_assets = calibration_assets(ep)
    for row in current_assets:
        if before.get(str(row["id"])) != row["sha256"]:
            raise RuntimeError("visual critic modified calibration assets")

    data = read_json(candidate)
    data["schema_version"] = 1
    data["story_os_version"] = episode_contract_version(ep)
    data["profile_id"] = contract["profile_id"]
    data["profile_path"] = contract["profile_path"]
    data["profile_sha256"] = contract["profile_sha256"]
    data["critic_provenance"] = runtime_provenance.build_critic_provenance(
        "CODEX",
        attempt=attempt,
        log=log.relative_to(ROOT).as_posix(),
    )
    by_id = {str(row["id"]): row for row in current_assets}
    for row in data.get("calibration") or []:
        rid = str(row.get("id") or "")
        if rid in by_id:
            row["sha256"] = by_id[rid]["sha256"]

    errors = validate_payload(
        data,
        profile_id=contract["profile_id"],
        profile_sha=contract["profile_sha256"],
        assets=current_assets,
        version=episode_contract_version(ep),
    )
    final = ep / REVIEW_REL
    write_json(final, data)
    candidate.unlink(missing_ok=True)
    if errors:
        print("VISUAL PROFILE REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        return 2
    print("VISUAL PROFILE REVIEW PASS")
    return 0


def finalize_product_review(ep: Path, *, attempt: int, runtime: str) -> int:
    contract = compile_prompt_contract(ep)
    assets = calibration_assets(ep)
    candidate = ep / CANDIDATE_REL
    data, provenance = product_review_adapter.finalize_candidate(
        ep,
        kind="visual-profile-legacy",
        runtime=runtime,
        attempt=attempt,
        candidate_path=candidate,
    )
    data["schema_version"] = 1
    data["story_os_version"] = episode_contract_version(ep)
    data["profile_id"] = contract["profile_id"]
    data["profile_path"] = contract["profile_path"]
    data["profile_sha256"] = contract["profile_sha256"]
    data["critic_provenance"] = provenance
    by_id = {str(row["id"]): row for row in assets}
    for row in data.get("calibration") or []:
        rid = str(row.get("id") or "")
        if rid in by_id:
            row["sha256"] = by_id[rid]["sha256"]
    errors = validate_payload(
        data,
        profile_id=contract["profile_id"],
        profile_sha=contract["profile_sha256"],
        assets=assets,
        version=episode_contract_version(ep),
    )
    final = ep / REVIEW_REL
    write_json(final, data)
    if errors:
        print("VISUAL PROFILE REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        return 2
    product_review_adapter.mark_complete(ep, "visual-profile-legacy", attempt=attempt, final_path=final)
    candidate.unlink(missing_ok=True)
    print("VISUAL PROFILE REVIEW PASS")
    return 0


def self_test() -> None:
    h = "a" * 64
    assets = [{"id": x, "sha256": h} for x in ("A", "B", "C")]
    data = {
        "schema_version": 1,
        "story_os_version": story_os_version(),
        "profile_id": "M00",
        "profile_sha256": h,
        "critic_provenance": runtime_provenance.build_critic_provenance("WORK", attempt=1),
        "calibration": [
            {"id": x, "sha256": h, "checks": {k: True for k in CHECKS}, "issues": []}
            for x in ("A", "B", "C")
        ],
        "issue_codes": [],
        "summary": {"passed": True},
    }
    assert validate_payload(data, profile_id="M00", profile_sha=h, assets=assets, version=story_os_version()) == []
    data["calibration"][0]["checks"]["not_cinematic"] = False
    assert validate_payload(data, profile_id="M00", profile_sha=h, assets=assets, version=story_os_version())
    print("VISUAL PROFILE REVIEW SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run-critic")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=900)
    p = sub.add_parser("finalize-review")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--runtime", choices=["WORK", "WEB"], default="WORK")
    p = sub.add_parser("verify")
    p.add_argument("episode_dir")
    p = sub.add_parser("show")
    p.add_argument("episode_dir")
    sub.add_parser("self-test")
    args = ap.parse_args()

    if args.cmd == "self-test":
        self_test()
        return 0
    ep = Path(args.episode_dir).resolve()
    if not ep.is_dir():
        raise SystemExit(f"episode directory not found: {ep}")
    if args.cmd == "run-critic":
        try:
            return run_critic(ep, attempt=args.attempt, codex_raw=args.codex, timeout=args.timeout)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            print("VISUAL PROFILE REVIEW ERROR:", exc)
            return 3
    if args.cmd == "finalize-review":
        try:
            return finalize_product_review(ep, attempt=args.attempt, runtime=args.runtime)
        except (OSError, RuntimeError, ValueError, product_review_adapter.ProductReviewError) as exc:
            print("VISUAL PROFILE REVIEW ERROR:", exc)
            return 3
    if args.cmd == "show":
        p = ep / REVIEW_REL
        print(p.read_text(encoding="utf-8") if p.is_file() else "{}")
        return 0
    errors = verify(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("VISUAL PROFILE REVIEW VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
