from dataclasses import asdict
from pathlib import Path
import json

from platform.core.contracts.event_contract import EventContract


class JsonlEventStore:
    """Phase 0 Event 持久化。

    使用追加写 JSONL，未来可平滑迁移到 MySQL Event 表。
    不承担状态计算。
    """

    def __init__(self, path: str = ".storyos/events.jsonl"):
        self.path = Path(path)

    def append(self, event: EventContract) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(event), default=str, ensure_ascii=False) + "\n")
