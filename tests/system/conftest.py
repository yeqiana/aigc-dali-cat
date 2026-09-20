"""Hermetic storage defaults for broad system tests.

Production defaults are MySQL/Redis/MySQL. Most system tests construct temporary
Episode trees and validate workflow semantics, so they must not accidentally
open developer/production services merely because the production defaults are
live. Tests that verify config defaults explicitly clear these overrides.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _hermetic_system_storage(monkeypatch):
    monkeypatch.setenv("STORYOS_RUNTIME_STORE_MODE", "jsonl")
    monkeypatch.setenv("STORYOS_EPISODE_META_STORE_MODE", "json")
    monkeypatch.setenv("STORYOS_HOT_STATE_MODE", "file")
