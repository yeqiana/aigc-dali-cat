#!/usr/bin/env python3
"""RETIRED temporary Codex shim.

Kept only because older Git history referenced this tracked path. New Story OS
runtime code must not call it. Use explicit CODEX runtime routing instead.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "RETIRED_CODEX_SHIM: use STORY_OS_RUNTIME=CODEX and the canonical runtime router; "
        "this temporary shim no longer delegates to a user-specific codex.exe path.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
