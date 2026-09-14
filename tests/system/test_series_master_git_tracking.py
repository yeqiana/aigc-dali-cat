#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系列剧本母版图必须提交 Git（AGENTS.md 提交规则）。

"像素资产默认不入 Git" 的唯一强制例外是系列母版图：series 级
`meta/series-character-identity.json` 用 path + SHA 把系列身份权威绑定到像素锚点，
锚点若只留在本地，fresh clone / CI 会得到一个悬空的身份绑定。

本套测试固定 contract_sync.untracked_series_masters 的边界：
* 已入库的母版图通过；
* 本地存在但未入库的母版图 FAIL 并点名路径；
* 声明了但本地不存在的母版图按 missing 报出（不与未入库混淆）；
* 没有 series identity 的仓库不产生假失败；
* 当前真实仓库不存在未入库的系列母版图。
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import contract_sync  # noqa: E402
import story_json  # noqa: E402

SERIES = "10_测试系列"
IDENTITY_REL = Path("episodes") / SERIES / "meta" / contract_sync.SERIES_IDENTITY_NAME
GROUP_REL = f"episodes/{SERIES}/01_测试集/assets/characters/group.png"
PRIMARY_REL = f"episodes/{SERIES}/01_测试集/assets/characters/p01.png"
SUPPORT_REL = f"episodes/{SERIES}/01_测试集/assets/characters/p01_side.png"


def identity_doc(*, group=GROUP_REL, primary=PRIMARY_REL, support=SUPPORT_REL) -> dict:
    return {
        "schema_version": 1,
        "series_id": SERIES,
        "approved": True,
        "group_identity_asset": {"path": group, "sha256": "0" * 64},
        "characters": {
            "P01": {
                "primary_asset": {"path": primary, "sha256": "0" * 64},
                "supporting_assets": [{"path": support, "sha256": "0" * 64}],
            }
        },
    }


@unittest.skipUnless(shutil.which("git"), "git is required for series master tracking checks")
class SeriesMasterGitTrackingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="storyos-series-master-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        self.master_rels = (GROUP_REL, PRIMARY_REL, SUPPORT_REL)
        for rel in self.master_rels:
            target = self.tmp / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"\x89PNG\r\n\x1a\n series master fixture")

    def write_identity(self, doc: dict | None = None) -> None:
        path = self.tmp / IDENTITY_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        story_json.write_json(path, doc or identity_doc())

    def stage(self, *rels: str) -> None:
        subprocess.run(["git", "-C", str(self.tmp), "add", "--", *rels], check=True)

    def test_committed_series_masters_pass(self) -> None:
        self.write_identity()
        self.stage(*self.master_rels)
        self.assertEqual(contract_sync.untracked_series_masters(self.tmp), [])

    def test_local_only_master_image_fails_and_names_the_path(self) -> None:
        self.write_identity()
        self.stage(GROUP_REL, PRIMARY_REL)
        errors = contract_sync.untracked_series_masters(self.tmp)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn(SUPPORT_REL, errors[0])
        self.assertIn("committed to Git", errors[0])
        self.assertIn("P01:supporting:0", errors[0])

    def test_absent_master_image_is_reported_as_missing(self) -> None:
        self.write_identity()
        self.stage(*self.master_rels)
        (self.tmp / SUPPORT_REL).unlink()
        errors = contract_sync.untracked_series_masters(self.tmp)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("missing", errors[0])
        self.assertIn(SUPPORT_REL, errors[0])

    def test_repo_without_series_identity_is_not_flagged(self) -> None:
        self.assertEqual(contract_sync.untracked_series_masters(self.tmp), [])

    def test_gitless_checkout_is_skipped(self) -> None:
        self.write_identity()
        shutil.rmtree(self.tmp / ".git")
        self.assertEqual(contract_sync.untracked_series_masters(self.tmp), [])

    def test_declared_masters_cover_group_primary_and_supporting(self) -> None:
        rows = contract_sync.series_master_assets(identity_doc())
        self.assertEqual(
            rows,
            [("group", GROUP_REL), ("P01:primary", PRIMARY_REL), ("P01:supporting:0", SUPPORT_REL)],
        )

    def test_this_repository_has_no_untracked_series_master(self) -> None:
        self.assertEqual(contract_sync.untracked_series_masters(ROOT), [])


if __name__ == "__main__":
    unittest.main()
