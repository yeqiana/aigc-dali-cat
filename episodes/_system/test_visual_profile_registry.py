#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import visual_profile  # noqa: E402
import visual_profile_bridge_v224 as visual_bridge  # noqa: E402

EP12 = ROOT / "episodes" / "12_千寻" / "01_那条不存在的隧道"
PROFILE_ID = "SPIRITED_AWAY_LIVE_ACTION_V1"
PROFILE_REL = "standards/visual_profiles/SPIRITED_AWAY_LIVE_ACTION_V1.json"


def ns(**kw):
    return argparse.Namespace(**kw)


class VisualProfileRegistryTests(unittest.TestCase):
    def test_registered_profiles_include_m00_and_spirited(self):
        ids = [p["profile_id"] for p in visual_profile.list_registered_profiles()]
        self.assertIn("M00", ids)
        self.assertIn(PROFILE_ID, ids)

    def _with_gates(self, ep: Path):
        meta = ep / "meta"
        meta.mkdir(parents=True, exist_ok=True)
        (meta / "story-gates.json").write_text(json.dumps({"schema_version": 1}), encoding="utf-8")

    def test_set_override_resolves_profile_by_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp)
            self._with_gates(ep)
            args = ns(episode_dir=str(ep), profile_id=PROFILE_ID, profile_path=None,
                      reason="test auto lookup", capture_profile=None)
            self.assertEqual(visual_profile.cmd_set_override(args), 0)
            gates = json.loads((ep / "meta" / "story-gates.json").read_text(encoding="utf-8"))
            vp = gates["visual_profile"]
            self.assertEqual(vp["mode"], "override")
            self.assertEqual(vp["profile_id"], PROFILE_ID)
            self.assertEqual(vp["profile_path"], PROFILE_REL)
            self.assertEqual(vp["override_reason"], "test auto lookup")

    def test_set_override_explicit_path_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp)
            self._with_gates(ep)
            args = ns(episode_dir=str(ep), profile_id=PROFILE_ID, profile_path=PROFILE_REL,
                      reason="test explicit path", capture_profile=None)
            self.assertEqual(visual_profile.cmd_set_override(args), 0)
            gates = json.loads((ep / "meta" / "story-gates.json").read_text(encoding="utf-8"))
            self.assertEqual(gates["visual_profile"]["profile_path"], PROFILE_REL)

    def test_set_override_unknown_id_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = ns(episode_dir=tmp, profile_id="NOT_A_REAL_PROFILE", profile_path=None,
                      reason="test", capture_profile=None)
            with self.assertRaises(SystemExit):
                visual_profile.cmd_set_override(args)

    def test_episode12_resolves_to_spirited(self):
        if not EP12.is_dir():
            self.skipTest("episode 12 meta not present")
        resolved = visual_bridge.resolve_profile(EP12)
        self.assertEqual(resolved["profile_id"], PROFILE_ID)

    def test_compile_contract_carries_must_keep_and_forbidden(self):
        if not EP12.is_dir():
            self.skipTest("episode 12 meta not present")
        contract = visual_bridge.compile_prompt_contract(EP12)
        self.assertEqual(contract["profile_id"], PROFILE_ID)
        self.assertIn("must_keep=", contract["text"])
        self.assertIn("forbidden=", contract["text"])


if __name__ == "__main__":
    unittest.main()
