#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import visual_narrative_core_v22 as core


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        legacy = root / "legacy"
        legacy.mkdir()
        a = core.activation(legacy)
        assert a["active"] is False
        assert core.required(legacy) is False

        formal = root / "formal"
        write(
            formal / "meta/episode-state.json",
            {"tool_version": "2.2.0"},
        )
        af = core.activation(formal)
        assert af["active"] is True
        assert af["formal"] is True
        assert core.required(formal) is True
        assert any(
            "VISUAL_NARRATIVE_INPUT_MISSING" in x
            for x in core.activation_errors(formal)
        )

        regression = root / "regression"
        write(
            regression / "meta/visual-narrative-core.json",
            {
                "enabled": True,
                "mode": "regression",
                "contract_version": "2.2.0",
                "authority": "NON_AUTHORITY_REGRESSION_ONLY",
                "input_path": (
                    "meta/tests/visual-narrative-regression/"
                    "shot-progression-review.json"
                ),
            },
        )
        ar = core.activation(regression)
        assert ar["active"] is True
        assert ar["formal"] is False
        assert core.required(regression) is False
        assert core.regression_active(regression) is True

    print("V2.2 R2 ACTIVATION LEGACY SELF-TEST PASS")


if __name__ == "__main__":
    main()
