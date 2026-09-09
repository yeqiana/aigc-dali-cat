from platform.repository.migration_drill import MigrationDrill


def test_migration_drill_match():
    result = MigrationDrill().verify(
        "event",
        [{"id": 1, "type": "TASK_STARTED"}],
        [{"id": 1, "type": "TASK_STARTED"}],
    )

    assert result.success is True


def test_migration_drill_mismatch():
    result = MigrationDrill().verify(
        "event",
        [{"id": 1}],
        [{"id": 2}],
    )

    assert result.success is False
