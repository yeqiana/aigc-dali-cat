from datetime import datetime, timezone

from platform.core.contracts.event_contract import EventContract
from platform.core.enums.entity_type import EntityType
from platform.core.enums.event_type import EventType
from platform.repository.dual_write import DualWriteEventRepository


class FakeLegacyStore:
    def __init__(self):
        self.items = []

    def append(self, entity):
        self.items.append(entity)


class FakeMysqlRepository:
    def __init__(self):
        self.saved = []

    def save(self, entity):
        self.saved.append(entity)


def _event():
    return EventContract(
        event_id="evt_dual",
        event_type=EventType.TASK_STARTED,
        aggregate_type=EntityType.TASK,
        aggregate_id="task1",
        occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


def test_dual_write_writes_both_stores():
    legacy = FakeLegacyStore()
    mysql = FakeMysqlRepository()
    repo = DualWriteEventRepository(legacy, mysql)

    result = repo.save(_event())

    assert result == {"legacy": "OK", "mysql": "OK"}
    assert len(legacy.items) == 1
    assert len(mysql.saved) == 1


def test_dual_write_skips_mysql_when_disabled():
    legacy = FakeLegacyStore()
    mysql = FakeMysqlRepository()
    repo = DualWriteEventRepository(legacy, mysql, secondary_enabled=False)

    result = repo.save(_event())

    assert result == {"legacy": "OK", "mysql": "SKIPPED"}
    assert len(legacy.items) == 1
    assert len(mysql.saved) == 0


def test_dual_write_legacy_only_without_mysql():
    legacy = FakeLegacyStore()
    repo = DualWriteEventRepository(legacy)

    result = repo.save(_event())

    assert result == {"legacy": "OK", "mysql": "SKIPPED"}
    assert len(legacy.items) == 1


def test_event_repository_reexport_backward_compatible():
    from platform.repository.event_repository import DualWriteEventRepository as LegacyImport
    from platform.repository.dual_write import DualWriteEventRepository as NewImport

    assert LegacyImport is NewImport
