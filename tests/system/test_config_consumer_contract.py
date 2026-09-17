#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate G (P1-A): a declared production parameter has a consumer, one authority,
and a recorded source.

Each test here exists because reading the config proved nothing. W-75 was not a
wrong number: `max_inflight_codex_images` / `adaptive_concurrency_steps` were
declared in six files across four formats, two of them disagreeing with the file
the running code actually reads -- including `standards/AUTHORITY_INDEX.json`,
the registry whose whole job is to settle that kind of question. Every one of
those files parsed. `doctor` was green. Only executing the consumer showed which
number was real.

So these tests do not assert that fields exist. They assert that a value reaches
behaviour, that no second copy of it survives, and that a run which took an
environment override can be told apart, afterwards, from one that did not.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import codex_subscription_batch_runtime
import codex_subscription_image
import effective_config
import runtime_router
import runtime_workspace
import storage_config
import storyos_config

YAML = ROOT / "config/storyos.yaml"

# The one parameter family that had six declarations. Both the canonical names
# and every alias that was found in the wild, so a copy under a new name is
# caught too.
BATCH_LIMIT_KEYS = (
    "max_inflight_codex_images",
    "max_inflight_logical_images",
    "codex_logical_batch_max_inflight_images",
    "codex_max_inflight_images",
)
BATCH_STEP_KEYS = (
    "adaptive_concurrency_steps",
    "adaptive_steps",
    "codex_adaptive_concurrency",
    "codex_logical_batch_adaptive_steps",
)
AUTHORITY = "config/agent_runtime/codex-subscription-batch.json"

# §8.1: the production-critical surface. Every one of these must be read by a
# module that actually runs, not merely type-checked by the config validator.
PRODUCTION_KEYS = (
    "runtime.preferred_runtime",
    "runtime.image_execution_runtime",
    "runtime.review.vision.runtime",
    "runtime.review.vision.max_inflight_final",
    "runtime.workers.local_codex_preimage",
    "runtime.workers.derived",
    "runtime.preimage_parallel_enabled",
    "production.max_inflight_images",
    "provider.group_reference_proxy",
    "normalize.provider_ratio_crop_exception_enabled",
    "storage.runtime_store.mode",
    "storage.runtime_store.jsonl_root",
    "storage.episode_meta_store.mode",
)

# Declared on 2026-09-15 as non-operative and removed. They must not come back
# as inert keys: a switch nothing executes is worse than no switch, because it
# reads like control.
REMOVED_DEAD_KEYS = (
    "runtime.parallel.authority_enabled",
    "runtime.parallel.derived_enabled",
    "runtime.workers.review",
    "runtime.workers.authority",
)


def _json_surface(root: Path) -> list[Path]:
    """Files that declare configuration or contract values."""
    files = sorted((root / "config").rglob("*.json"))
    files += sorted((root / "runtimes").glob("*.json"))
    for rel in ("standards/AUTHORITY_INDEX.json", "story_os_manifest.json"):
        if (root / rel).is_file():
            files.append(root / rel)
    return files


