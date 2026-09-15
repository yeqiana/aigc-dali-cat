from __future__ import annotations

import fnmatch
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"


def test_formal_review_modules_are_not_classified_as_legacy():
    index = json.loads((SYSTEM / "MODULE_INDEX.json").read_text(encoding="utf-8"))
    formal = index["formal_review"]
    patterns = index["legacy_or_migration_patterns"]
    assert "visual_lock_v21.py" in formal
    assert "incremental_frame_review.py" in formal
    assert "*_v21*.py" not in patterns
    conflicts = [
        (name, pattern)
        for name in formal
        for pattern in patterns
        if fnmatch.fnmatch(name, pattern)
    ]
    assert conflicts == []


def test_start_here_declares_three_locks_and_repair_as_scope_authorization():
    text = (ROOT / "START_HERE.md").read_text(encoding="utf-8")
    assert "三个正式人工锁点 + 返修范围授权" in text
    assert "**Repair Lock**" not in text
    assert "返修不是第四个 Lock" in text
    assert "repair authorization / reopen lane" in text


def test_legacy_notify_hook_has_no_production_consumer():
    for name in (
        "codex_subscription_image.py",
        "codex_user_runner.py",
        "scoped_codex_worker.py",
        "codex_auto_orchestrator.py",
    ):
        text = (SYSTEM / name).read_text(encoding="utf-8-sig")
        assert "legacy_notify" not in text
