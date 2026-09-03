#!/usr/bin/env python3
from __future__ import annotations
import image_provider_runtime

def select_for_batch(count: int, *, has_references: bool) -> dict:
    decision = image_provider_runtime.select_batch_provider(count)
    decision["has_references"] = bool(has_references)
    decision["route_is_stage_authority"] = False
    return decision

def self_test() -> None:
    snap = image_provider_runtime.capability_snapshot()
    assert snap["secret_values_persisted"] is False
    print("IMAGE PROVIDER ROUTER V2.4.1 SELF-TEST PASS")

if __name__ == "__main__":
    self_test()