def _walker(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key, value, path
            yield from _walker(value, f"{path}/{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walker(value, f"{path}/{index}")


def declarations(root: Path) -> list[tuple[str, str, object]]:
    """Every (file, key, value) that declares a batch limit as a value.

    Pointer keys are not declarations: naming the authority file is the opposite
    of duplicating it.
    """
    found = []
    for path in _json_surface(root):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # a malformed config is a different test's problem
            raise AssertionError(f"{path} is not readable JSON: {exc}") from exc
        for key, value, _ in _walker(data):
            if key in BATCH_LIMIT_KEYS or key in BATCH_STEP_KEYS:
                found.append((path.relative_to(root).as_posix(), key, value))
    return found


def readers_of(key: str) -> list[str]:
    """Production modules that read `key` through the unified entry.

    `storyos_config.py` is excluded on purpose: validate() merely type-checks a
    key, and a key whose only reader is its own validator is exactly the
    "declared but never consumed" state this contract forbids.
    """
    hits = []
    for base in (ROOT / "episodes/_system", ROOT / "platform"):
        for path in sorted(base.rglob("*.py")):
            if path.name.startswith("test_") or path.name == "storyos_config.py":
                continue
            if "__pycache__" in path.parts:
                continue
            if key in path.read_text(encoding="utf-8", errors="replace"):
                hits.append(path.relative_to(ROOT).as_posix())
    return hits


class SingleAuthorityTests(unittest.TestCase):

    def test_the_batch_limits_are_declared_in_exactly_one_file(self) -> None:
        found = declarations(ROOT)
        self.assertTrue(found, "扫描面里一个声明都没有——扫描本身失效了")
        files = sorted({rel for rel, _, _ in found})
        self.assertEqual(
            files, [AUTHORITY],
            "同一个参数又出现了第二份声明：\n  " +
            "\n  ".join(f"{rel}: {key}={value!r}" for rel, key, value in found),
        )

    def test_the_scan_would_notice_a_second_declaration(self) -> None:
        """A scan that cannot fail protects nothing."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "config/agent_runtime").mkdir(parents=True)
            (root / "config/agent_runtime/codex-subscription-batch.json").write_text(
                json.dumps({"max_inflight_codex_images": 3}), encoding="utf-8")
            (root / "config/providers").mkdir(parents=True)
            (root / "config/providers/other.json").write_text(
                json.dumps({"nested": {"adaptive_concurrency_steps": [5, 3, 1]}}), encoding="utf-8")
            files = sorted({rel for rel, _, _ in declarations(root)})
        self.assertEqual(files, [AUTHORITY, "config/providers/other.json"])

    def test_the_authority_file_is_the_one_the_running_code_reads(self) -> None:
        """Rewrite the authority; the consumer must follow. Nothing else may."""
        path = ROOT / AUTHORITY
        original = path.read_text(encoding="utf-8")

        def restore() -> None:
            path.write_text(original, encoding="utf-8")

        self.addCleanup(restore)
        data = json.loads(original)
        data["max_inflight_codex_images"] = 7
        data["adaptive_concurrency_steps"] = [7, 4, 1]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        self.assertEqual(codex_subscription_batch_runtime.max_inflight(), 7,
                         "改了权威文件而消费者没变——消费者读的不是这个文件")
        self.assertEqual(codex_subscription_batch_runtime.adaptive_steps(), [7, 4, 1])

    def test_every_pointer_names_a_file_that_exists(self) -> None:
        pointers = []
        for rel in ("standards/AUTHORITY_INDEX.json", "runtimes/runtime-contract.json",
                    "runtimes/workflow-contract.json", "config/providers/image-provider-runtime.json"):
            data = json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))
            for key, value, _ in _walker(data):
                if isinstance(value, str) and value.endswith("codex-subscription-batch.json"):
                    pointers.append((rel, key, value))
        self.assertGreaterEqual(len(pointers), 4, f"指向权威文件的指针少了：{pointers}")
        for rel, key, value in pointers:
            self.assertTrue((ROOT / value).is_file(), f"{rel}#{key} 指向不存在的文件：{value}")


class ConsumerTests(unittest.TestCase):

    def test_every_production_key_has_a_real_consumer(self) -> None:
        missing = {key: readers_of(key) for key in PRODUCTION_KEYS if not readers_of(key)}
        self.assertEqual(missing, {},
                         f"这些配置项没有任何生产消费者（只有类型检查）：{sorted(missing)}")

    def test_no_declared_parallel_switch_is_merely_type_checked(self) -> None:
        """The W-91 shape: a switch whose only reader is the validator."""
        for key in ("runtime.preimage_parallel_enabled",):
            self.assertTrue(readers_of(key), f"{key} 没有执行消费者")

    def test_removed_dead_keys_are_gone_from_both_yaml_and_the_validator(self) -> None:
        """Checked against the parsed config, not the file text.

        The YAML explains *why* these keys were removed, and that comment names
        them. A text scan would fail on its own explanation.
        """
        cfg = storyos_config.load_config()
        self.assertNotIn("parallel", storyos_config.get_path(cfg, "runtime") or {},
                         "runtime.parallel 又回来了——它两个开关都没有执行消费者")
        self.assertNotIn("review", storyos_config.get_path(cfg, "runtime.workers") or {},
                         "runtime.workers.review 又回来了——它的唯一读取点没有生产消费者")
        for key in REMOVED_DEAD_KEYS:
            self.assertIsNone(storyos_config.get_path(cfg, key), f"{key} 仍是有效配置")
        self.assertEqual(storyos_config.validate(cfg), [],
                         "删除死配置后 validate() 不再干净")

    def test_active_agent_contracts_delegate_image_default_to_storyos_config(self) -> None:
        """Active entry docs must not freeze a second image-model default."""
        authority = "config/storyos.yaml:image.model"
        stale_phrases = (
            "默认 `image_model=gpt-image-2`",
            "实际图片仍由 `gpt-image-2`",
            "实际图片模型固定 `gpt-image-2`",
        )
        for rel in ("AGENTS.md", "START_HERE.md", "SKILL.md"):
            text = (ROOT / rel).read_text(encoding="utf-8-sig")
            self.assertIn(authority, text, f"{rel} 没有委托 image.model 唯一配置入口")
            for phrase in stale_phrases:
                self.assertNotIn(phrase, text, f"{rel} 又写死了旧图片模型：{phrase}")


class EffectiveConfigTests(unittest.TestCase):

    def test_an_env_override_is_recorded_with_the_variable_that_caused_it(self) -> None:
        with mock.patch.dict(os.environ, {"STORY_OS_IMAGE_RUNTIME": "PRODUCT_RUNTIME"}):
            row = effective_config.snapshot()["sources"]["image_execution_runtime"]
            self.assertEqual(row, {"value": "PRODUCT_RUNTIME",
                                   "source": "env:STORY_OS_IMAGE_RUNTIME"})
            self.assertEqual(runtime_router.image_execution_runtime()[0], "PRODUCT_RUNTIME")

    def test_without_an_override_the_config_file_is_named_as_the_source(self) -> None:
        env = {k: "" for k in ("STORY_OS_IMAGE_RUNTIME", "STORY_OS_VISION_RUNTIME", "STORY_OS_RUNTIME")}
        with mock.patch.dict(os.environ, env):
            sources = effective_config.snapshot()["sources"]
        self.assertEqual(sources["image_execution_runtime"]["source"],
                         "config/storyos.yaml#runtime.image_execution_runtime")
        self.assertEqual(sources["runtime"]["source"],
                         "config/storyos.yaml#runtime.preferred_runtime")
        self.assertEqual(effective_config.snapshot()["overrides_in_force"], [])

    def test_the_snapshot_value_agrees_with_the_router_that_decides(self) -> None:
        """Derived evidence must not drift from the thing it describes."""
        sources = effective_config.snapshot()["sources"]
        self.assertEqual(sources["runtime"]["value"], runtime_router.detect()[0])
        self.assertEqual(sources["image_execution_runtime"]["value"],
                         runtime_router.image_execution_runtime()[0])
        self.assertEqual(sources["vision_review_runtime"]["value"],
                         runtime_router.vision_review_runtime()[0])

    def test_credentials_are_recorded_as_presence_never_as_values(self) -> None:
        secret = "not-a-real-password-4f21"
        with mock.patch.dict(os.environ, {"STORYOS_MYSQL_PWD": secret}):
            data = effective_config.snapshot()
            blob = json.dumps(data, ensure_ascii=False)
        self.assertNotIn(secret, blob, "快照把凭据值写出去了")
        self.assertTrue(data["credential_presence"]["STORYOS_MYSQL_PWD"]["present"])

    def test_the_snapshot_lands_in_the_episode_runtime_workspace(self) -> None:
        base = ROOT / "episodes/_tests"
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as td:
            runtime_root = Path(td) / ".runtime-test"
            with mock.patch.object(runtime_workspace, "DEFAULT_ROOT", runtime_root):
                effective_config.write(td)
                path = runtime_workspace.workspace_path(td, effective_config.REL)
                self.assertTrue(path.is_file())
                self.assertFalse((Path(td) / effective_config.REL).exists())
                written = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("sources", written)

    def test_runtime_store_is_application_resolved_and_platform_has_no_hidden_default(self) -> None:
        """W-95: app resolves YAML/env; platform must not invent a second root/connection."""
        sys.path.insert(0, str(ROOT))
        from platform.repository import runtime_repository_provider as provider

        env = {k: "" for k in (
            "STORYOS_RUNTIME_JSONL_ROOT",
            "STORYOS_RUNTIME_STORE_MODE",
            "STORYOS_EPISODE_META_STORE_MODE",
        )}
        with mock.patch.dict(os.environ, env):
            resolved = storage_config.runtime_store_config()
            self.assertEqual(resolved, {"mode": "jsonl", "jsonl_root": ".storyos"})
            sources = effective_config.snapshot()["sources"]
            with self.assertRaises(ValueError):
                provider.build_runtime_repositories()
        self.assertEqual(sources["runtime_store_mode"], {
            "value": "jsonl", "source": "config/storyos.yaml#storage.runtime_store.mode"})
        self.assertEqual(sources["runtime_jsonl_root"], {
            "value": ".storyos", "source": "config/storyos.yaml#storage.runtime_store.jsonl_root"})
        self.assertEqual(sources["episode_meta_store_mode"], {
            "value": "json", "source": "config/storyos.yaml#storage.episode_meta_store.mode"})

        with mock.patch.dict(os.environ, {"STORYOS_RUNTIME_JSONL_ROOT": "/declared/root"}):
            row = effective_config.snapshot()["sources"]["runtime_jsonl_root"]
        self.assertEqual(row, {"value": "/declared/root",
                               "source": "env:STORYOS_RUNTIME_JSONL_ROOT"})

    def test_storage_summary_separates_resolved_values_from_env_presence(self) -> None:
        env = {key: "" for key in (
            "STORYOS_MYSQL_HOST", "STORYOS_MYSQL_PORT", "STORYOS_MYSQL_USER", "STORYOS_MYSQL_DB",
            "STORYOS_REDIS_HOST", "STORYOS_REDIS_PORT", "STORYOS_REDIS_DB",
            "STORYOS_RUNTIME_STORE_MODE", "STORYOS_RUNTIME_JSONL_ROOT",
        )}
        with mock.patch.dict(os.environ, env):
            summary = storage_config.storage_summary()
        self.assertEqual(summary["mysql"]["host"], "127.0.0.1")
        self.assertFalse(summary["mysql"]["user_present"])
        self.assertFalse(summary["mysql"]["host_env_provided"])
        self.assertEqual(summary["runtime_store"]["jsonl_root"], ".storyos")
        self.assertFalse(summary["runtime_store"]["jsonl_root_env_provided"])

        with mock.patch.dict(os.environ, {"STORYOS_MYSQL_HOST": "10.0.0.9"}):
            summary = storage_config.storage_summary()
        self.assertEqual(summary["mysql"]["host"], "10.0.0.9")
        self.assertTrue(summary["mysql"]["host_env_provided"])

    def test_phase9_evidence_summaries_share_application_storage_resolution(self) -> None:
        """W-94: evidence may report env presence, but values come from one resolver."""
        scripts = (
            "phase9_runtime_worker.py",
            "phase9_recovery_drill.py",
            "phase9_consistency_scan.py",
            "phase9_canary_drill.py",
            "phase9_liveness_watchdog.py",
            "phase9_runtime_smoke.py",
        )
        for name in scripts:
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8-sig")
            self.assertIn("storage_config.storage_summary()", source, name)
        # Connection construction must use the same resolved application entry.
        for name in ("phase9_runtime_worker.py", "phase9_consistency_scan.py"):
            source = (ROOT / "scripts" / name).read_text(encoding="utf-8-sig")
            self.assertIn("storage_config.mysql_connection_kwargs()", source, name)

    def test_product_booleans_have_yaml_authority_and_env_override(self) -> None:
        env = {
            "STORY_OS_GROUP_REFERENCE_PROXY": "",
            "STORY_OS_PROVIDER_RATIO_CROP_EXCEPTION": "",
        }
        with mock.patch.dict(os.environ, env):
            sources = effective_config.snapshot()["sources"]
            self.assertFalse(codex_subscription_image._configurable_bool(
                "provider.group_reference_proxy", "STORY_OS_GROUP_REFERENCE_PROXY"))
            self.assertFalse(codex_subscription_image._configurable_bool(
                "normalize.provider_ratio_crop_exception_enabled", "STORY_OS_PROVIDER_RATIO_CROP_EXCEPTION"))
        self.assertEqual(sources["group_reference_proxy"]["source"],
                         "config/storyos.yaml#provider.group_reference_proxy")
        self.assertEqual(sources["provider_ratio_crop_exception"]["source"],
                         "config/storyos.yaml#normalize.provider_ratio_crop_exception_enabled")

        with mock.patch.dict(os.environ, {"STORY_OS_GROUP_REFERENCE_PROXY": "true"}):
            self.assertTrue(codex_subscription_image._configurable_bool(
                "provider.group_reference_proxy", "STORY_OS_GROUP_REFERENCE_PROXY"))
            row = effective_config.snapshot()["sources"]["group_reference_proxy"]
        self.assertEqual(row, {"value": True, "source": "env:STORY_OS_GROUP_REFERENCE_PROXY"})

    def test_env_only_controls_are_explicitly_classified_not_pretend_product_config(self) -> None:
        with mock.patch.dict(os.environ, {"STORY_OS_ALLOW_CODEX_FULL_ACCESS": ""}):
            row = effective_config.snapshot()["sources"]["allow_codex_full_access"]
        self.assertEqual(row["classification"], "security_opt_in")
        self.assertIn("(unset)", row["source"])
        self.assertIsNone(storyos_config.get_path(storyos_config.load_config(), "security.allow_codex_full_access"))

    def test_w97_original_env_surface_is_fully_classified(self) -> None:
        """W-97: product rules move to YAML; operator/security facts stay env-only."""
        original = {
            "STORY_OS_IMAGE_PROVIDER_ROUTE",
            "STORY_OS_GROUP_REFERENCE_PROXY",
            "STORY_OS_MANUAL_RAW_DIR",
            "STORY_OS_PROVIDER_RATIO_CROP_EXCEPTION",
            "STORY_OS_RUNTIME",
            "STORY_OS_ALLOW_CODEX_FULL_ACCESS",
            "STORY_OS_ROLLING_VISION_VERIFIED",
        }
        classified = {row[2] for row in effective_config.ROUTED}
        classified |= {row[2] for row in effective_config.CONFIGURABLE_ENV}
        classified |= {row[1] for row in effective_config.ENV_ONLY}
        self.assertTrue(original.issubset(classified), original - classified)

        product_env = {row[2] for row in effective_config.CONFIGURABLE_ENV}
        self.assertEqual(product_env, {
            "STORY_OS_GROUP_REFERENCE_PROXY",
            "STORY_OS_PROVIDER_RATIO_CROP_EXCEPTION",
        })
        env_only = {row[1]: row[2] for row in effective_config.ENV_ONLY}
        self.assertEqual(env_only["STORY_OS_IMAGE_PROVIDER_ROUTE"], "operator_transport_override")
        self.assertEqual(env_only["STORY_OS_MANUAL_RAW_DIR"], "recovery_debug_override")
        self.assertEqual(env_only["STORY_OS_ALLOW_CODEX_FULL_ACCESS"], "security_opt_in")
        self.assertEqual(env_only["STORY_OS_ROLLING_VISION_VERIFIED"], "capability_attestation")

    def test_nothing_reads_the_snapshot_back_to_decide_anything(self) -> None:
        """It is a record of a decision, not a source of one.

        The runner writes it every cycle. Nothing may open it to find out what
        the configuration is -- that question is `storyos_config`'s, and a
        second answer to it is exactly how W-75 happened.
        """
        rel = effective_config.REL.as_posix()
        readers = []
        for rel_mod in readers_of("effective_config") + readers_of("effective-config.json"):
            if "test" in rel_mod or rel_mod.endswith("effective_config.py"):
                continue
            text = (ROOT / rel_mod).read_text(encoding="utf-8", errors="replace")
            if f"effective_config.snapshot(" in text or f'"{rel}"' in text or f"'{rel}'" in text:
                readers.append(rel_mod)
        self.assertEqual(readers, [],
                         f"有生产模块把派生快照当成了配置来源：{readers}")
        self.assertTrue(readers_of("effective_config"),
                        "没有任何生产代码写快照——那它就只是文档")


if __name__ == "__main__":
    unittest.main(verbosity=2)
