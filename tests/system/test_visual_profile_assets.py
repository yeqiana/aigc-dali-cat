#!/usr/bin/env python3
"""Visual Profile asset tests (Visual Profile Governance Phase 2.2).

Phase 2.1 made the registry the single source of truth and turned an unknown
profile id into a hard failure. Phase 2.2 migrates the shipped M00 asset into
that governance model and adds the first multi-world profiles (M01 / M02 / M03).

These tests lock the asset contract:

  Case1: the four governed profiles all satisfy the profile schema        -> PASS
  Case2: registry ids are unique and match standards/visual_profiles/profiles
  Case3: M02 declares reality_basis=fictional_world_mundane + diegetic device
  Case4: no profile's prohibited_patterns leak into its own requirements
  Case5: deprecated aliases never change how a historical id resolves

Extra coverage: the legacy locked M00 asset is not rewritten (sha256 pinned),
and the governed M00 mirror keeps the legacy visual DNA verbatim.
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import visual_profile_registry as registry  # noqa: E402

STANDARDS_DIR = ROOT / "standards/visual_profiles"
PROFILES_DIR = STANDARDS_DIR / "profiles"

GOVERNED = (
    "M00_REAL_WORLD_DOCUMENTARY_V1",
    "M01_ANCIENT_MUNDANE_LIFE_V1",
    "M02_HEAVEN_MUNDANE_WORKER_V1",
    "M03_JIANGNAN_IMMERSIVE_LIFE_V1",
)

# Pinned hash of the pre-Phase-2.2 locked asset. If this moves, every historical
# Frame Contract profile_sha256 breaks at once.
LEGACY_M00_SHA256 = "7a4de65bad3ff9e659cb595af64cc5e2c4eb23a7b0de88959f20c74a11cff25f"

GOVERNANCE_FIELDS = (
    "id",
    "name",
    "scope",
    "reality_basis",
    "capture_philosophy",
    "camera_language",
    "realism_level",
    "lighting_rules",
    "prohibited_patterns",
    "compatible_story_types",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_profile(profile_id: str) -> dict:
    return registry.load_profile_document(profile_id, ROOT)


def governed_profile_files() -> list[Path]:
    return sorted(PROFILES_DIR.glob("*.json"))


def legacy_m00_path() -> Path:
    matches = sorted(STANDARDS_DIR.glob("M00_MP4_*.json"))
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one legacy M00 asset, found {matches}")
    return matches[0]


class GovernedProfileSchemaTest(unittest.TestCase):
    """Case 1: the governed profiles are legal under the shared schema."""

    def test_case1_governed_profiles_pass_schema(self) -> None:
        for profile_id in GOVERNED:
            with self.subTest(profile_id=profile_id):
                self.assertEqual(registry.validate_registered_profile(profile_id, ROOT), [])

    def test_governed_profiles_declare_schema_version_2_and_fields(self) -> None:
        for profile_id in GOVERNED:
            with self.subTest(profile_id=profile_id):
                doc = load_profile(profile_id)
                self.assertGreaterEqual(doc["profile_schema_version"], 2)
                self.assertEqual(doc["id"], profile_id)
                for field in GOVERNANCE_FIELDS:
                    self.assertIn(field, doc, f"{profile_id} missing {field}")
                    self.assertTrue(doc[field], f"{profile_id}.{field} must not be empty")

    def test_governed_m00_mirrors_legacy_visual_dna(self) -> None:
        legacy = json.loads(legacy_m00_path().read_text(encoding="utf-8"))
        governed = load_profile("M00_REAL_WORLD_DOCUMENTARY_V1")
        for field in ("visual_dna", "texture_translation", "anchors", "anti_homogeneity",
                      "principle", "precedence"):
            self.assertEqual(governed.get(field), legacy.get(field), field)

    def test_legacy_m00_asset_is_not_rewritten(self) -> None:
        self.assertEqual(sha256_file(legacy_m00_path()), LEGACY_M00_SHA256)
        governed = load_profile("M00_REAL_WORLD_DOCUMENTARY_V1")
        self.assertEqual(
            governed["derived_from"]["legacy_locked_sha256"], LEGACY_M00_SHA256
        )
        entry = registry.registry_entry("M00", ROOT)
        self.assertEqual(entry["path"], "standards/visual_profiles/" + legacy_m00_path().name)


class ProfileRegistryIdentityTest(unittest.TestCase):
    """Case 2: ids are unique, and the governed files match the registry."""

    def test_case2_registry_ids_are_unique(self) -> None:
        ids = registry.registry_ids(ROOT)
        self.assertEqual(len(ids), len(set(ids)), ids)
        for profile_id in ids:
            self.assertTrue(profile_id.strip())

    def test_case2_governed_files_match_registry(self) -> None:
        on_disk = {
            json.loads(path.read_text(encoding="utf-8"))["id"]
            for path in governed_profile_files()
        }
        self.assertEqual(on_disk, set(GOVERNED))
        for profile_id in GOVERNED:
            entry = registry.registry_entry(profile_id, ROOT)
            self.assertEqual(entry["status"], "active")
            self.assertEqual(entry["format"], "governed_v2")
            self.assertTrue((ROOT / entry["path"]).is_file(), profile_id)

    def test_single_account_default_is_m00(self) -> None:
        self.assertEqual(registry.default_profile_id(ROOT), "M00")
        for profile_id in GOVERNED[1:]:
            self.assertNotEqual(load_profile(profile_id).get("default_when_unspecified"), True)


class M02FictionalWorldTest(unittest.TestCase):
    """Case 3: the heaven-world profile cannot inherit real_world."""

    def test_case3_m02_requires_fictional_world_mundane(self) -> None:
        doc = load_profile("M02_HEAVEN_MUNDANE_WORKER_V1")
        self.assertEqual(doc["reality_basis"], "fictional_world_mundane")
        self.assertNotEqual(doc["reality_basis"], "real_world")
        self.assertTrue(doc.get("reality_basis_note"))

    def test_case3_m02_declares_diegetic_capture_device(self) -> None:
        doc = load_profile("M02_HEAVEN_MUNDANE_WORKER_V1")
        device = doc["diegetic_capture_device"]
        for field in ("device", "holder", "why_exists", "capture_reason", "save_reason",
                      "resolves_ghost_camera"):
            self.assertTrue(device.get(field), f"diegetic_capture_device.{field} must not be empty")
        self.assertEqual(doc["visual_dna"].get("diegetic_capture_device"), "required")
        self.assertEqual(doc["visual_dna"].get("ghost_camera"), "forbidden")


class ProhibitedPatternTest(unittest.TestCase):
    """Case 4: forbidden looks never become requirements in any profile."""

    def test_case4_prohibited_terms_never_appear_in_requirements(self) -> None:
        for profile_id in GOVERNED:
            doc = load_profile(profile_id)
            requirements = " ".join(
                list(doc.get("must_keep") or []) + list(doc.get("compatible_story_types") or [])
            )
            with self.subTest(profile_id=profile_id):
                for term in doc.get("prohibited_patterns") or []:
                    self.assertNotIn(term, requirements, f"{profile_id}: {term}")

    def test_case4_m01_and_m03_carry_explicit_prohibitions(self) -> None:
        m01 = load_profile("M01_ANCIENT_MUNDANE_LIFE_V1")
        m03 = load_profile("M03_JIANGNAN_IMMERSIVE_LIFE_V1")
        self.assertTrue(m01["prohibited_patterns"])
        self.assertTrue(m03["prohibited_patterns"])
        for term in ("影视古装大片", "影楼写真", "现代摄影设备入镜", "完美棚拍"):
            self.assertTrue(
                any(term in item for item in m01["prohibited_patterns"]), term
            )
        for term in ("旅游宣传片", "风景大片", "商业摄影"):
            self.assertTrue(
                any(term in item for item in m03["prohibited_patterns"]), term
            )
        self.assertTrue(load_profile("M02_HEAVEN_MUNDANE_WORKER_V1")["prohibited_patterns"])

    def test_case4_m03_era_is_not_assumed_historical(self) -> None:
        m03 = load_profile("M03_JIANGNAN_IMMERSIVE_LIFE_V1")
        self.assertEqual(m03["era"], "unspecified")
        self.assertIn("modern", m03["era_policy"]["allowed"])
        self.assertIn("historical", m03["era_policy"]["allowed"])


class DeprecatedAliasTest(unittest.TestCase):
    """Case 5: aliases are metadata and never change historical resolution."""

    def test_case5_alias_table_is_recorded(self) -> None:
        aliases = {entry["old_id"]: entry for entry in registry.registry_aliases(ROOT)}
        self.assertEqual(
            set(aliases), {"M00_ANCIENT_DAILY_LIFE_V1", "M00_HEAVEN_WORKER_DAILY_V1"}
        )
        registered = set(registry.registry_ids(ROOT))
        for old_id, entry in aliases.items():
            self.assertEqual(entry["status"], "deprecated")
            self.assertIn(entry["replacement"], registered)
            self.assertNotIn(old_id, registered)

    def test_case5_deprecated_alias_still_fails_closed(self) -> None:
        for old_id in ("M00_ANCIENT_DAILY_LIFE_V1", "M00_HEAVEN_WORKER_DAILY_V1"):
            with self.subTest(old_id=old_id):
                with self.assertRaises(registry.VisualProfileNotRegistered):
                    registry.resolve_registered_profile(old_id, story_root=ROOT)

    def test_case5_alias_replacement_requires_opt_in(self) -> None:
        self.assertIsNone(registry.alias_replacement("M00_ANCIENT_DAILY_LIFE_V1", story_root=ROOT))
        self.assertEqual(
            registry.alias_replacement(
                "M00_ANCIENT_DAILY_LIFE_V1", story_root=ROOT, follow_deprecated=True
            ),
            "M01_ANCIENT_MUNDANE_LIFE_V1",
        )
        self.assertIsNone(registry.alias_replacement("NOT_AN_ALIAS", story_root=ROOT))

    def test_case5_configured_default_still_resolves(self) -> None:
        resolved = registry.resolve_registered_profile("M00", story_root=ROOT)
        self.assertTrue(resolved["registered"])
        self.assertFalse(resolved["fallback"])
        self.assertEqual(registry.validate_registered_profile("M00", ROOT), [])


if __name__ == "__main__":
    unittest.main()
