#!/usr/bin/env python3
"""CI-only strict Episode baseline comparator, with no production database access.

Both official --all --metadata-only validators run unchanged. Pre-existing
failures are recorded as auditable debt against the exact pre-integration
commit, while new failures, removed checked Episodes or crashes fail CI.
This does not grant production/release authority to any Episode.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "ea6f917d9bcab208293beb7153759f7b45589480"
BASELINE = ROOT / "tests" / "baselines" / "storyos_episode_debt_ea6f917.json"
VALIDATORS = ("validate_episode.py", "machine_gate.py")
# Bootstrap the true stdlib platform before augmenting the package lookup.
BOOTSTRAP = """
import os,platform,runpy,sys
from pathlib import Path
root=Path.cwd().resolve()
platform.__path__=[str(root/'platform')]
sys.path[:0]=[str(root/'episodes'/'_system'),str(root)]
script=root/'episodes'/'_system'/sys.argv[1]
sys.argv=[str(script),'--all','--metadata-only']
runpy.run_path(str(script),run_name='__main__')
"""
HEADER = re.compile(r"^=== (?:PASS|FAIL)(?: MACHINE GATE [A-Z_]+ ::)? (.*?) ===$")


def _git_head(root: Path) -> str:
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def _record(root: Path, script: str) -> dict:
    env = dict(os.environ)
    env.update({
        "PYTHONUTF8": "1",
        "STORYOS_EPISODE_META_STORE_MODE": "json",
        "STORYOS_HOT_STATE_MODE": "file",
        "STORYOS_MYSQL_HOST": "127.0.0.1",
        "STORYOS_MYSQL_PORT": "1",
    })
    # This interpreter is deliberately offline. No mock PASS records are written.
    proc = subprocess.run([sys.executable, "-c", BOOTSTRAP, script],
                          cwd=root, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=150)
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"{script} crashed (rc={proc.returncode}): {proc.stderr[-1200:]}")
    checked: set[str] = set()
    errors: Counter[str] = Counter()
    current = None
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        header = HEADER.match(line)
        if header:
            absolute = header.group(1).strip()
            try:
                relative = Path(absolute).resolve().relative_to(root.resolve()).as_posix()
            except ValueError as exc:
                raise RuntimeError(f"validator inspected outside checkout: {absolute}") from exc
            current = relative
            checked.add(relative)
        elif line.startswith("[FAIL]"):
            if current is None:
                raise RuntimeError(f"{script} emitted an unscoped failure: {line}")
            # Report messages may include the checkout's absolute path.
            normalized = line.replace(str(root), "<CHECKOUT>")
            normalized = normalized.replace(str(root.resolve()), "<CHECKOUT>")
            normalized = normalized.replace("\\", "/")
            errors[f"{current} | {normalized}"] += 1
    if not checked:
        raise RuntimeError(f"{script} did not enumerate any Episode")
    if (proc.returncode != 0) != bool(errors):
        raise RuntimeError(f"{script} exit/failure mismatch (rc={proc.returncode}, errors={sum(errors.values())})")
    return {
        "checked_episodes": sorted(checked),
        "failures": dict(sorted(errors.items())),
        "failure_count": sum(errors.values()),
        "strict_exit_code": proc.returncode,
    }


def snapshot(root: Path) -> dict:
    return {
        "schema_version": 1,
        "baseline_commit": BASE_SHA,
        "policy": "historical_failure_debt_only; no new failures or omitted Episodes",
        "validators": {name: _record(root, name) for name in VALIDATORS},
    }


def check() -> int:
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if baseline.get("baseline_commit") != BASE_SHA or baseline.get("schema_version") != 1:
        raise RuntimeError("unrecognized pinned baseline manifest")
    changed = False
    for name in VALIDATORS:
        old = baseline["validators"][name]
        new = _record(ROOT, name)
        missing = sorted(set(old["checked_episodes"]) - set(new["checked_episodes"]))
        novel_episodes = sorted(set(new["checked_episodes"]) - set(old["checked_episodes"]))
        old_issues = Counter(old["failures"])
        new_issues = Counter(new["failures"])
        extra = new_issues - old_issues
        print(f"{name}: strict_rc={new['strict_exit_code']}, "
              f"checked={len(new['checked_episodes'])}, "
              f"preexisting_failures={sum(old_issues.values())}, "
              f"current_failures={sum(new_issues.values())}, "
              f"new_failures={sum(extra.values())}")
        for episode in sorted({row.split(" | ", 1)[0] for row in new_issues}):
            print(f"  HISTORICAL_UNRESOLVED: {episode}")
        if missing or novel_episodes or extra:
            changed = True
            print(f"  BLOCKED: omitted={missing} added={novel_episodes}")
            for issue, count in extra.most_common(18):
                print(f"  NEW_FAILURE x{count}: {issue}")
    if changed:
        print("FAIL: strict Episode metadata baseline regressed; no production promotion.")
        return 1
    print("PASS: no NEW Episode metadata/Review regression against pinned ea6f917.")
    print("NOTE: historical failures remain unresolved and do NOT grant PUBLISH_READY.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("snapshot", "check"))
    parser.add_argument("--baseline-root", type=Path)
    args = parser.parse_args()
    if args.command == "check":
        return check()
    if args.baseline_root is None:
        raise SystemExit("--baseline-root is required for snapshot")
    root = args.baseline_root.resolve()
    if _git_head(root) != BASE_SHA:
        raise RuntimeError("baseline snapshot requires the exact pinned pre-integration commit")
    data = snapshot(root)
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"baseline captured: {[(k, v['failure_count']) for k, v in data['validators'].items()]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
