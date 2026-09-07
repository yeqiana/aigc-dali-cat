#!/usr/bin/env python3
from __future__ import annotations

import codecs
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_json


class StoryJsonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="story-json-test-")
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_roundtrip_unicode_and_encoding(self):
        p = self.dir / "a.json"
        payload = {"t": "墨脱·修行洞窟", "n": 2, "ratio": "4:5"}
        story_json.write_json(p, payload)
        self.assertEqual(story_json.read_json(p), payload)
        raw = p.read_bytes()
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        self.assertIn("墨脱·修行洞窟".encode("utf-8"), raw)

    def test_read_tolerates_bom_and_plain_utf8(self):
        payload = {"ok": True}
        bom = self.dir / "bom.json"
        bom.write_bytes(codecs.BOM_UTF8 + json.dumps(payload).encode("utf-8"))
        plain = self.dir / "plain.json"
        plain.write_bytes(json.dumps(payload).encode("utf-8"))
        self.assertEqual(story_json.read_json(bom), payload)
        self.assertEqual(story_json.read_json(plain), payload)

    def test_strict_missing_raises(self):
        with self.assertRaises(FileNotFoundError):
            story_json.read_json(self.dir / "missing.json")

    def test_lenient_missing_returns_default(self):
        self.assertEqual(story_json.read_json(self.dir / "missing.json", default={}), {})

    def test_lenient_bad_json_and_non_object_return_default(self):
        bad = self.dir / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        self.assertEqual(story_json.read_json(bad, default=None), None)
        arr = self.dir / "arr.json"
        arr.write_text("[1,2,3]", encoding="utf-8")
        self.assertEqual(story_json.read_json(arr, default={}), {})

    def test_strict_bad_json_raises(self):
        bad = self.dir / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            story_json.read_json(bad)

    def test_strict_non_object_raises_unless_opted_out(self):
        arr = self.dir / "arr.json"
        arr.write_text("[1,2,3]", encoding="utf-8")
        with self.assertRaises(ValueError):
            story_json.read_json(arr)
        self.assertEqual(story_json.read_json(arr, require_object=False), [1, 2, 3])

    def test_write_creates_parents_and_leaves_no_tmp(self):
        p = self.dir / "deep" / "nested" / "state.json"
        story_json.write_json(p, {"x": 1})
        self.assertTrue(p.is_file())
        leftovers = [x.name for x in p.parent.iterdir() if x.name != "state.json"]
        self.assertEqual(leftovers, [])

    def test_deterministic_output(self):
        a = self.dir / "a.json"
        b = self.dir / "b.json"
        payload = {"b": [1, 2], "a": "中文"}
        story_json.write_json(a, payload)
        story_json.write_json(b, payload)
        self.assertEqual(a.read_bytes(), b.read_bytes())


if __name__ == "__main__":
    unittest.main()

