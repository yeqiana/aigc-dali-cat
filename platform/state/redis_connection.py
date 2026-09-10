"""Redis 连接适配器（Story OS V3 Runtime State）。

P9.27：为 Runtime 实时状态层提供真实 Redis 客户端与健康检查。
配置全部来自环境变量，凭据不落盘。

环境变量：
    STORYOS_REDIS_HOST     默认 127.0.0.1
    STORYOS_REDIS_PORT     默认 6379
    STORYOS_REDIS_DB       默认 0
    STORYOS_REDIS_PASSWORD 无默认，运行时从环境读取
    STORYOS_REDIS_TIMEOUT  默认 5（秒）
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 5


class RedisConnection:
    """懒连接的 Redis 客户端适配器。

    构造时不建连，首次使用才按环境变量连接；这样导入与配置校验不需要真实实例。
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
        timeout: float | None = None,
        decode_responses: bool = True,
    ) -> None:
        self.host = host or os.environ.get("STORYOS_REDIS_HOST", "127.0.0.1")
        self.port = int(
            port if port is not None else os.environ.get("STORYOS_REDIS_PORT", "6379")
        )
        self.db = int(db if db is not None else os.environ.get("STORYOS_REDIS_DB", "0"))
        self.password = (
            password if password is not None
            else (os.environ.get("STORYOS_REDIS_PASSWORD") or None)
        )
        self.timeout = float(
            timeout if timeout is not None
            else os.environ.get("STORYOS_REDIS_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS))
        )
        self.decode_responses = decode_responses
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import redis

            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=self.decode_responses,
                socket_timeout=self.timeout,
                socket_connect_timeout=self.timeout,
            )
        return self._client

    def ping(self) -> bool:
        return bool(self.client.ping())

    def health_check(self) -> dict[str, Any]:
        """真实探活：连不上会抛异常，不做静默降级。"""
        server = self.client.info("server")
        memory = self.client.info("memory")
        keyspace = self.client.info("keyspace")
        return {
            "alive": self.ping(),
            "version": server.get("redis_version"),
            "mode": server.get("redis_mode"),
            "uptime_seconds": server.get("uptime_in_seconds"),
            "used_memory_human": memory.get("used_memory_human"),
            "keyspace": dict(keyspace),
        }

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

