import json

from platform.state.runtime_state_store import RuntimeStateStore


class RedisRuntimeStateStore(RuntimeStateStore):
    """Redis运行状态实现。

    生产环境通过Redis客户端连接。
    当前保留实现边界。
    """

    def __init__(self, client=None):
        self.client = client

    def set_state(self, key, value, expire_seconds=None):
        if self.client:
            self.client.set(key, json.dumps(value), ex=expire_seconds)

    def get_state(self, key):
        if not self.client:
            return None
        value = self.client.get(key)
        return json.loads(value) if value else None

    def delete_state(self, key):
        if self.client:
            self.client.delete(key)
