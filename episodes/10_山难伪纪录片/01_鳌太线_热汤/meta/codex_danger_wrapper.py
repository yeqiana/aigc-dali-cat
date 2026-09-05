#!/usr/bin/env python3
"""RETIRED episode-local Codex danger wrapper.

Historical execution logs referenced this path. It is intentionally inert now:
new execution must use the canonical runtime router and, if absolutely required,
`episodes/_system/codex_win_fullaccess.py` with explicit CODEX + full-access opt-in.
"""
from __future__ import annotations

import sys


def main() -> int:
    print(
        "RETIRED_CODEX_DANGER_WRAPPER: episode-local full-access wrappers are disabled; "
        "use explicit canonical CODEX runtime routing instead.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
