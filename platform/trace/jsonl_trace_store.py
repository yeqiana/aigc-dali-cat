from dataclasses import asdict
from pathlib import Path
import json

from platform.core.contracts.trace_contract import TraceContract


class JsonlTraceStore:
    """Phase 0 Trace 持久化。

    记录执行事实，不参与调度、重试和门禁。
    """

    def __init__(self, path: str = ".storyos/traces.jsonl"):
        self.path = Path(path)

    def append(self, trace: TraceContract) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(trace), default=str, ensure_ascii=False) + "\n")

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

    def read_by_id(self, trace_id: str, span_id: str) -> dict | None:
        """返回该 (trace_id, span_id) 的最新一条记录。

        Trace 的 RUNNING 先落一次，完成态用同一主键再落一次，
        只有最后一行代表当前状态，必须 last-wins。
        """
        found = None
        for record in self.read_all():
            if record.get("trace_id") == trace_id and record.get("span_id") == span_id:
                found = record
        return found
