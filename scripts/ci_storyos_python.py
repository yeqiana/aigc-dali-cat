#!/usr/bin/env python3
"""CI-only Python entrypoint for the StoryOS 'platform' package collision.

StoryOS uses a package named platform.repository. Ordinary Python has its own
stdlib 'platform' module (not a package). A direct sys.path/PYTHONPATH tweak can
either break 'platform.repository' or make stdlib clients like uuid fail when
they call platform.system().

This shim imports the genuine stdlib module FIRST, then grants it a search path
for StoryOS's repository subpackage. No production runtime or model dispatch is
started here. A CI subprocess gets a fresh interpreter for each invocation.

Usage: python scripts/ci_storyos_python.py [-m module | script.py] [args...]
"""
from __future__ import annotations

import os
import platform as stdlib_platform
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "platform"

if not PACKAGE.is_dir() or not (PACKAGE / "repository").is_dir():
    raise SystemExit("STORYOS_CI_PLATFORM_PACKAGE_MISSING")

# Keep stdlib platform.system/platform.python_version available to libraries.
# Extending __path__ only gives Python a way to resolve platform.repository.*.
stdlib_platform.__path__ = [str(PACKAGE)]
# Propagate CI-only startup intent to known child-script launchers.
os.environ['STORYOS_CI_PYTHON_BOOTSTRAP'] = '1'
sys.path.insert(0, str(ROOT))


def main() -> int:
    arguments = sys.argv[1:]
    if not arguments:
        raise SystemExit("usage: ci_storyos_python.py [-m module | script.py] [args]")

    if arguments[0] == "-m":
        if len(arguments) < 2 or arguments[1].startswith("-"):
            raise SystemExit("STORYOS_CI_INVALID_MODULE")
        sys.argv = [arguments[1], *arguments[2:]]
        runpy.run_module(arguments[1], run_name="__main__", alter_sys=True)
        return 0

    if arguments[0].startswith("-"):
        raise SystemExit("STORYOS_CI_INVALID_SCRIPT")

    script = Path(arguments[0]).resolve()
    if not script.is_file() or not script.is_relative_to(ROOT):
        raise SystemExit("STORYOS_CI_SCRIPT_OUTSIDE_WORKSPACE")
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *arguments[1:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
