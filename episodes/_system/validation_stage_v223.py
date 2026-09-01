from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional

VERSION = "2.2.3"

PLACEHOLDER_TOKENS = {
    "", "todo", "tbd", "placeholder", "pending", "idea_locked",
    "null", "none", "unknown", "待补", "待定", "占位", "空骨架"
}

BOOTSTRAP_GROUPS = {
    "episode_blueprint": [
        "episode_blueprint.json", "*blueprint*.json"
    ],
    "chapter_lock": [
        "chapter_lock.json", "*chapter*lock*.json"
    ],
    "visual_profile": [
        "visual_profile.json", "*visual*profile*.json"
    ],
    "asset_manifest": [
        "asset_manifest.json", "*asset*manifest*.json"
    ],
}

PREPRODUCTION_GROUPS = {
    "character_contract": [
        "character_contract.json", "*character*contract*.json"
    ],
    "location_contract": [
        "location_contract.json", "*location*contract*.json",
        "*environment*contract*.json"
    ],
    "device_or_prop_contract": [
        "device_contract.json", "*device*contract*.json",
        "prop_contract.json", "*prop*contract*.json"
    ],
    "asset_manifest": [
        "asset_manifest.json", "*asset*manifest*.json"
    ],
    "resolved_frame_contracts": [
        "*resolved*frame*contract*.json",
        "resolved_frame_contracts.json",
        "contracts/*.json",
        "runtime/contracts/*.json",
        "meta/runtime/contracts/*.json",
    ],
    "authority_or_binding": [
        "*authority*.json", "*binding*.json", "*handoff*.json"
    ],
}

SHA_KEYS = {
    "sha", "sha1", "sha256", "authority_sha", "asset_sha",
    "blob_sha", "digest", "content_sha"
}

AUTHORITY_KEYS = {
    "authority_scope", "authority_source", "authority",
    "source_branch", "branch"
}


@dataclass
class CheckResult:
    name: str
    status: str
    path: Optional[str] = None
    detail: Optional[str] = None


def _norm(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).lower()
    return str(v).strip().lower()


def _json_has_placeholder(value) -> bool:
    if isinstance(value, dict):
        return any(_json_has_placeholder(k) or _json_has_placeholder(v) for k, v in value.items())
    if isinstance(value, list):
        return any(_json_has_placeholder(x) for x in value)
    if isinstance(value, str):
        return _norm(value) in PLACEHOLDER_TOKENS
    return False


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _is_meaningful_json(path: Path) -> tuple[bool, str]:
    data = _load_json(path)
    if data is None:
        return False, "INVALID_JSON"
    if data in ({}, [], None):
        return False, "EMPTY_JSON"
    if _json_has_placeholder(data):
        return False, "PLACEHOLDER_CONTENT"
    return True, "OK"


def _candidate_files(root: Path, patterns: Iterable[str]) -> list[Path]:
    found = []
    for pattern in patterns:
        found.extend(p for p in root.rglob(pattern) if p.is_file())
    # deterministic + dedupe
    uniq = {}
    for p in found:
        uniq[str(p.resolve())] = p
    return sorted(uniq.values(), key=lambda p: (len(p.parts), str(p).lower()))


def _find_meaningful(root: Path, patterns: Iterable[str]) -> tuple[Optional[Path], str]:
    candidates = _candidate_files(root, patterns)
    if not candidates:
        return None, "MISSING"
    reasons = []
    for p in candidates:
        if p.suffix.lower() == ".json":
            ok, reason = _is_meaningful_json(p)
            if ok:
                return p, "OK"
            reasons.append(f"{p.name}:{reason}")
        elif p.stat().st_size > 0:
            return p, "OK"
        else:
            reasons.append(f"{p.name}:EMPTY_FILE")
    return None, "; ".join(reasons) if reasons else "MISSING"


def _walk_json_values(obj, key_filter: set[str]):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in key_filter:
                hits.append(v)
            hits.extend(_walk_json_values(v, key_filter))
    elif isinstance(obj, list):
        for x in obj:
            hits.extend(_walk_json_values(x, key_filter))
    return hits


def _sha_like(value: str) -> bool:
    value = value.strip().lower()
    return bool(re.fullmatch(r"[0-9a-f]{7,64}", value))


def _validate_sha_presence(paths: list[Path]) -> CheckResult:
    vals = []
    for p in paths:
        data = _load_json(p)
        if data is not None:
            vals.extend(_walk_json_values(data, SHA_KEYS))
    good = [str(v) for v in vals if isinstance(v, str) and _sha_like(v)]
    if good:
        return CheckResult("asset_sha_or_digest", "PASS", detail=f"{len(good)} SHA/digest value(s)")
    return CheckResult(
        "asset_sha_or_digest",
        "FAIL",
        detail="No SHA/digest field with a plausible hexadecimal value was found."
    )


