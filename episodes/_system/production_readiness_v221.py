#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS V2.2.1 pre-generation readiness gate."""
from __future__ import annotations

import argparse
from pathlib import Path

import world_identity_contract
import character_appearance_anchor
import visual_narrative_core_v22
import frame_contract


def verify(ep: Path, stage: str) -> list[str]:
    ep = Path(ep).resolve()
    errors = []
    if not world_identity_contract.required(ep):
        return []

    errors.extend(world_identity_contract.verify(ep))
    errors.extend(character_appearance_anchor.verify(ep))
    errors.extend(visual_narrative_core_v22.verify_all(ep))

    if stage == "production":
        errors.extend(frame_contract.verify_all(ep))
        if not errors:
            try:
                row = frame_contract.compile_frame(
                    ep, 1, write_cache=False
                )
                hm = row.get("hash_material") or {}
                prompt = row.get("prompt_contract") or ""
                for key in (
                    "world_identity",
                    "world_identity_sha256",
                    "character_appearance_anchor",
                    "character_appearance_anchor_sha256",
                ):
                    if key not in hm:
                        errors.append(
                            f"V221_FRAME_CONTRACT_BINDING_MISSING:{key}"
                        )
                for marker in (
                    "[WORLD IDENTITY V2.2.1]",
                    "[CHARACTER APPEARANCE ANCHOR V2.2.1]",
                ):
                    if marker not in prompt:
                        errors.append(
                            f"V221_FRAME_PROMPT_BINDING_MISSING:{marker}"
                        )
            except Exception as exc:
                errors.append(f"V221_FRAME_CONTRACT_PROBE_FAIL:{exc}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("episode_dir")
    ap.add_argument(
        "--stage",
        choices=["preimage", "production"],
        default="preimage",
    )
    args = ap.parse_args()
    errors = verify(Path(args.episode_dir), args.stage)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 2

    if args.stage == "production":
        print(
            "V2.2.1 PRODUCTION READINESS PASS | "
            "world_identity=PASS character_anchor=PASS "
            "visual_narrative=PASS frame_binding=PASS"
        )
    else:
        print(
            "V2.2.1 PREIMAGE READINESS PASS | "
            "world_identity=PASS character_anchor=PASS "
            "visual_narrative=PASS"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
