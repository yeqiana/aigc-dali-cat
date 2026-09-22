from platform.repository.consistency_checker import RepositoryConsistencyChecker


def test_consistency_checker_match():
    checker = RepositoryConsistencyChecker()

    result = checker.compare(
        "event",
        [{"id": 1, "type": "TASK_STARTED"}],
        [{"id": 1, "type": "TASK_STARTED"}],
    )

    assert result.success
    assert result.matched == 1


def test_consistency_checker_mismatch():
    checker = RepositoryConsistencyChecker()

    result = checker.compare(
        "event",
        [{"id": 1, "type": "TASK_STARTED"}],
        [{"id": 1, "type": "TASK_FAILED"}],
    )

    assert not result.success
    assert result.mismatched == 1