def _validate_authority_scope(paths: list[Path]) -> CheckResult:
    vals = []
    for p in paths:
        data = _load_json(p)
        if data is not None:
            vals.extend(_walk_json_values(data, AUTHORITY_KEYS))
    normalized = [_norm(v) for v in vals if isinstance(v, (str, int))]
    allowed_markers = {
        "current_story_branch", "story", "current branch",
        "current_story", "current-story-branch"
    }
    bad_markers = ("external", "ohmyphoto", "other_repo", "workspace", "history")
    if any(any(b in v for b in bad_markers) for v in normalized):
        return CheckResult(
            "authority_scope",
            "FAIL",
            detail="External/abandoned authority marker detected."
        )
    if any(v in allowed_markers or "current_story_branch" in v for v in normalized):
        return CheckResult(
            "authority_scope",
            "PASS",
            detail="Authority is explicitly scoped to the current story branch."
        )
    return CheckResult(
        "authority_scope",
        "FAIL",
        detail="Authority scope is not explicitly bound to current_story_branch/story."
    )


def _collect_json(root: Path) -> list[Path]:
    return sorted([p for p in root.rglob("*.json") if p.is_file()])


def validate_bootstrap(episode_dir: Path) -> dict:
    checks = []
    for name, patterns in BOOTSTRAP_GROUPS.items():
        p, reason = _find_meaningful(episode_dir, patterns)
        if p:
            checks.append(CheckResult(name, "PASS", str(p.relative_to(episode_dir))))
        else:
            checks.append(CheckResult(name, "FAIL", detail=reason))

    status = "BOOTSTRAP_VALIDATE_PASS" if all(c.status == "PASS" for c in checks) else "BOOTSTRAP_VALIDATE_FAILED"
    return {
        "story_os_validation_version": VERSION,
        "stage": "bootstrap",
        "episode_dir": str(episode_dir),
        "status": status,
        "checks": [asdict(c) for c in checks],
        "next_state": "READY_FOR_PREPRODUCTION" if status.endswith("_PASS") else "BOOTSTRAP_INCOMPLETE",
    }


def validate_preproduction(episode_dir: Path) -> dict:
    checks = []

    # Preproduction validation includes bootstrap validity as a hard dependency.
    bootstrap = validate_bootstrap(episode_dir)
    checks.append(CheckResult(
        "bootstrap_dependency",
        "PASS" if bootstrap["status"] == "BOOTSTRAP_VALIDATE_PASS" else "FAIL",
        detail=bootstrap["status"]
    ))

    located = []
    for name, patterns in PREPRODUCTION_GROUPS.items():
        p, reason = _find_meaningful(episode_dir, patterns)
        if p:
            located.append(p)
            checks.append(CheckResult(name, "PASS", str(p.relative_to(episode_dir))))
        else:
            checks.append(CheckResult(name, "FAIL", detail=reason))

    json_files = _collect_json(episode_dir)
    checks.append(_validate_sha_presence(json_files))
    checks.append(_validate_authority_scope(json_files))

    status = "PREPRODUCTION_VALIDATE_PASS" if all(c.status == "PASS" for c in checks) else "PREPRODUCTION_VALIDATE_FAILED"
    return {
        "story_os_validation_version": VERSION,
        "stage": "preproduction",
        "episode_dir": str(episode_dir),
        "status": status,
        "checks": [asdict(c) for c in checks],
        "next_state": "READY_FOR_SMOKE_TEST" if status.endswith("_PASS") else "PREPRODUCTION_INCOMPLETE",
    }


def write_report(episode_dir: Path, result: dict) -> Path:
    out_dir = episode_dir / "meta" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{result['stage']}_validation_report.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Story OS V2.2.3 staged validation"
    )
    parser.add_argument(
        "stage",
        choices=["bootstrap", "preproduction"],
        help="Validation stage"
    )
    parser.add_argument(
        "episode_dir",
        help="Episode directory, e.g. episodes/12_千寻/01_那条不存在的隧道"
    )
    parser.add_argument(
        "--no-write-report",
        action="store_true",
        help="Do not write meta/validation/*_validation_report.json"
    )
    args = parser.parse_args()

    episode_dir = Path(args.episode_dir).resolve()
    if not episode_dir.is_dir():
        print(json.dumps({
            "status": "VALIDATION_ERROR",
            "detail": f"Episode directory does not exist: {episode_dir}"
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    result = validate_bootstrap(episode_dir) if args.stage == "bootstrap" else validate_preproduction(episode_dir)

    if not args.no_write_report:
        report = write_report(episode_dir, result)
        result["report"] = str(report)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"].endswith("_PASS") else 1)


if __name__ == "__main__":
    main()
