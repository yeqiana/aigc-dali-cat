#!/usr/bin/env python3
"""把 config/storyos.yaml#storage 解析成连接参数（应用层解析器）。

为什么放在 episodes/_system 而不是 platform/：
    platform/ 是基础设施层，对仓库配置文件保持零依赖——两个连接模块的
    docstring 都声明「配置全部来自环境变量，凭据不落盘」。本模块负责读配置，
    再把结果显式注入 MySqlConnection / RedisConnection，依赖方向始终是
    应用层 → 平台层，不会被倒置。

优先级（高 → 低，固定写死，不提供配置开关）：
    1. 调用方显式传入的参数
    2. 运行时环境变量
    3. config/storyos.yaml 的 storage 默认值

凭据只从 password_env 指名的环境变量读取。本模块不落盘、不打印凭据值；
需要出证据时用 storage_summary()，它只输出 password_present 布尔。
"""

from __future__ import annotations

import os
from typing import Any

import storyos_config

# 环境变量名沿用两个连接模块既有的约定，不新增第二套命名。
MYSQL_ENV_KEYS = {
    "host": "STORYOS_MYSQL_HOST",
    "port": "STORYOS_MYSQL_PORT",
    "user": "STORYOS_MYSQL_USER",
    "database": "STORYOS_MYSQL_DB",
}
REDIS_ENV_KEYS = {
    "host": "STORYOS_REDIS_HOST",
    "port": "STORYOS_REDIS_PORT",
    "db": "STORYOS_REDIS_DB",
    "timeout": "STORYOS_REDIS_TIMEOUT",
}


def _section(name: str) -> dict[str, Any]:
    """取 storage.<name>；缺失或类型不对时 fail-fast，不静默回落。"""
    cfg = storyos_config.load_config()
    section = storyos_config.get_path(cfg, f"storage.{name}")
    if not isinstance(section, dict):
        raise ValueError(f"CONFIG_INVALID: storage.{name} must be a mapping")
    return section


def _present(raw: Any) -> bool:
    return raw is not None and str(raw).strip() != ""


def _text(overrides: dict, key: str, env_name: str, default: Any) -> str:
    if key in overrides and overrides[key] is not None:
        return str(overrides[key])
    raw = os.environ.get(env_name)
    if _present(raw):
        return str(raw)
    return str(default)


def _integer(overrides: dict, key: str, env_name: str, default: Any) -> int:
    if key in overrides and overrides[key] is not None:
        return int(overrides[key])
    raw = os.environ.get(env_name)
    if _present(raw):
        return int(str(raw).strip())
    return int(default)


def _number(overrides: dict, key: str, env_name: str, default: Any) -> float:
    if key in overrides and overrides[key] is not None:
        return float(overrides[key])
    raw = os.environ.get(env_name)
    if _present(raw):
        return float(str(raw).strip())
    return float(default)


def _credential(env_name: str) -> str | None:
    """凭据只从运行时环境读。空串按「未提供」处理，与连接模块既有语义一致。"""
    raw = os.environ.get(env_name)
    if raw is None or raw == "":
        return None
    return raw


def mysql_connection_kwargs(overrides: dict | None = None) -> dict[str, Any]:
    """返回可直接展开给 MySqlConnection 的参数。

    password 只在对应环境变量确实存在时才出现；缺失时不出现在返回值里，交给
    MySqlConnection 自己的回退逻辑，保持与直接构造 MySqlConnection() 一致。
    """
    overrides = overrides or {}
    section = _section("mysql")
    kwargs: dict[str, Any] = {
        "host": _text(overrides, "host", MYSQL_ENV_KEYS["host"], section.get("host")),
        "port": _integer(overrides, "port", MYSQL_ENV_KEYS["port"], section.get("port")),
        "user": _text(overrides, "user", MYSQL_ENV_KEYS["user"], section.get("user")),
        "database": _text(
            overrides, "database", MYSQL_ENV_KEYS["database"], section.get("database")
        ),
    }
    password = _credential(str(section.get("password_env") or ""))
    if password is not None:
        kwargs["password"] = password
    return kwargs


def redis_connection_kwargs(overrides: dict | None = None) -> dict[str, Any]:
    """返回可直接展开给 RedisConnection 的参数。"""
    overrides = overrides or {}
    section = _section("redis")
    kwargs: dict[str, Any] = {
        "host": _text(overrides, "host", REDIS_ENV_KEYS["host"], section.get("host")),
        "port": _integer(overrides, "port", REDIS_ENV_KEYS["port"], section.get("port")),
        "db": _integer(overrides, "db", REDIS_ENV_KEYS["db"], section.get("db")),
        "timeout": _number(
            overrides, "timeout", REDIS_ENV_KEYS["timeout"], section.get("timeout_seconds")
        ),
    }
    password = _credential(str(section.get("password_env") or ""))
    if password is not None:
        kwargs["password"] = password
    return kwargs


def storage_summary() -> dict[str, Any]:
    """非凭据证据：只输出解析后的拓扑与「密码是否存在」，绝不输出密码值。

    返回的是连接「实际会用到」的值（已按 显式 > 环境变量 > yaml 解析），
    因此可以安全地代替巡检脚本里各自手抄的 env 摘要。
    """
    mysql_section = _section("mysql")
    redis_section = _section("redis")
    return {
        "mysql": {
            "host": _text({}, "host", MYSQL_ENV_KEYS["host"], mysql_section.get("host")),
            "port": _integer({}, "port", MYSQL_ENV_KEYS["port"], mysql_section.get("port")),
            "database": _text(
                {}, "database", MYSQL_ENV_KEYS["database"], mysql_section.get("database")
            ),
            "password_present": _credential(str(mysql_section.get("password_env") or "")) is not None,
        },
        "redis": {
            "host": _text({}, "host", REDIS_ENV_KEYS["host"], redis_section.get("host")),
            "port": _integer({}, "port", REDIS_ENV_KEYS["port"], redis_section.get("port")),
            "db": _integer({}, "db", REDIS_ENV_KEYS["db"], redis_section.get("db")),
            "password_present": _credential(str(redis_section.get("password_env") or "")) is not None,
        },
    }
