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
