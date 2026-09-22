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

    assert core._owner_class({"pov_mode": "ground_phone"}) == "diegetic_device_camera"
    assert core._camera_owner({"pov_mode": "ground_phone"}, {"photographer_id": "P01"}) == "P01_phone"
    impossible = {
        "pov_mode": "dropping_phone",
        "primary_subject": "P01手与正在下落的手机",
        "camera_position": "手机离手后的倾斜下落机位",
        "action": "P01松手",
        "capture_purpose": "记录动作",
        "visual_function": "选择反转",
        "new_information": True,
    }
    assert any("SELF_CAMERA_VISIBLE" in x for x in core._camera_authorship_errors(root, 17, impossible))

    print("V2.2 R2 ACTIVATION LEGACY SELF-TEST PASS")


if __name__ == "__main__":
    main()
