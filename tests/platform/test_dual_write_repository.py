class FakeRepository:
    def __init__(self):
        self.values = []

    def save(self, data):
        self.values.append(data)
        return True


def test_dual_write_repository():
    from platform.repository.dual_write_repository import DualWriteRepository

    primary = FakeRepository()
    secondary = FakeRepository()

    repository = DualWriteRepository(primary, secondary)
    result = repository.save({"event": "TASK_STARTED"})

    assert result["primary"] is True
    assert result["secondary"] is True
    assert len(primary.values) == 1
    assert len(secondary.values) == 1
