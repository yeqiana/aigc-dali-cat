#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Asset boundary validation.

Production media and test/demo assets must stay isolated.
This gate is intentionally non-destructive: it only reports violations.
"""
from __future__ import annotations

from pathlib import Path


TEST_ROOTS = (
    "assets/placeholders/",
    "assets/fixtures/",
    "assets/demo/",
)

PRODUCTION_ROOTS = (
    "/media/raw/",
    "/media/candidates/",
    "./media/approved/",
    "./media/publish/",
)


def is_test_asset(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(root) for root in TEST_ROOTS)


def check_asset_path(path: str) -> list[str]:
    """Return violations without modifying files."""
    normalized = path.replace("\\", "/")
    errors: list[str] = []

    if is_test_asset(normalized) and "/media/" in normalized:
        errors.append("placeholder/test asset cannot enter production media")

    if any(root in normalized for root in PRODUCTION_ROOTS):
        if is_test_asset(normalized):
            errors.append("production asset references test boundary")

    return errors


def classify(path: str) -> str:
    if is_test_asset(path):
        return "TEST_ASSET"
    return "PRODUCTION_OR_UNKNOWN"


def self_test() -> None:
    assert classify("assets/placeholders/demo.png") == "TEST_ASSET"
    assert not check_asset_path("assets/placeholders/demo.png")
    assert check_asset_path("assets/placeholders/demo.png/media/raw/x.png")
    print("ASSET BOUNDARY GATE SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
