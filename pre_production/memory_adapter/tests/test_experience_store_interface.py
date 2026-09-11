#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Experience Store interface and backward-compatibility tests.

The design phase ships contracts and signatures, not a database. These tests
pin the interface shape, prove it is implementable without shipping storage,
and confirm the existing Memory Adapter behaviour is unchanged.
"""
from __future__ import annotations

import inspect
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pre_production.memory_adapter import DEFAULT_STORE_DIR, MemoryAdapter  # noqa: E402
from pre_production.memory_adapter.experience_store import (  # noqa: E402
    ExperienceStoreRepository,
    build_experience_record,
)
from pre_production.story_dna.validator import validate_review_reference  # noqa: E402

INTERFACE_METHODS = ("save_experience", "get_related_experience", "query_pattern")


class _InMemoryStub(ExperienceStoreRepository):
    """Minimal test-local stub: proves the interface is implementable without a database."""

    def __init__(self):
        self.records: list = []

    def save_experience(self, record: dict) -> dict:
        self.records.append(record)
        return {"status": "SAVED", "experience_id": record.get("experience_id"),
                "stored": len(self.records)}

    def get_related_experience(self, *, story_dna=None, episode_id=None, limit=None) -> list:
        found = [r for r in self.records if episode_id is None or r.get("episode_id") == episode_id]
        return found if limit is None else found[:limit]

    def query_pattern(self, *, risk_type=None, tokens=(), limit=None) -> list:
        return []


class ExperienceStoreInterfaceTests(unittest.TestCase):
    def test_interface_declares_exactly_three_abstract_methods(self):
        self.assertEqual(ExperienceStoreRepository.__abstractmethods__, frozenset(INTERFACE_METHODS))

    def test_interface_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            ExperienceStoreRepository()

    def test_signatures_are_stable(self):
        save = inspect.signature(ExperienceStoreRepository.save_experience)
        self.assertEqual(list(save.parameters), ["self", "record"])

        related = inspect.signature(ExperienceStoreRepository.get_related_experience)
        self.assertEqual(list(related.parameters), ["self", "story_dna", "episode_id", "limit"])
        for name in ("story_dna", "episode_id", "limit"):
            self.assertEqual(related.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY)

        pattern = inspect.signature(ExperienceStoreRepository.query_pattern)
        self.assertEqual(list(pattern.parameters), ["self", "risk_type", "tokens", "limit"])
        for name in ("risk_type", "tokens", "limit"):
            self.assertEqual(pattern.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_the_interface_exposes_no_rule_editing_entry_point(self):
        banned = ("update_rule", "set_weight", "edit_lexicon", "learn", "train",
                  "build_report", "assess_risk", "decide")
        members = set(dir(ExperienceStoreRepository))
        for name in banned:
            self.assertNotIn(name, members)

    def test_read_methods_return_candidates_only(self):
        stub = _InMemoryStub()
        record = build_experience_record(episode_id="10-03", observation_reference="OBS-1")
        stub.save_experience(record)
        found = stub.get_related_experience(episode_id="10-03")
        self.assertEqual(found, [record])
        self.assertEqual(stub.get_related_experience(episode_id="99-99"), [])
        self.assertEqual(stub.query_pattern(tokens=("fog",)), [])


class MemoryAdapterBackwardCompatibilityTests(unittest.TestCase):
    def test_existing_exports_are_unchanged(self):
        self.assertTrue(issubclass(MemoryAdapter, object))
        self.assertEqual(DEFAULT_STORE_DIR, "reports/pre-production")

    def test_existing_read_write_surface_is_intact(self):
        for name in ("history", "list_review_references", "read_review_reference",
                     "build_review_reference", "save_review_reference"):
            self.assertTrue(hasattr(MemoryAdapter, name), name)
        params = inspect.signature(MemoryAdapter.save_review_reference).parameters
        self.assertEqual(list(params), ["self", "advisor_report", "creator_decision",
                                        "feedback", "final_result"])

    def test_review_reference_still_validates_after_the_new_interface(self):
        report = {"report_id": "PPA-10-03-deadbeef", "episode_id": "10-03",
                  "decision": "WARNING"}
        with tempfile.TemporaryDirectory(prefix="pp-memory-") as tmp:
            adapter = MemoryAdapter(repo_root=tmp, store_dir=Path(tmp) / "store")
            path = adapter.save_review_reference(report, creator_decision="accepted")
            self.assertTrue(path.is_file())
            self.assertEqual(validate_review_reference(adapter.read_review_reference(path.stem)), [])
            self.assertEqual(adapter.list_review_references(), [path])

    def test_memory_adapter_is_not_the_experience_store(self):
        self.assertFalse(issubclass(MemoryAdapter, ExperienceStoreRepository))


if __name__ == "__main__":
    unittest.main()
