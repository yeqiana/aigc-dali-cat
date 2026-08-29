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

ROOT = Path(__file__).resolve().parents[2]
REVIEW_REL = Path("meta/story-semantic-review.json")
CANDIDATE_REL = Path("meta/.story-semantic-review.candidate.json")
TARGET_CONTRACT = (2, 0, 3, 2)

CONTRACT_FIELDS = [
    "protagonist",
    "presence_reason",
    "personal_stake",
    "core_anomaly",
    "rule",
    "trigger",
    "direct_consequence",
    "midpoint_reframe",
    "climax_choice",
]
BLIND_FIELDS = [
    "protagonist_and_reason",
    "core_anomaly_rule",
    "worsening_choice",
    "climax_resolution",
    "ending_reinterpretation",
]
HARD_CHECKS = [
    "clarity",
    "causal_chain",
    "mechanism_consistency",
    "motivation_stake",
    "trigger_consequence",
    "midpoint_reframe",
    "climax_payoff",
    "ending_payoff",
    "storyboard_information_gain",
    "delete_frame_test",
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


def repo_file(raw: object, where: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{where} missing")
    rel = Path(raw.strip())
    p = rel.resolve() if rel.is_absolute() else (ROOT / rel).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{where} escapes repository") from exc
    if not p.is_file():
        raise ValueError(f"{where} missing: {raw}")
    return p


def story_paths(ep: Path) -> tuple[Path, Path]:
    manifest = read_json(ep / "meta/release-manifest.json")
    artifacts = manifest.get("artifacts") or {}
    return (
        repo_file(artifacts.get("story"), "manifest.artifacts.story"),
        repo_file(artifacts.get("storyboard"), "manifest.artifacts.storyboard"),
    )


def validate_payload(data: dict, *, story_sha: str, storyboard_sha: str, version: str) -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("story_os_version") != version:
        errors.append("story_os_version mismatch")
    if str(data.get("story_sha256") or "").lower() != story_sha.lower():
        errors.append("story_sha256 mismatch")
    if str(data.get("storyboard_sha256") or "").lower() != storyboard_sha.lower():
        errors.append("storyboard_sha256 mismatch")

    provenance = data.get("critic_provenance") or {}
    if provenance.get("runtime") != "CODEX_ISOLATED":
        errors.append("critic runtime must be CODEX_ISOLATED")
    if provenance.get("isolated_session") is not True:
        errors.append("critic must be an isolated session")
    attempt = provenance.get("attempt")
    if attempt not in {1, 2}:
        errors.append("critic attempt must be 1 or 2")
    if data.get("revision_count") not in {0, 1}:
        errors.append("revision_count must be 0 or 1")
    elif attempt in {1, 2} and data.get("revision_count") != attempt - 1:
        errors.append("revision_count must equal critic attempt - 1")

    contract = data.get("contract") or {}
    for key in CONTRACT_FIELDS:
        if not str(contract.get(key) or "").strip():
            errors.append(f"contract.{key} missing")
    reinterpret = contract.get("ending_recontextualization")
    if not isinstance(reinterpret, list) or len([x for x in reinterpret if str(x).strip()]) < 3:
        errors.append("ending must recontextualize at least 3 concrete earlier facts")

    blind = data.get("blind_retell") or {}
    for key in BLIND_FIELDS:
        if not str(blind.get(key) or "").strip():
            errors.append(f"blind_retell.{key} missing")

    checks = data.get("hard_checks") or {}
    for key in HARD_CHECKS:
        if checks.get(key) is not True:
            errors.append(f"hard_checks.{key} must be true")

    issue_codes = data.get("issue_codes")
    if not isinstance(issue_codes, list):
        errors.append("issue_codes must be a list")
    elif issue_codes:
        errors.append("issue_codes must be empty for PASS")

    summary = data.get("summary") or {}
    if summary.get("passed") is not True:
        errors.append("summary.passed must be true")
    return errors


def verify(ep: Path) -> list[str]:
    if not review_required(ep):
        return []
    path = ep / REVIEW_REL
    if not path.is_file():
        return ["meta/story-semantic-review.json missing"]
    try:
        story, storyboard = story_paths(ep)
        data = read_json(path)
    except Exception as exc:
        return [str(exc)]
    return validate_payload(
        data,
        story_sha=sha256_file(story),
        storyboard_sha=sha256_file(storyboard),
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


def command_prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == ".py":
        return [sys.executable, str(codex)]
    if os.name == "nt" and codex.suffix.lower() in {".cmd", ".bat"}:
        return ["cmd.exe", "/d", "/c", str(codex)]
    return [str(codex)]


def critic_prompt(ep: Path, story: Path, storyboard: Path, candidate: Path, attempt: int) -> str:
    rel_ep = ep.relative_to(ROOT).as_posix()
    rel_story = story.relative_to(ROOT).as_posix()
    rel_board = storyboard.relative_to(ROOT).as_posix()
    rel_out = candidate.relative_to(ROOT).as_posix()
    return f"""You are an adversarial Story Critic in a fresh isolated session.
Do NOT rewrite the story. Do NOT score it politely. Your job is to find reasons it should NOT enter production.
Read:
- {rel_story}
- {rel_board}
- standards/制作规范_正式版.md
- standards/创作执行强制规范_V2.0.3.2.md
- standards/story_regressions/cases.json

This is critic attempt {attempt}. Ignore propagation scores and author self-evaluation.

Hard rules:
1. A viewer must be able to explain protagonist, why they are here, their personal stake, the ONE core anomaly rule, trigger, direct consequence, midpoint reframe, climax choice/cost, result and aftermath.
2. The main events must be explainable by one coherent underlying anomaly mechanism. If an object first returns by itself, later guides people, then suddenly "marks the next person" without one established rule explaining all three, mechanism_consistency=false.
3. Causality must read as reality goal -> rule/setup -> meaningful choice/violation -> direct consequence -> forced next action -> climax choice/cost -> result -> aftermath. A warning revealed only after the violation cannot retroactively create a meaningful choice unless the story established the rule another way.
4. "I found them", "the door opened", "the monster appeared", "the photo changed" are discoveries/setup, not a climax by themselves. The climax needs choice, cost, relationship change, rule payoff, identity turn or irreversible consequence.
5. The ending must recontextualize at least THREE concrete earlier facts. Introducing a brand-new anomaly behavior at the end is not payoff.
6. In any run of 5 storyboard frames, at least one frame must add new evidence, causal turn or cognitive upgrade. Apply the delete-frame test.
7. Perform a BLIND RETELL from your own understanding. If you need "maybe / perhaps / unclear" to explain the core mechanism or climax, clarity/mechanism_consistency must fail.
8. PASS only when every hard check is true and issue_codes is empty.

Write ONLY valid JSON to {rel_out}. Do not modify any other repository file.
Required JSON shape:
{{
  "contract": {{
    "protagonist": "...",
    "presence_reason": "...",
    "personal_stake": "...",
    "core_anomaly": "...",
    "rule": "...",
    "trigger": "...",
    "direct_consequence": "...",
    "midpoint_reframe": "...",
    "climax_choice": "...",
    "ending_recontextualization": ["earlier fact 1", "earlier fact 2", "earlier fact 3"]
  }},
  "blind_retell": {{
    "protagonist_and_reason": "...",
    "core_anomaly_rule": "...",
    "worsening_choice": "...",
    "climax_resolution": "...",
    "ending_reinterpretation": "..."
  }},
  "hard_checks": {{
    "clarity": true,
    "causal_chain": true,
    "mechanism_consistency": true,
    "motivation_stake": true,
    "trigger_consequence": true,
    "midpoint_reframe": true,
    "climax_payoff": true,
    "ending_payoff": true,
    "storyboard_information_gain": true,
    "delete_frame_test": true
  }},
  "issue_codes": [],
  "notes": ["specific evidence or failure notes"],
  "summary": {{"passed": true}}
}}
If any hard rule fails, set its boolean false, add specific codes such as STORY_COMPREHENSION_FAIL, CAUSAL_CHAIN_BROKEN, MECHANISM_CONTRADICTION, CLIMAX_DISCOVERY_ONLY, ENDING_PAYOFF_TOO_WEAK, STORYBOARD_STALL, and set summary.passed=false.
Episode: {rel_ep}
"""


def run_critic(ep: Path, *, attempt: int, codex_raw: str | None, timeout: int) -> int:
    if attempt not in {1, 2}:
        raise RuntimeError("attempt must be 1 or 2; only one automatic story revision is allowed")
    story, storyboard = story_paths(ep)
    before_story = sha256_file(story)
    before_board = sha256_file(storyboard)
    candidate = ep / CANDIDATE_REL
    candidate.unlink(missing_ok=True)

    codex = resolve_codex(codex_raw)
    cmd = command_prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        "-c", 'model_reasoning_effort="high"',
        "-s", "workspace-write", "-C", str(ROOT), "--json", "-"
    ]
    log = ep / "meta" / f"story-critic-attempt-{attempt}.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w", encoding="utf-8", newline="\n") as handle:
        completed = subprocess.run(
            cmd,
            input=critic_prompt(ep, story, storyboard, candidate, attempt),
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(f"isolated story critic failed rc={completed.returncode}; log={log}")
    if sha256_file(story) != before_story or sha256_file(storyboard) != before_board:
        raise RuntimeError("critic modified story/storyboard; isolated review is invalid")
    if not candidate.is_file():
        raise RuntimeError(f"critic did not produce {candidate}")

    data = read_json(candidate)
    data["schema_version"] = 1
    data["story_os_version"] = story_os_version()
    data["story_sha256"] = before_story
    data["storyboard_sha256"] = before_board
    data["revision_count"] = attempt - 1
    data["critic_provenance"] = {
        "runtime": "CODEX_ISOLATED",
        "isolated_session": True,
        "attempt": attempt,
        "reviewed_at": now(),
        "log": log.relative_to(ROOT).as_posix(),
    }
    errors = validate_payload(
        data,
        story_sha=before_story,
        storyboard_sha=before_board,
        version=story_os_version(),
    )
    final = ep / REVIEW_REL
    write_json(final, data)
    candidate.unlink(missing_ok=True)
    if errors:
        print("STORY SEMANTIC REVIEW FAIL")
        for error in errors:
            print("FAIL:", error)
        for code in data.get("issue_codes") or []:
            print("ISSUE:", code)
        return 2
    print("STORY SEMANTIC REVIEW PASS")
    return 0


def self_test() -> None:
    h = "a" * 64
    data = {
        "schema_version": 1,
        "story_os_version": story_os_version(),
        "story_sha256": h,
        "storyboard_sha256": h,
        "revision_count": 0,
        "critic_provenance": {"runtime": "CODEX_ISOLATED", "isolated_session": True, "attempt": 1},
        "contract": {key: "x" for key in CONTRACT_FIELDS},
        "blind_retell": {key: "x" for key in BLIND_FIELDS},
        "hard_checks": {key: True for key in HARD_CHECKS},
        "issue_codes": [],
        "summary": {"passed": True},
    }
    data["contract"]["ending_recontextualization"] = ["a", "b", "c"]
    assert validate_payload(data, story_sha=h, storyboard_sha=h, version=story_os_version()) == []
    data["hard_checks"]["mechanism_consistency"] = False
    assert any("mechanism_consistency" in x for x in validate_payload(data, story_sha=h, storyboard_sha=h, version=story_os_version()))
    print("STORY SEMANTIC REVIEW SELF-TEST PASS")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run-critic")
    p.add_argument("episode_dir")
    p.add_argument("--attempt", type=int, default=1)
    p.add_argument("--codex")
    p.add_argument("--timeout", type=int, default=900)
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
            print("STORY SEMANTIC REVIEW ERROR:", exc)
            return 3
    if args.cmd == "show":
        path = ep / REVIEW_REL
        print(path.read_text(encoding="utf-8") if path.is_file() else "{}")
        return 0
    errors = verify(ep)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2
    print("STORY SEMANTIC REVIEW VERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
