"""CODEX_MANAGED is whole-chain ownership, not just image generation."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import production_mode
import runtime_router


def _clean_env(monkeypatch):
    monkeypatch.delenv("STORY_OS_RUNTIME", raising=False)
    monkeypatch.delenv("STORY_OS_IMAGE_RUNTIME", raising=False)
    monkeypatch.delenv("STORY_OS_VISION_RUNTIME", raising=False)
    monkeypatch.delenv("STORY_OS_VISION_EXECUTOR", raising=False)
    monkeypatch.delenv("STORY_OS_IMAGE_EXECUTOR", raising=False)


def test_native_codex_manages_all_review_and_image_roles(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("STORY_OS_PRODUCTION_MODE", "CODEX_MANAGED")
    monkeypatch.setenv("STORY_OS_IMAGE_EXECUTOR", "CODEX")
    assert production_mode.resolve()["effective_runtime"] == "CODEX"
    assert runtime_router.text_review_runtime() == ("CODEX", "production.mode=CODEX_MANAGED")
    assert runtime_router.governance_review_runtime() == ("CODEX", "production.mode=CODEX_MANAGED")
    assert runtime_router.vision_review_runtime()[0] == "CODEX"
    assert runtime_router.image_execution_runtime()[0] == "CODEX"
    assert runtime_router.local_codex_allowed()
    assert runtime_router.local_codex_vision_allowed()
    assert runtime_router.local_codex_image_allowed()


def test_collaborative_reviews_preserve_work_owner(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("STORY_OS_PRODUCTION_MODE", "COLLABORATIVE")
    assert runtime_router.text_review_runtime()[0] == "WORK"
    assert runtime_router.governance_review_runtime()[0] == "WORK"
    assert production_mode.resolve()["effective_runtime"] == "WORK"


def test_legacy_runtime_override_cannot_grant_codex_managed_reviews(monkeypatch):
    _clean_env(monkeypatch)
    monkeypatch.setenv("STORY_OS_PRODUCTION_MODE", "COLLABORATIVE")
    monkeypatch.setenv("STORY_OS_RUNTIME", "CODEX")
    assert runtime_router.text_review_runtime()[0] == "WORK"
    assert runtime_router.governance_review_runtime()[0] == "WORK"
    assert production_mode.resolve()["effective_runtime"] == "WORK"


@pytest.mark.parametrize("value", ["invalid", "WORK", "WEB"])
def test_native_mode_never_silently_downgrades_to_host_runtime(monkeypatch, value):
    _clean_env(monkeypatch)
    monkeypatch.setenv("STORY_OS_PRODUCTION_MODE", "CODEX_MANAGED")
    monkeypatch.setenv("STORY_OS_RUNTIME", value)
    assert runtime_router.text_review_runtime()[0] == "CODEX"
    assert runtime_router.governance_review_runtime()[0] == "CODEX"
