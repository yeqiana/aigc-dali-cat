import json
from pathlib import Path

import pytest

from platform.core.clock import utc_now
from platform.core.contracts.event_contract import EventContract
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.repository.dual_write import DualWriteEventRepository
from platform.repository.runtime_repository_provider import (
    RuntimeRepositoryProvider,
    RuntimeStoreMode,
    build_runtime_repositories,
    resolve_store_mode,
)


class FakeConnection:
    """只记录调用，不连接真实 MySQL。"""

    def __init__(self):
        self.calls = []
        self.closed = False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        return 1

    def query_one(self, sql, params=None):
        return {
            "alive": 1,
            "version": "8.0.fake",
            "database": "story_os_runtime",
            "charset": "utf8mb4",
            "time_zone": "SYSTEM",
        }

    def query_all(self, sql, params=None):
        return []

    def health_check(self):
        return {
            "alive": True,
            "version": "8.0.fake",
            "database": "story_os_runtime",
            "charset": "utf8mb4",
            "time_zone": "SYSTEM",
        }

    def close(self):
        self.closed = True


def _event(event_id: str = 'evt_wire') -> EventContract:
    return EventContract(
        event_id=event_id,
        event_type=EventType.TASK_STARTED,
        aggregate_type=EntityType.TASK,
        aggregate_id='task1',
        occurred_at=utc_now(),
    )


def _jsonl_rows(path) -> list:
    text = Path(path).read_text(encoding='utf-8')
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def test_default_mode_is_jsonl_and_writes_legacy_only(tmp_path, monkeypatch):
    monkeypatch.delenv('STORYOS_RUNTIME_STORE_MODE', raising=False)
    monkeypatch.delenv('STORYOS_RUNTIME_JSONL_ROOT', raising=False)
    repos = build_runtime_repositories(jsonl_root=str(tmp_path))

    assert repos.mode is RuntimeStoreMode.JSONL
    assert repos.connection is None
    assert isinstance(repos.event, DualWriteEventRepository)
    assert repos.event.mysql_repository is None
    assert repos.event.save(_event()) == {'legacy': 'OK', 'mysql': 'SKIPPED'}
    assert len(_jsonl_rows(tmp_path / 'events.jsonl')) == 1


def test_jsonl_root_env_is_honored(tmp_path, monkeypatch):
    monkeypatch.setenv('STORYOS_RUNTIME_JSONL_ROOT', str(tmp_path))
    repos = build_runtime_repositories()
    repos.event.save(_event())

    assert (tmp_path / 'events.jsonl').exists()


def test_mode_resolution_from_env(monkeypatch):
    monkeypatch.setenv('STORYOS_RUNTIME_STORE_MODE', 'DUAL')
    assert resolve_store_mode() is RuntimeStoreMode.DUAL
    monkeypatch.setenv('STORYOS_RUNTIME_STORE_MODE', '   ')
    assert resolve_store_mode() is RuntimeStoreMode.JSONL
    monkeypatch.delenv('STORYOS_RUNTIME_STORE_MODE', raising=False)
    assert resolve_store_mode() is RuntimeStoreMode.JSONL
    assert resolve_store_mode(RuntimeStoreMode.MYSQL) is RuntimeStoreMode.MYSQL


def test_invalid_mode_raises_instead_of_silently_falling_back(tmp_path):
    with pytest.raises(ValueError) as excinfo:
        build_runtime_repositories('postgres', jsonl_root=str(tmp_path))

    assert 'STORYOS_RUNTIME_STORE_MODE' in str(excinfo.value)
    assert list(tmp_path.iterdir()) == []


def test_jsonl_mode_never_constructs_mysql_connection(tmp_path, monkeypatch):
    from platform.repository.mysql import mysql_connection as mysql_module

    def boom(*args, **kwargs):
        raise AssertionError('jsonl mode must not create a MySQL connection')

    monkeypatch.setattr(mysql_module, 'MySqlConnection', boom)
    repos = build_runtime_repositories(jsonl_root=str(tmp_path))

    assert repos.connection is None


