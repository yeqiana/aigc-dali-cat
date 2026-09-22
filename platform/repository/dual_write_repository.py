from typing import Protocol, Any


class RepositoryWriter(Protocol):
    def save(self, data: Any):
        ...


class DualWriteRepository:
    """双写迁移包装器。

    主链路保持不变，允许同时写入旧存储和新存储。
    """

    def __init__(self, primary: RepositoryWriter, secondary: RepositoryWriter):
        self.primary = primary
        self.secondary = secondary

    def save(self, data: Any):
        primary_result = self.primary.save(data)
        secondary_result = self.secondary.save(data)
        return {
            "primary": primary_result,
            "secondary": secondary_result,
        }
