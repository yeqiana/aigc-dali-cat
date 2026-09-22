from abc import ABC, abstractmethod


class RuntimeStateStore(ABC):
    """Runtime实时状态存储抽象，不保存历史事实。"""

    @abstractmethod
    def set_state(self, key, value, expire_seconds=None):
        raise NotImplementedError

    @abstractmethod
    def get_state(self, key):
        raise NotImplementedError

    @abstractmethod
    def delete_state(self, key):
        raise NotImplementedError
