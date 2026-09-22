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

    def read_all(self) -> list[dict]:
        """按写入顺序读取全部 legacy 记录（P9.26.6 一致性校验用）。"""
        if not self.path.exists():
            return []
        records: list[dict] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def read_by_id(self, event_id: str) -> dict | None:
        """返回该主键的最新一条记录。

        JSONL 是追加写：同一主键被重复写入时最后一行才代表当前状态，
        因此必须 last-wins，与巡检 _collect 的口径保持一致。
        """
        found = None
        for record in self.read_all():
            if record.get("event_id") == event_id:
                found = record
        return found