def test_mysql_stack_is_imported_lazily():
    import ast

    from platform.repository import runtime_repository_provider as module

    source = Path(module.__file__).read_text(encoding='utf-8')
    tree = ast.parse(source)
    module_level_imports = '\n'.join(
        ast.dump(node)
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )

    # 模块顶层不得触碰 MySQL 依赖链；只有 mysql / dual 分支函数体内才导入。
    assert 'mysql' not in module_level_imports


def test_dual_mode_writes_legacy_and_mysql(tmp_path):
    connection = FakeConnection()
    repos = build_runtime_repositories('dual', jsonl_root=str(tmp_path), connection=connection)

    event = _event('evt_dual_path')
    assert repos.event.save(event) == {'legacy': 'OK', 'mysql': 'OK'}
    assert len(_jsonl_rows(tmp_path / 'events.jsonl')) == 1
    sql, params = connection.calls[0]
    assert 'INSERT INTO event_log' in sql
    assert params[0] == 'evt_dual_path'


def test_dual_mode_rollback_switch_skips_mysql(tmp_path):
    connection = FakeConnection()
    repos = build_runtime_repositories(
        'dual', jsonl_root=str(tmp_path), connection=connection, secondary_enabled=False
    )

    assert repos.event.save(_event()) == {'legacy': 'OK', 'mysql': 'SKIPPED'}
    assert connection.calls == []
    assert len(_jsonl_rows(tmp_path / 'events.jsonl')) == 1


def test_mysql_mode_writes_only_mysql(tmp_path):
    connection = FakeConnection()
    repos = build_runtime_repositories('mysql', jsonl_root=str(tmp_path), connection=connection)

    repos.event.save(_event('evt_mysql_only'))

    assert connection.calls
    assert not (tmp_path / 'events.jsonl').exists()


def test_observers_are_bound_to_the_same_repositories(tmp_path):
    from platform.core.enums.artifact_type import ArtifactType

    provider = RuntimeRepositoryProvider(jsonl_root=str(tmp_path))
    observers = provider.observers()

    event = observers.event.record(EventType.TASK_STARTED, EntityType.TASK, 'task-1')
    artifact = observers.artifact.register(
        ArtifactType.IMAGE, 'images/a.png', 'b' * 64, EntityType.TASK, 'task-1', 'tester'
    )
    trace = observers.trace.start('agent.execute')

    assert _jsonl_rows(tmp_path / 'events.jsonl')[0]['event_id'] == event.event_id
    assert _jsonl_rows(tmp_path / 'artifacts.jsonl')[0]['artifact_id'] == artifact.artifact_id
    assert _jsonl_rows(tmp_path / 'traces.jsonl')[0]['trace_id'] == trace.trace_id
    assert provider.observers() is observers


def test_provider_only_closes_connections_it_owns(tmp_path):
    injected = FakeConnection()
    provider = RuntimeRepositoryProvider('dual', jsonl_root=str(tmp_path), connection=injected)
    provider.repositories()
    assert provider._owns_connection is False
    provider.close()
    assert injected.closed is False

    owned = RuntimeRepositoryProvider('dual', jsonl_root=str(tmp_path))
    owned.repositories()
    assert owned._owns_connection is True
    owned.close()
    assert owned._connection is None


def test_provider_caches_repositories(tmp_path):
    provider = RuntimeRepositoryProvider(jsonl_root=str(tmp_path))
    assert provider.repositories() is provider.repositories()


def test_health_check_reports_mode_and_mysql(tmp_path):
    jsonl_provider = RuntimeRepositoryProvider(jsonl_root=str(tmp_path))
    jsonl_health = jsonl_provider.health_check()
    assert jsonl_health['mode'] == 'jsonl'
    assert jsonl_health['jsonl_root'] == str(tmp_path)
    assert 'mysql' not in jsonl_health

    dual_provider = RuntimeRepositoryProvider(
        'dual', jsonl_root=str(tmp_path), connection=FakeConnection()
    )
    dual_health = dual_provider.health_check()
    assert dual_health['mode'] == 'dual'
    assert dual_health['mysql']['alive'] is True
