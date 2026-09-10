"""P9.27 生产写入链路接线：Runtime Repository Provider。

集中决定 Event / Trace / Artifact 三类 Runtime 事实写到哪里：

    jsonl  默认。Legacy JSONL，与 Phase 0 行为一致，不导入 pymysql。
    mysql  只写 MySQL（真实持久化）。
    dual   Legacy JSONL + MySQL 双写；secondary_enabled=False 可单独回滚 MySQL 侧。

环境变量：
    STORYOS_RUNTIME_STORE_MODE   jsonl | mysql | dual，默认 jsonl
    STORYOS_RUNTIME_JSONL_ROOT   Legacy 目录，默认 .storyos
    STORYOS_MYSQL_*              MySQL 连接参数，见 mysql_connection

约束：
    - 默认模式不改变既有行为，也不会因为缺少 pymysql 而失败。
    - 非法模式直接 ValueError，不做静默降级。
    - JSONL 模式复用 DualWrite 包装（mysql 侧为 None），三种模式的 save() 语义一致。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from platform.artifact.jsonl_artifact_store import JsonlArtifactStore
from platform.event.jsonl_event_store import JsonlEventStore
from platform.repository.dual_write import (
    DualWriteArtifactRepository,
    DualWriteEventRepository,
    DualWriteTraceRepository,
)
from platform.trace.jsonl_trace_store import JsonlTraceStore

STORE_MODE_ENV = "STORYOS_RUNTIME_STORE_MODE"
JSONL_ROOT_ENV = "STORYOS_RUNTIME_JSONL_ROOT"
DEFAULT_JSONL_ROOT = ".storyos"


class RuntimeStoreMode(str, Enum):
    """Runtime 事实存储模式。"""

    JSONL = "jsonl"
    MYSQL = "mysql"
    DUAL = "dual"


def resolve_store_mode(value: str | RuntimeStoreMode | None = None) -> RuntimeStoreMode:
    """解析存储模式；非法值直接报错，不静默降级。"""
    if isinstance(value, RuntimeStoreMode):
        return value
    raw = value if value is not None else os.environ.get(STORE_MODE_ENV)
    if raw is None or str(raw).strip() == "":
        return RuntimeStoreMode.JSONL
    normalized = str(raw).strip().lower()
    try:
        return RuntimeStoreMode(normalized)
    except ValueError:
        allowed = ", ".join(mode.value for mode in RuntimeStoreMode)
        raise ValueError(
            f"unknown {STORE_MODE_ENV}={raw!r}; allowed: {allowed}"
        ) from None


@dataclass(frozen=True)
class RuntimeObservers:
    """与仓库绑定的一组观察器。"""

    event: Any
    trace: Any
    artifact: Any


@dataclass(frozen=True)
class RuntimeRepositories:
    """三类 Runtime 事实仓库的组合。"""

    mode: RuntimeStoreMode
    event: Any
    trace: Any
    artifact: Any
    connection: Any = None

    def observers(self) -> RuntimeObservers:
        """构建与这些仓库绑定的观察器（函数内导入，避免 repository -> observer 顶层依赖）。"""
        from platform.observer.artifact_observer import ArtifactObserver
        from platform.observer.event_observer import EventObserver
        from platform.observer.trace_observer import TraceObserver

        return RuntimeObservers(
            event=EventObserver(self.event),
            trace=TraceObserver(self.trace),
            artifact=ArtifactObserver(self.artifact),
        )


def build_runtime_repositories(
    mode: str | RuntimeStoreMode | None = None,
    *,
    jsonl_root: str | None = None,
    connection: Any = None,
    secondary_enabled: bool = True,
) -> RuntimeRepositories:
    """按模式构建三类仓库。

    connection 为空且模式需要 MySQL 时，本函数自行创建 MySqlConnection 并写回
    RuntimeRepositories.connection，由调用方负责 close()。
    """
    resolved = resolve_store_mode(mode)
    root = jsonl_root or os.environ.get(JSONL_ROOT_ENV) or DEFAULT_JSONL_ROOT

    if resolved is RuntimeStoreMode.JSONL:
        return RuntimeRepositories(
            mode=resolved,
            event=DualWriteEventRepository(
                jsonl_store=JsonlEventStore(os.path.join(root, "events.jsonl"))
            ),
            trace=DualWriteTraceRepository(
                jsonl_store=JsonlTraceStore(os.path.join(root, "traces.jsonl"))
            ),
            artifact=DualWriteArtifactRepository(
                jsonl_store=JsonlArtifactStore(os.path.join(root, "artifacts.jsonl"))
            ),
        )

    # 只有 mysql / dual 模式才导入 pymysql 依赖链。
    from platform.repository.artifact.mysql_artifact_repository import (
        MySqlArtifactRepository,
    )
    from platform.repository.mysql.mysql_connection import MySqlConnection
    from platform.repository.mysql.mysql_event_repository import MySqlEventRepository
    from platform.repository.trace.mysql_trace_repository import MySqlTraceRepository

    if connection is None:
        connection = MySqlConnection()

    mysql_event = MySqlEventRepository(connection)
    mysql_trace = MySqlTraceRepository(connection)
    mysql_artifact = MySqlArtifactRepository(connection)

    if resolved is RuntimeStoreMode.MYSQL:
        return RuntimeRepositories(
            mode=resolved,
            event=mysql_event,
            trace=mysql_trace,
            artifact=mysql_artifact,
            connection=connection,
        )

    return RuntimeRepositories(
        mode=resolved,
        event=DualWriteEventRepository(
            JsonlEventStore(os.path.join(root, "events.jsonl")), mysql_event, secondary_enabled
        ),
        trace=DualWriteTraceRepository(
            JsonlTraceStore(os.path.join(root, "traces.jsonl")), mysql_trace, secondary_enabled
        ),
        artifact=DualWriteArtifactRepository(
            JsonlArtifactStore(os.path.join(root, "artifacts.jsonl")),
            mysql_artifact,
            secondary_enabled,
        ),
        connection=connection,
    )


class RuntimeRepositoryProvider:
    """惰性构建并缓存仓库组合；负责关闭自己创建的 MySQL 连接。"""

    def __init__(
        self,
        mode: str | RuntimeStoreMode | None = None,
        *,
        jsonl_root: str | None = None,
        connection: Any = None,
        secondary_enabled: bool = True,
    ):
        self.mode = resolve_store_mode(mode)
        self.jsonl_root = jsonl_root or os.environ.get(JSONL_ROOT_ENV) or DEFAULT_JSONL_ROOT
        self.secondary_enabled = secondary_enabled
        self._connection = connection
        self._owns_connection = False
        self._repositories: RuntimeRepositories | None = None
        self._observers: RuntimeObservers | None = None

    def repositories(self) -> RuntimeRepositories:
        if self._repositories is None:
            needs_mysql = self.mode is not RuntimeStoreMode.JSONL
            self._owns_connection = needs_mysql and self._connection is None
            self._repositories = build_runtime_repositories(
                self.mode,
                jsonl_root=self.jsonl_root,
                connection=self._connection,
                secondary_enabled=self.secondary_enabled,
            )
            self._connection = self._repositories.connection
        return self._repositories

    def observers(self) -> RuntimeObservers:
        if self._observers is None:
            self._observers = self.repositories().observers()
        return self._observers

    def health_check(self) -> dict[str, Any]:
        """真实探活：jsonl 模式只报目录，mysql / dual 模式真连数据库。"""
        repositories = self.repositories()
        result: dict[str, Any] = {
            "mode": self.mode.value,
            "jsonl_root": (
                self.jsonl_root
                if self.mode is not RuntimeStoreMode.MYSQL
                else None
            ),
        }
        if repositories.connection is not None:
            result["mysql"] = repositories.connection.health_check()
        return result

    def close(self) -> None:
        """只关闭自己创建的连接；注入的连接不动。"""
        if self._owns_connection and self._connection is not None:
            self._connection.close()
        self._repositories = None
        self._observers = None
        self._connection = None
        self._owns_connection = False

    def __enter__(self) -> "RuntimeRepositoryProvider":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False


def build_runtime_repository_provider(
    mode: str | RuntimeStoreMode | None = None,
    **kwargs,
) -> RuntimeRepositoryProvider:
    """便捷构造入口。"""
    return RuntimeRepositoryProvider(mode, **kwargs)
