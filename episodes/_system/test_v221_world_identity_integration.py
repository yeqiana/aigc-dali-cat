#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import world_identity_contract as world
import character_appearance_anchor as anchor
import frame_semantic_review
import visual_lock_v21


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td) / "episode"
        write(
            ep / "meta/episode-state.json",
            {"tool_version": "2.2.1"},
        )
        write(
            ep / "meta/character-contract.json",
            {
                "status": "LOCKED",
                "cast": {
                    "members": [
                        {
                            "id": "P01",
                            "gender": "male",
                            "age": 24,
                            "build": "普通年轻人体型",
                            "hair": "普通黑色日常发型",
                            "clothing_anchor": "黑色T恤",
                            "device_anchor": "智能手机",
                        }
                    ]
                },
            },
        )
        write(
            ep / "meta/character-visual-contract.json",
            {
                "status": "LOCKED",
                "members": {
                    "P01": {
                        "visual_priority": "primary",
                        "body_build": "lean_proportionate_natural",
                        "face_identity": {
                            "original_character": True,
                            "independently_distinct_face": True,
                            "reference_similarity_target": "low",
                        },
                        "hair": {
                            "haircut_anchor": "short black crop",
                            "hair_length_anchor": "short",
                            "allowed_state_variation": [
                                "wet",
                                "messy",
                            ],
                        },
                        "presentation": {
                            "camera_friendly_but_believable": True
                        },
                    }
                },
            },
        )

        assert world.required(ep)
        effective = world.effective(ep)
        assert effective["world"]["country"] == "China"
        assert (
            effective["population"]["nationality_context"]
            == "Chinese"
        )

        built = anchor.build(ep, write=True)
        assert built["members"]["P01"]["nationality_context"] == "Chinese"
        assert anchor.verify(ep) == []

        # Version gating: 2.2.0 remains unaffected by 2.2.1-only pixel checks.
        assert "world_identity_fidelity" not in frame_semantic_review.checks_for_version("2.2.0")
        assert "world_identity_fidelity" in frame_semantic_review.checks_for_version("2.2.1")
        assert "world_identity_fidelity" not in visual_lock_v21.checks_for_version("2.2.0")
        assert "world_identity_fidelity" in visual_lock_v21.checks_for_version("2.2.1")

    print("V2.2.1 WORLD IDENTITY / CONTINUITY INTEGRATION TEST PASS")


if __name__ == "__main__":
    main()
