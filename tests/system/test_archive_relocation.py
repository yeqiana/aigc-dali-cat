#!/usr/bin/env python3
"""Archive Relocation Manifest tests.

The EP003 Production Exposure Audit found that when an Episode is physically
moved into episodes/_archive/, its frozen evidence keeps repository-relative
paths pointing at the pre-move location. artifacts.story then cannot be
resolved, so Story Lock / Visual Lock / reference / production evidence stops
being verifiable even though the bytes survived.

These tests lock the additive repair:

  Case1: build entry -> prefix map + relocated anchors               -> PASS
  Case2: moved bytes drift after relocation                          -> FAIL
  Case3: anchor file missing                                         -> FAIL
  Case4: no archived_from / no prefix map                            -> FAIL
  Case5: a path that still exists in place resolves directly         -> direct
  Case6: the real EP003 archive resolves and matches its manifest    -> PASS

The registry is evidence only. It never rewrites the archived Episode, the
Runtime, the machine gate or the production flow; unresolved free-text
references are advisory, only the declared anchors fail closed.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import archive_relocation  # noqa: E402

FROM_DIR = "episodes/10_demo/03_demo"
EP_NAME = "20260911_EP099_abandoned_demo"
TO_DIR = "episodes/_archive/" + EP_NAME
STORY_REL = FROM_DIR + "/docs/story.md"
STORY_BYTES = b"story-lock-v1\n"
MANIFEST_REL = "episodes/_archive/manifest.txt"
WRITTEN_AT = "2026-09-11T00:00:00+08:00"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


class ArchiveFixture:
    """A relocated Episode tree inside one temp repository root."""

    def __init__(self, tmp):
        self.root = Path(tmp)
        self.ep = self.root / TO_DIR
        (self.ep / "docs").mkdir(parents=True)
        (self.ep / "meta").mkdir(parents=True)
        self.story = self.ep / "docs/story.md"
        self.story.write_bytes(STORY_BYTES)
        write_json(self.ep / "meta/release-manifest.json", {"artifacts": {"story": STORY_REL}})
        write_json(self.ep / "meta/story-gates.json", {"story": {"hook_frames": [1]}})
        write_json(self.root / "episodes/_archive/.storyos-non-episode.json", {
            "schema_version": 1,
            "non_episode": True,
            "kind": "abandoned_episode_archive",
            "archived_at": "2026-09-11",
            "archived_from": FROM_DIR,
            "reason": "test fixture",
            "manifest": MANIFEST_REL,
        })
        self.write_manifest()

    def anchor_rels(self):
        return ("docs/story.md", "meta/release-manifest.json", "meta/story-gates.json")

    def write_manifest(self, override=None):
        override = override or {}
        lines = ["# test archive manifest"]
        for rel in self.anchor_rels():
            payload = (self.ep / rel).read_bytes()
            digest = override.get(rel) or sha256_bytes(payload)
            lines.append(digest + "  " + str(len(payload)) + "  " + rel)
        (self.root / MANIFEST_REL).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def build(self):
        return archive_relocation.build_entry(self.root, self.ep, written_at=WRITTEN_AT)


def codes(findings):
    return [code for code, _ in findings]


class ArchiveRelocationVerifyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = ArchiveFixture(self.tmp.name)

    def test_case1_relocated_anchors_resolve_and_verify(self):
        entry = self.fx.build()
        self.assertEqual(entry["from"], FROM_DIR)
        self.assertEqual(entry["to"], TO_DIR)
        self.assertEqual(entry["prefix_map"], [{"from": FROM_DIR + "/", "to": TO_DIR + "/"}])
        story = next(a for a in entry["anchors"] if a["name"] == "story")
        self.assertEqual(story["status"], "relocated")
        self.assertEqual(story["resolved_path"], TO_DIR + "/docs/story.md")
        self.assertEqual(story["sha256"], sha256_bytes(STORY_BYTES))
        self.assertEqual(archive_relocation.verify(self.fx.root, entry), [])

    def test_case2_hash_drift_fails(self):
        entry = self.fx.build()
        self.fx.story.write_bytes(b"story-lock-v2\n")
        self.assertIn("anchor_hash_drift", codes(archive_relocation.verify(self.fx.root, entry)))

    def test_case3_missing_anchor_fails(self):
        entry = self.fx.build()
        self.fx.story.unlink()
        self.assertIn("anchor_unresolved", codes(archive_relocation.verify(self.fx.root, entry)))

    def test_case4_missing_prefix_map_fails(self):
        write_json(self.fx.root / "episodes/_archive/.storyos-non-episode.json", {
            "schema_version": 1, "non_episode": True, "kind": "abandoned_episode_archive",
            "archived_at": "2026-09-11",
        })
        entry = self.fx.build()
        self.assertEqual(entry["prefix_map"], [])
        self.assertIn("relocation_prefix_missing", codes(archive_relocation.verify(self.fx.root, entry)))

    def test_case5_direct_path_wins_over_prefix_remap(self):
        in_place = self.fx.root / STORY_REL
        in_place.parent.mkdir(parents=True, exist_ok=True)
        in_place.write_bytes(STORY_BYTES)
        entry = self.fx.build()
        resolved = archive_relocation.resolve_ref(self.fx.root, STORY_REL, entry)
        self.assertEqual(resolved["status"], "direct")
        self.assertEqual(resolved["path"], STORY_REL)

    def test_prefix_map_mismatch_fails(self):
        entry = self.fx.build()
        entry["prefix_map"][0]["to"] = "episodes/_archive/other/"
        self.assertIn("prefix_map_mismatch", codes(archive_relocation.verify(self.fx.root, entry)))

    def test_archive_dir_missing_fails(self):
        entry = self.fx.build()
        entry["to"] = "episodes/_archive/does_not_exist"
        self.assertIn("archive_dir_missing", codes(archive_relocation.verify(self.fx.root, entry)))

    def test_unsupported_schema_fails(self):
        entry = self.fx.build()
        entry["schema_version"] = 99
        self.assertIn("relocation_schema_unsupported", codes(archive_relocation.verify(self.fx.root, entry)))

    def test_file_manifest_hash_mismatch_fails(self):
        entry = self.fx.build()
        self.fx.write_manifest(override={"docs/story.md": "0" * 64})
        self.assertIn("file_manifest_hash_mismatch", codes(archive_relocation.verify(self.fx.root, entry)))

    def test_reference_scan_is_advisory_only(self):
        entry = self.fx.build()
        scan = archive_relocation.scan_references(self.fx.root, self.fx.ep, entry)
        counts = scan["counts"]
        self.assertEqual(counts["total"], counts["direct"] + counts["relocated"] + counts["unresolved"])
        self.assertGreaterEqual(counts["relocated"], 1)
        self.assertEqual(archive_relocation.verify(self.fx.root, entry), [])


class ArchiveRelocationRegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = ArchiveFixture(self.tmp.name)

    def test_upsert_is_idempotent_and_lookup_matches(self):
        entry = self.fx.build()
        archive_relocation.upsert_entry(self.fx.root, entry)
        archive_relocation.upsert_entry(self.fx.root, entry)
        self.assertEqual(len(archive_relocation.registry(self.fx.root)), 1)
        found = archive_relocation.entry_for(self.fx.root, self.fx.ep)
        self.assertEqual(found["to"], TO_DIR)

    def test_entry_for_ref_matches_new_prefix(self):
        entry = self.fx.build()
        archive_relocation.upsert_entry(self.fx.root, entry)
        found = archive_relocation.entry_for_ref(self.fx.root, STORY_REL)
        self.assertIsNotNone(found)
        self.assertEqual(found["to"], TO_DIR)

    def test_registry_round_trips_utf8_paths(self):
        entry = self.fx.build()
        entry["to"] = "episodes/_archive/20260911_EP099_abandoned_中文目录"
        archive_relocation.upsert_entry(self.fx.root, entry)
        raw = (self.fx.root / "episodes/_archive/relocations.json").read_text(encoding="utf-8")
        self.assertIn("中文目录", raw)
        self.assertEqual(archive_relocation.registry(self.fx.root)[0]["to"], entry["to"])


class RealArchiveRegressionTest(unittest.TestCase):
    """Case6: the shipped EP003 archive is the reason this module exists."""

    def test_ep003_relocation_entry_verifies(self):
        archived = sorted((ROOT / "episodes/_archive").glob("*EP003*"))
        if not archived:
            self.skipTest("EP003 archive not present in this checkout")
        entry = archive_relocation.entry_for(ROOT, archived[0])
        if entry is None:
            self.skipTest("EP003 relocation entry not registered")
        self.assertEqual(entry["from"], "episodes/10_彼此的天上/03_雾中的另一座生活区")
        self.assertEqual(archive_relocation.verify(ROOT, entry), [])
        story = next(a for a in entry["anchors"] if a["name"] == "story")
        self.assertEqual(story["status"], "relocated")
        target = ROOT / story["resolved_path"]
        self.assertTrue(target.is_file())
        self.assertEqual(archive_relocation.sha256_file(target), story["sha256"])
        manifest = archive_relocation.file_manifest_hashes(ROOT, entry)
        rel_in_ep = target.relative_to(archived[0]).as_posix()
        self.assertEqual(manifest.get(rel_in_ep), story["sha256"])

    def test_registry_only_lists_archived_episodes(self):
        for entry in archive_relocation.registry(ROOT):
            self.assertTrue(str(entry.get("to") or "").startswith("episodes/_archive/"))
            self.assertTrue((ROOT / str(entry.get("to"))).is_dir())


class ReferenceTokenTest(unittest.TestCase):
    """normalize_ref clips a token glued to CJK prose, keeps path periods."""

    def test_cjk_sentence_punctuation_clips_trailing_prose(self):
        self.assertEqual(
            archive_relocation.normalize_ref("episodes/a/b/series.json。Frame01"),
            "episodes/a/b/series.json",
        )

    def test_backticks_and_quotes_are_delimiters(self):
        self.assertEqual(
            archive_relocation.normalize_ref("见 `episodes/a/b/c.yaml` 一节"),
            "episodes/a/b/c.yaml",
        )
        self.assertEqual(
            archive_relocation.normalize_ref('"episodes/a/b/c.yaml"'),
            "episodes/a/b/c.yaml",
        )

    def test_trailing_ascii_period_is_trimmed(self):
        self.assertEqual(archive_relocation.normalize_ref("episodes/a/b.md."), "episodes/a/b.md")

    def test_non_repo_string_yields_none(self):
        self.assertIsNone(archive_relocation.normalize_ref("no path here"))


if __name__ == "__main__":
    unittest.main()
