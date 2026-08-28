#!/usr/bin/env python3
"""Story OS V2.0.3 contract/adapter consistency validator.

This validator intentionally checks *contract parity*, not implementation parity.
The canonical engine is allowed to exist only under episodes/_system; Skill folders
must remain thin adapters and must not grow proxy copies of core engine modules.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

EXPECTED_VERSION = "2.0.3"
EXPECTED_STAGES = [
    "IDEA_LOCKED",
    "STORYBOARD_LOCKED",
    "VISUAL_CALIBRATED",
    "PRODUCTION_PASSED",
    "PUBLISH_READY",
    "PUBLISHED",
    "DATA_REVIEWED",
]
CORE_ENGINE_FILES = [
    "episode_state.py",
    "validate_episode.py",
    "machine_gate.py",
    "evidence_gate.py",
    "canvas_normalize.py",
    "delegated_delivery.py",
    "codex_auto_orchestrator.py",
]
REQUIRED_CAPABILITIES = {
    "single_state_machine",
    "multi_runtime",
    "machine_gate",
    "evidence_gate",
    "production_ledger",
    "frame_reviews",
    "canvas_normalization",
    "deterministic_postflight",
    "delegated_delivery",
    "release_manifest",
    "minimal_edit_contract",
}
ADAPTER_SKILLS = [
    Path("skills/dali-cat-story/SKILL.md"),
    Path(".agents/skills/dali-cat-story/SKILL.md"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _contains_v203(text: str) -> bool:
    return bool(re.search(r"\bV?2\.0\.3\b", text, flags=re.IGNORECASE))


def collect_errors(root: Path | None = None) -> list[str]:
    root = root or repo_root()
    errors: list[str] = []

    manifest_path = root / "story_os_manifest.json"
    if not manifest_path.is_file():
        return ["missing story_os_manifest.json"]

    try:
        manifest = json.loads(read_text(manifest_path))
    except Exception as exc:  # pragma: no cover - defensive CLI path
        return [f"invalid story_os_manifest.json: {exc}"]

    if manifest.get("story_os_version") != EXPECTED_VERSION:
        errors.append(
            f"manifest version must be {EXPECTED_VERSION}, got {manifest.get('story_os_version')!r}"
        )
    if manifest.get("canonical_engine") != "episodes/_system":
        errors.append("canonical_engine must be episodes/_system")
    if manifest.get("canonical_state_source") != "<episode>/meta/episode-state.json":
        errors.append("canonical_state_source must remain <episode>/meta/episode-state.json")
    if manifest.get("stages") != EXPECTED_STAGES:
        errors.append("manifest stages drifted from the canonical seven-stage machine")

    declared_capabilities = set(manifest.get("capabilities") or [])
    missing_caps = sorted(REQUIRED_CAPABILITIES - declared_capabilities)
    if missing_caps:
        errors.append("manifest missing capabilities: " + ", ".join(missing_caps))

    version_files = [
        Path("START_HERE.md"),
        Path("SKILL.md"),
        Path("episodes/_system/README.md"),
        *ADAPTER_SKILLS,
    ]
    for rel in version_files:
        p = root / rel
        if not p.is_file():
            errors.append(f"missing contract file: {rel.as_posix()}")
            continue
        if not _contains_v203(read_text(p)):
            errors.append(f"{rel.as_posix()} does not declare Story OS V2.0.3")

    engine = root / "episodes" / "_system"
    for name in CORE_ENGINE_FILES:
        if not (engine / name).is_file():
            errors.append(f"missing canonical engine file: episodes/_system/{name}")

    # Skill scripts must never become a second engine implementation.
    skill_scripts = root / "skills" / "dali-cat-story" / "scripts"
    for name in CORE_ENGINE_FILES:
        duplicate = skill_scripts / name
        if duplicate.exists():
            errors.append(
                f"duplicate engine implementation forbidden in Skill: {duplicate.relative_to(root).as_posix()}"
            )

    for rel in ADAPTER_SKILLS:
        p = root / rel
        if not p.is_file():
            continue
        text = read_text(p)
        for token in [
            "episodes/_system",
            "episode-state.json",
            *sorted(REQUIRED_CAPABILITIES),
        ]:
            if token not in text:
                errors.append(f"{rel.as_posix()} missing adapter contract token: {token}")
        if "Skill is an adapter, not a Story OS copy" not in text:
            errors.append(f"{rel.as_posix()} missing thin-adapter invariant")

    # Wrapper smoke-level source checks. Runtime behavior is covered by unit tests.
    bootstrap = skill_scripts / "bootstrap_episode.py"
    if not bootstrap.is_file():
        errors.append("missing Skill wrapper: skills/dali-cat-story/scripts/bootstrap_episode.py")
    else:
        text = read_text(bootstrap)
        for token in ["episodes", "_system", "episode_state.py", '"init"']:
            if token not in text:
                errors.append(f"bootstrap_episode.py no longer delegates canonical init ({token})")

    validate_all = skill_scripts / "validate_all.py"
    if not validate_all.is_file():
        errors.append("missing Skill wrapper: skills/dali-cat-story/scripts/validate_all.py")
    else:
        text = read_text(validate_all)
        for token in ["episodes", "_system", "validate_episode.py"]:
            if token not in text:
                errors.append(f"validate_all.py no longer delegates canonical validator ({token})")

    # Detect stale/phantom script references in the adapter scripts README.
    scripts_readme = skill_scripts / "README.md"
    if not scripts_readme.is_file():
        errors.append("missing skills/dali-cat-story/scripts/README.md")
    else:
        text = read_text(scripts_readme)
        code_refs = set(re.findall(r"`([^`\n]+\.py)`", text))
        for ref in sorted(code_refs):
            if ref.startswith("episodes/_system/"):
                target = root / ref
            elif "/" in ref or "\\" in ref:
                target = root / Path(ref.replace("\\", "/"))
            else:
                target = skill_scripts / ref
            if not target.is_file():
                errors.append(f"adapter scripts README references missing file: {ref}")

    workflow = root / ".github" / "workflows" / "story-gates.yml"
    if not workflow.is_file():
        errors.append("missing .github/workflows/story-gates.yml")
    else:
        wf = read_text(workflow)
        for token in [
            ".agents/skills/dali-cat-story/**",
            "python episodes/_system/contract_sync.py",
            "python episodes/_system/test_v203_contract_hardening.py -v",
        ]:
            if token not in wf:
                errors.append(f"CI missing V2.0.3 contract check: {token}")

    return errors


def main(argv: Iterable[str] | None = None) -> int:
    errors = collect_errors()
    if errors:
        print("[FAIL] Story OS V2.0.3 contract sync")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("[PASS] Story OS V2.0.3 contract sync")
    print("       thin adapters -> episodes/_system canonical engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
