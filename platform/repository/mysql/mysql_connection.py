"""MySQL 连接适配器（Story OS V3 Runtime Persistence）。

P9.26.4：提供真实 pymysql 连接、事务边界与最小连接管理。
P9.27 ：并发安全（每线程独立连接）、断连自动重连、健康检查，
        以及写入参数的时间归一化（aware -> naive UTC）。

配置全部来自环境变量，凭据不落盘。

环境变量：
    STORYOS_MYSQL_HOST   默认 127.0.0.1
    STORYOS_MYSQL_PORT   默认 3306
    STORYOS_MYSQL_USER   默认 root
    STORYOS_MYSQL_PWD    数据库密码（运行时从环境读取，禁止写入仓库）
    STORYOS_MYSQL_DB     默认 story_os_runtime
"""

from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Any

import pymysql
from pymysql.err import OperationalError

from platform.core.clock import to_naive_utc
from platform.repository.mysql.mysql_connection_pool import shared_pool

# 兼容旧导入路径：to_naive_utc 已移动到 platform.core.clock。
__all__ = ["MySqlConnection", "to_naive_utc"]

_UNSET = object()

# 服务端断开 / 连接丢失错误码：重连一次即可恢复。
_RECONNECT_ERROR_CODES = frozenset({2006, 2013, 2055})


class MySqlConnection:
    """pymysql 连接适配器。

    - 默认 autocommit=True：单条 execute 立即提交，保证 save() 的持久化语义。
    - 通过进程内有界 DBUtils 池借还连接，不跨线程同时共享物理连接。
    - 连接丢失（2006/2013/2055）时自动重连并重试一次。
    - transaction() 上下文管理器临时关闭 autocommit，提供 commit/rollback 边界。
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = _UNSET,
        charset: str = "utf8mb4",
        connect_timeout: int = 10,
        read_timeout: int = 10,
        write_timeout: int = 10,
    ) -> None:
        self.host = host or os.environ.get("STORYOS_MYSQL_HOST", "127.0.0.1")
        self.port = port or int(os.environ.get("STORYOS_MYSQL_PORT", "3306"))
        self.user = user or os.environ.get("STORYOS_MYSQL_USER", "root")
        self.password = (
            password if password is not None
            else os.environ.get("STORYOS_MYSQL_PWD", "")
        )
        if database is _UNSET:
            self.database = os.environ.get("STORYOS_MYSQL_DB", "story_os_runtime")
        else:
            self.database = database
        self.charset = charset
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self._local = threading.local()
        self._pool = shared_pool({
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "charset": self.charset,
            "autocommit": True,
            "connect_timeout": self.connect_timeout,
            "read_timeout": self.read_timeout,
            "write_timeout": self.write_timeout,
        })

    # ---- 连接管理 ----

    def _open(self) -> "pymysql.connections.Connection":
        """Compatibility helper used by tests and diagnostics."""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset=self.charset,
            autocommit=True,
            connect_timeout=self.connect_timeout,
            read_timeout=self.read_timeout,
            write_timeout=self.write_timeout,
        )

    @contextmanager
    def _borrow(self):
        """Borrow one pooled connection, or reuse the active transaction's one."""
        active = getattr(self._local, "transaction_connection", None)
        if active is not None:
            yield active
            return
        conn = self._pool.connection()
        try:
            yield conn
        finally:
            conn.close()

    def _with_reconnect(self, operation):
        in_transaction = getattr(self._local, "transaction_connection", None) is not None
        attempts = 1 if in_transaction else 2
        for attempt in range(attempts):
            try:
                with self._borrow() as conn:
                    return operation(conn)
            except OperationalError as exc:
                code = exc.args[0] if exc.args else None
                if code not in _RECONNECT_ERROR_CODES or attempt + 1 >= attempts:
                    raise

    @staticmethod
    def _normalize_params(params):
        if isinstance(params, tuple):
            return tuple(to_naive_utc(item) for item in params)
        if isinstance(params, list):
            return [to_naive_utc(item) for item in params]
        if isinstance(params, dict):
            return {key: to_naive_utc(value) for key, value in params.items()}
        return params

    # ---- 查询接口 ----

    def close(self) -> None:
        """Retained for call-site compatibility; operation scopes return leases."""
        return None

    def health_check(self) -> dict[str, Any]:
        """真实探活：连不上或查询失败会抛异常，不做静默降级。"""
        row = self.query_one(
            "SELECT VERSION() AS version, DATABASE() AS db, "
            "@@character_set_server AS charset, @@session.time_zone AS time_zone"
        ) or {}
        probe = self.query_one("SELECT 1 AS alive") or {}
        return {
            "alive": probe.get("alive") == 1,
            "version": row.get("version"),
            "database": row.get("db"),
            "charset": row.get("charset"),
            "time_zone": row.get("time_zone"),
        }

    def execute(self, sql: str, params: tuple | list | dict | None = None) -> int:
        params = self._normalize_params(params)

        def operation(conn) -> int:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.rowcount

        return self._with_reconnect(operation)

    def query_one(self, sql: str, params: tuple | list | dict | None = None) -> dict[str, Any] | None:
        params = self._normalize_params(params)

        def operation(conn) -> dict[str, Any] | None:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                row = cur.fetchone()
                if row is None:
                    return None
                cols = [d[0] for d in cur.description]
                return dict(zip(cols, row))

        return self._with_reconnect(operation)

    def query_all(self, sql: str, params: tuple | list | dict | None = None) -> list[dict[str, Any]]:
        params = self._normalize_params(params)

        def operation(conn) -> list[dict[str, Any]]:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in rows]

        return self._with_reconnect(operation)

    @contextmanager
    def transaction(self):
        """事务边界。块内 execute 与块外共用同一线程连接。

        注意：若块内发生断连重连，事务会退化为普通语句，需要上层重跑。
        """
        if getattr(self._local, "transaction_connection", None) is not None:
            raise RuntimeError("nested MySQL transactions are not supported")
        conn = self._pool.connection()
        try:
            # 证据门禁等长流程可能让池内空闲连接被远端 MySQL 断开。
            conn.ping(reconnect=True)
            conn.begin()
            self._local.transaction_connection = conn
            yield self
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._local.transaction_connection = None
            conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
