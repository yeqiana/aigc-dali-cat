#!/usr/bin/env python3
"""Visual Profile Registry tests (Visual Profile Governance Phase 2.1).

Before this phase a runtime-request could declare an arbitrary visual_profile id
(real case: episodes/江南卖花姑娘的一天/meta/runtime-request.json declared
M00_ANCIENT_DAILY_LIFE_V1, which has no document under standards/visual_profiles/).
The resolver did not fail: it returned the default M00 profile and production
continued. Configuration presence was treated as evidence.

These tests lock the fail-closed contract:

  Case1: a registered profile (M00) resolves and validates          -> PASS
  Case2: an unregistered profile id fails closed                    -> FAIL
  Case3: an explicit allow_fallback=True still resolves             -> PASS
  Case4: registry path / registry document problems fail closed     -> FAIL

Extra coverage: the two shipped profiles stay legal without being rewritten,
governed profiles must carry the full governance field set, keyword inference can
never emit an unregistered id, and create_episode fails before it writes anything.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_creator  # noqa: E402
import visual_profile  # noqa: E402
import visual_profile_registry as registry  # noqa: E402
import visual_profile_resolver as resolver  # noqa: E402

M00 = "M00"
SPIRITED = "SPIRITED_AWAY_LIVE_ACTION_V1"
UNREGISTERED = "M00_ANCIENT_DAILY_LIFE_V1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VisualProfileRegistryCaseTest(unittest.TestCase):
    """The four required cases against the real checkout registry."""

    def test_case1_registered_profile_resolves(self) -> None:
        resolved = resolver.resolve_profile(M00, story_root=ROOT)
        self.assertEqual(resolved["profile_id"], M00)
        self.assertTrue(resolved["registered"])
        self.assertFalse(resolved["fallback"])
        self.assertEqual(resolved["resolution"], "registry")
        self.assertTrue(resolved["profile"])
        self.assertTrue(resolved["profile"]["visual_dna"])
        self.assertTrue((ROOT / resolved["profile_path"]).is_file())
        self.assertEqual(registry.validate_registered_profile(M00, ROOT), [])

    def test_case2_unregistered_profile_fails_closed(self) -> None:
        with self.assertRaises(registry.VisualProfileNotRegistered) as ctx:
            registry.resolve_registered_profile(UNREGISTERED, story_root=ROOT)
        self.assertEqual(ctx.exception.code, "VISUAL_PROFILE_NOT_REGISTERED")
        self.assertIn(UNREGISTERED, str(ctx.exception))

        with self.assertRaises(SystemExit):
            resolver.resolve_profile(UNREGISTERED, story_root=ROOT)

    def test_case2_does_not_silently_return_default(self) -> None:
        try:
            resolved = resolver.resolve_profile(UNREGISTERED, story_root=ROOT)
        except SystemExit:
            return
        self.fail(f"unregistered profile resolved instead of failing: {resolved['profile_id']}")

    def test_case3_explicit_fallback_still_resolves(self) -> None:
        resolved = resolver.resolve_profile(UNREGISTERED, story_root=ROOT, allow_fallback=True)
        self.assertEqual(resolved["profile_id"], M00)
        self.assertTrue(resolved["fallback"])
        self.assertEqual(resolved["resolution"], "fallback_default")
        self.assertEqual(resolved["requested_profile_id"], UNREGISTERED)
        self.assertEqual(resolved["fallback_default_id"], M00)

    def test_case4_registry_path_error_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-registry-missing-") as tmp:
            with self.assertRaises(registry.VisualProfileRegistryMissing) as ctx:
                resolver.resolve_profile(M00, story_root=Path(tmp))
            self.assertEqual(ctx.exception.code, "VISUAL_PROFILE_REGISTRY_MISSING")

    def test_case4_malformed_registry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-registry-bad-") as tmp:
            root = Path(tmp)
            target = root / registry.REGISTRY_REL
            target.parent.mkdir(parents=True)
            target.write_text(
                json.dumps({
                    "schema_version": 1,
                    "default_profile": "M00",
                    "profiles": [{"id": "M00", "path": "standards/visual_profiles/M00.json"}],
                }),
                encoding="utf-8",
            )
            with self.assertRaises(registry.VisualProfileRegistryInvalid) as ctx:
                resolver.resolve_profile(M00, story_root=root)
            self.assertEqual(ctx.exception.code, "VISUAL_PROFILE_REGISTRY_INVALID")
            self.assertIn("status", str(ctx.exception))

    def test_case4_default_not_registered_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-registry-default-") as tmp:
            root = Path(tmp)
            target = root / registry.REGISTRY_REL
            target.parent.mkdir(parents=True)
            target.write_text(
                json.dumps({
                    "schema_version": 1,
                    "default_profile": "M99",
                    "profiles": [{"id": "M00", "path": "standards/visual_profiles/M00.json", "status": "active"}],
                }),
                encoding="utf-8",
            )
            with self.assertRaises(registry.VisualProfileRegistryInvalid) as ctx:
                resolver.resolve_profile(M00, story_root=root)
            self.assertIn("default_profile", str(ctx.exception))

    def test_case4_unparsable_registry_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-registry-json-") as tmp:
            root = Path(tmp)
            target = root / registry.REGISTRY_REL
            target.parent.mkdir(parents=True)
            target.write_text("{ not json", encoding="utf-8")
            with self.assertRaises(registry.VisualProfileRegistryInvalid):
                registry.load_registry(root)


class VisualProfileSchemaTest(unittest.TestCase):
    """Schema contract for shipped and governed profiles."""

    def _copy_standards(self, tmp: str) -> Path:
        root = Path(tmp)
        shutil.copytree(ROOT / "standards/visual_profiles", root / "standards/visual_profiles")
        return root

    def test_shipped_profiles_pass_without_being_rewritten(self) -> None:
        profile_dir = ROOT / "standards/visual_profiles"
        before = {p.name: sha256_file(p) for p in profile_dir.glob("*.json")}
        for profile_id in registry.registry_ids(ROOT):
            self.assertEqual(registry.validate_registered_profile(profile_id, ROOT), [], profile_id)
        after = {p.name: sha256_file(p) for p in profile_dir.glob("*.json")}
        self.assertEqual(before, after, "validation must not rewrite profile documents")

    def test_governed_profile_requires_full_field_set(self) -> None:
        governed = {
            "profile_schema_version": 2,
            "id": "M01",
            "name": "古代普通人生活纪实",
            "scope": "account_immersive_profile",
            "reality_basis": "real_world_ordinary",
            "capture_philosophy": "记录一个普通人的一天",
            "camera_language": "first_person_or_companion_eye",
            "realism_level": "documentary_ordinary",
            "lighting_rules": ["practical_and_available_only"],
            "prohibited_patterns": ["影视棚拍布光"],
            "compatible_story_types": ["historical_ordinary_life"],
        }
        self.assertEqual(registry.validate_profile_document(governed, ROOT), [])
        for missing in ("reality_basis", "camera_language", "lighting_rules",
                        "prohibited_patterns", "compatible_story_types"):
            incomplete = {k: v for k, v in governed.items() if k != missing}
            errors = registry.validate_profile_document(incomplete, ROOT)
            self.assertTrue(
                any(missing in error for error in errors),
                f"{missing} should be required, got {errors}",
            )

    def test_legacy_profile_still_needs_identity_fields(self) -> None:
        errors = registry.validate_profile_document({"profile_id": "LEGACY"}, ROOT)
        self.assertTrue(any("profile_name" in error for error in errors))
        self.assertTrue(any("scope" in error for error in errors))

    def test_conditional_property_types_are_checked(self) -> None:
        errors = registry.validate_profile_document(
            {"profile_id": "X", "profile_name": "x", "scope": "s", "prohibited_patterns": "not-a-list"},
            ROOT,
        )
        self.assertTrue(any("prohibited_patterns" in error for error in errors), errors)

    def test_non_active_profile_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-registry-status-") as tmp:
            root = self._copy_standards(tmp)
            target = root / registry.REGISTRY_REL
            data = json.loads(target.read_text(encoding="utf-8"))
            data["profiles"][0]["status"] = "retired"
            target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            with self.assertRaises(registry.VisualProfileNotActive) as ctx:
                resolver.resolve_profile(M00, story_root=root)
            self.assertEqual(ctx.exception.code, "VISUAL_PROFILE_NOT_ACTIVE")

    def test_registered_id_with_missing_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-registry-file-") as tmp:
            root = Path(tmp)
            (root / "standards/visual_profiles").mkdir(parents=True)
            (root / registry.REGISTRY_REL).write_text(
                json.dumps({
                    "schema_version": 1,
                    "default_profile": "M00",
                    "profiles": [{"id": "M00", "path": "standards/visual_profiles/missing.json", "status": "active"}],
                }),
                encoding="utf-8",
            )
            with self.assertRaises(registry.VisualProfileFileMissing) as ctx:
                resolver.resolve_profile(M00, story_root=root)
            self.assertEqual(ctx.exception.code, "VISUAL_PROFILE_FILE_MISSING")


class VisualProfileInferenceTest(unittest.TestCase):
    """Keyword routing may only ever hand back a registered id."""

    def test_planned_routes_are_inert_until_registered(self) -> None:
        registered = set(registry.registry_ids(ROOT))
        for title in ("江南卖花姑娘的一天", "天界云务送信", "普通的周末", "random english title"):
            inferred = resolver.infer_profile(title, story_root=ROOT)
            self.assertIn(inferred, registered, title)

    def test_unregistered_route_target_falls_back_to_default(self) -> None:
        self.assertEqual(resolver.infer_profile("江南卖花姑娘的一天", story_root=ROOT), M00)
        self.assertNotIn(UNREGISTERED, registry.registry_ids(ROOT))


class VisualProfileCreatorTest(unittest.TestCase):
    """create_episode fails before writing, and records the resolution."""

    def _root(self, tmp: str) -> Path:
        root = Path(tmp)
        shutil.copytree(ROOT / "standards/visual_profiles", root / "standards/visual_profiles")
        return root

    def test_create_with_unregistered_profile_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-create-fail-") as tmp:
            root = self._root(tmp)
            with self.assertRaises(SystemExit):
                story_creator.create_episode(root, "雾中的另一座生活区", UNREGISTERED)
            self.assertFalse((root / "episodes").exists(), "a rejected request must not create an Episode")

    def test_create_with_registered_profile_records_no_fallback(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vp-create-ok-") as tmp:
            root = self._root(tmp)
            episode = story_creator.create_episode(root, "普通的周末", M00)
            request = json.loads((episode / "meta/runtime-request.json").read_text(encoding="utf-8"))
            self.assertEqual(request["visual_profile"], M00)
            resolution = request["visual_profile_resolution"]
            self.assertEqual(resolution["resolved_profile_id"], M00)
            self.assertEqual(resolution["requested_profile_id"], M00)
            self.assertIs(resolution["registered"], True)
            self.assertIs(resolution["fallback"], False)
            self.assertEqual(resolution["registry"], "standards/visual_profiles/index.json")

    def test_list_registered_profiles_reads_registry(self) -> None:
        listed = {p["profile_id"]: p for p in visual_profile.list_registered_profiles()}
        self.assertIn(M00, listed)
        self.assertIn(SPIRITED, listed)
        self.assertEqual(listed[M00]["profile_path"], "standards/visual_profiles/M00_MP4_网吧_流水席_旧数码.json")
        self.assertEqual(listed[M00]["status"], "active")


if __name__ == "__main__":
    unittest.main()
