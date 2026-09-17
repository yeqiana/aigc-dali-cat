#!/usr/bin/env python3
"""storage 配置解析器（episodes/_system/storage_config.py）契约测试。

覆盖四条不变量：
    1. 优先级固定为 显式参数 > 环境变量 > config/storyos.yaml 默认值；
    2. 凭据只按 storage.*.password_env 指名的环境变量解析，绝不来自 yaml 值；
    3. 证据（storage_summary）只报 password_present，不泄露凭据；
    4. config/storyos.yaml 一旦写入凭据字面量必须 fail-fast。
"""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import storage_config  # noqa: E402
import storyos_config  # noqa: E402

SECRET = "unit-test-secret-value"

ENV_KEYS = (
    "STORYOS_MYSQL_HOST",
    "STORYOS_MYSQL_PORT",
    "STORYOS_MYSQL_USER",
    "STORYOS_MYSQL_DB",
    "STORYOS_MYSQL_PWD",
    "STORYOS_REDIS_HOST",
    "STORYOS_REDIS_PORT",
    "STORYOS_REDIS_DB",
    "STORYOS_REDIS_PASSWORD",
    "STORYOS_REDIS_TIMEOUT",
    "STORYOS_EPISODE_META_STORE_MODE",
)


class _CleanEnv:
    """清空 STORYOS_* 连接变量，避免宿主环境影响断言；退出时原样恢复。"""

    def __enter__(self):
        self._saved = {key: os.environ.pop(key, None) for key in ENV_KEYS}
        return self

    def __exit__(self, *exc):
        for key in ENV_KEYS:
            os.environ.pop(key, None)
        for key, value in self._saved.items():
            if value is not None:
                os.environ[key] = value
        return False


class StorageConfigTests(unittest.TestCase):
    def test_yaml_declares_only_non_secret_topology(self):
        config = storyos_config.load_config()
        self.assertEqual(
            storyos_config.get_path(config, "storage.mysql.password_env"), "STORYOS_MYSQL_PWD"
        )
        self.assertEqual(
            storyos_config.get_path(config, "storage.redis.password_env"),
            "STORYOS_REDIS_PASSWORD",
        )
        self.assertEqual(
            storyos_config.get_path(config, "storage.mysql.database"), "story_os_runtime"
        )

    def test_yaml_defaults_used_when_env_absent(self):
        with _CleanEnv():
            mysql = storage_config.mysql_connection_kwargs()
            redis = storage_config.redis_connection_kwargs()
            episode_meta = storage_config.episode_meta_store_config()
        config = storyos_config.load_config()
        self.assertEqual(mysql["host"], storyos_config.get_path(config, "storage.mysql.host"))
        self.assertEqual(mysql["port"], storyos_config.get_path(config, "storage.mysql.port"))
        self.assertEqual(mysql["user"], storyos_config.get_path(config, "storage.mysql.user"))
        self.assertEqual(
            mysql["database"], storyos_config.get_path(config, "storage.mysql.database")
        )
        self.assertEqual(redis["host"], storyos_config.get_path(config, "storage.redis.host"))
        self.assertEqual(redis["port"], storyos_config.get_path(config, "storage.redis.port"))
        self.assertEqual(redis["db"], storyos_config.get_path(config, "storage.redis.db"))
        self.assertEqual(
            redis["timeout"],
            float(storyos_config.get_path(config, "storage.redis.timeout_seconds")),
        )
        self.assertEqual(episode_meta, {"mode": "json"})

    def test_episode_meta_store_allows_only_safe_migration_modes(self):
        with _CleanEnv():
            os.environ["STORYOS_EPISODE_META_STORE_MODE"] = "dual"
            self.assertEqual(storage_config.episode_meta_store_config(), {"mode": "dual"})
            os.environ["STORYOS_EPISODE_META_STORE_MODE"] = "mysql"
            with self.assertRaises(ValueError):
                storage_config.episode_meta_store_config()

    def test_env_overrides_yaml(self):
        with _CleanEnv():
            os.environ["STORYOS_MYSQL_HOST"] = "203.0.113.7"
            os.environ["STORYOS_MYSQL_PORT"] = "9000"
            os.environ["STORYOS_REDIS_TIMEOUT"] = "9"
            mysql = storage_config.mysql_connection_kwargs()
            redis = storage_config.redis_connection_kwargs()
        self.assertEqual(mysql["host"], "203.0.113.7")
        self.assertEqual(mysql["port"], 9000)
        self.assertEqual(redis["timeout"], 9.0)

    def test_explicit_parameter_beats_env_and_yaml(self):
        with _CleanEnv():
            os.environ["STORYOS_MYSQL_HOST"] = "203.0.113.7"
            mysql = storage_config.mysql_connection_kwargs(
                {"host": "198.51.100.4", "port": 1234}
            )
        self.assertEqual(mysql["host"], "198.51.100.4")
        self.assertEqual(mysql["port"], 1234)

    def test_credential_resolved_through_password_env_indirection(self):
        with _CleanEnv():
            os.environ["STORYOS_MYSQL_PWD"] = SECRET
            os.environ["STORYOS_REDIS_PASSWORD"] = SECRET
            self.assertEqual(storage_config.mysql_connection_kwargs()["password"], SECRET)
            self.assertEqual(storage_config.redis_connection_kwargs()["password"], SECRET)

    def test_password_key_absent_when_credential_not_provided(self):
        with _CleanEnv():
            self.assertNotIn("password", storage_config.mysql_connection_kwargs())
            self.assertNotIn("password", storage_config.redis_connection_kwargs())

    def test_summary_reports_presence_without_leaking_credential(self):
        with _CleanEnv():
            os.environ["STORYOS_MYSQL_PWD"] = SECRET
            summary = storage_config.storage_summary()
        self.assertNotIn(SECRET, json.dumps(summary, ensure_ascii=False))
        self.assertTrue(summary["mysql"]["password_present"])
        self.assertFalse(summary["redis"]["password_present"])

    def test_password_env_written_as_credential_literal_is_rejected(self):
        config = copy.deepcopy(storyos_config.load_config())
        config["storage"]["mysql"]["password_env"] = SECRET
        errors = storyos_config.validate(config)
        self.assertTrue([e for e in errors if "password_env" in e], errors)

    def test_missing_storage_section_fails_fast(self):
        config = copy.deepcopy(storyos_config.load_config())
        del config["storage"]
        self.assertIn("storage must be a mapping", storyos_config.validate(config))

    def test_redis_timeout_must_be_positive(self):
        config = copy.deepcopy(storyos_config.load_config())
        config["storage"]["redis"]["timeout_seconds"] = 0
        errors = storyos_config.validate(config)
        self.assertTrue([e for e in errors if "timeout_seconds" in e], errors)

    def test_connection_modules_stay_free_of_yaml_dependency(self):
        """platform/ 层必须保持零 yaml 依赖：依赖方向只能是 应用层 → 平台层。"""
        for rel in ("platform/repository/mysql/mysql_connection.py", "platform/state/redis_connection.py"):
            source = (ROOT / rel).read_text(encoding="utf-8")
            self.assertNotIn("storyos_config", source, rel)
            self.assertNotIn("storage_config", source, rel)
            self.assertNotIn("yaml", source, rel)


if __name__ == "__main__":
    unittest.main()
