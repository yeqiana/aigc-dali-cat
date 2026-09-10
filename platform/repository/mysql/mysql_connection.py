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

# 兼容旧导入路径：to_naive_utc 已移动到 platform.core.clock。
__all__ = ["MySqlConnection", "to_naive_utc"]

_UNSET = object()

# 服务端断开 / 连接丢失错误码：重连一次即可恢复。
_RECONNECT_ERROR_CODES = frozenset({2006, 2013, 2055})


class MySqlConnection:
    """pymysql 连接适配器。

    - 默认 autocommit=True：单条 execute 立即提交，保证 save() 的持久化语义。
    - 每线程持有独立连接（pymysql Connection 非线程安全，不能跨线程复用）。
    - 连接丢失（2006/2013/2055）时自动重连并重试一次。
    - transaction() 上下文管理器临时关闭 autocommit，提供 commit/rollback 边界。

    已知边界：这是“每线程连接”而非连接池，没有上限与空闲回收；
    长期驻留进程若持续创建新线程，需要上层控制线程数量。
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
        self._connections: list[Any] = []
        self._lock = threading.RLock()

    # ---- 连接管理 ----

    def _open(self) -> "pymysql.connections.Connection":
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

    def _ensure_connected(self) -> "pymysql.connections.Connection":
        conn = getattr(self._local, "connection", None)
        if conn is not None and getattr(conn, "open", False):
            return conn
        if conn is not None:
            self._forget(conn)
        conn = self._open()
        self._local.connection = conn
        with self._lock:
            self._connections.append(conn)
        return conn

    def _forget(self, conn) -> None:
        if getattr(self._local, "connection", None) is conn:
            self._local.connection = None
        with self._lock:
            if conn in self._connections:
                self._connections.remove(conn)
        try:
            conn.close()
        except Exception:
            pass

    def _with_reconnect(self, operation):
        try:
            return operation()
        except OperationalError as exc:
            code = exc.args[0] if exc.args else None
            if code not in _RECONNECT_ERROR_CODES:
                raise
            conn = getattr(self._local, "connection", None)
            if conn is not None:
                self._forget(conn)
            return operation()

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
        with self._lock:
            connections = list(self._connections)
            self._connections.clear()
        self._local.connection = None
        for conn in connections:
            try:
                conn.close()
            except Exception:
                pass

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

        def operation() -> int:
            conn = self._ensure_connected()
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                return cur.rowcount

        return self._with_reconnect(operation)

    def query_one(self, sql: str, params: tuple | list | dict | None = None) -> dict[str, Any] | None:
        params = self._normalize_params(params)

        def operation() -> dict[str, Any] | None:
            conn = self._ensure_connected()
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

        def operation() -> list[dict[str, Any]]:
            conn = self._ensure_connected()
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
        conn = self._ensure_connected()
        conn.autocommit(False)
        try:
            yield self
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.autocommit(True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

