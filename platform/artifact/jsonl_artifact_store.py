from dataclasses import asdict
from pathlib import Path
import json

from platform.core.contracts.artifact_contract import ArtifactContract


class JsonlArtifactStore:
    """Phase 0 Artifact 索引存储。

    只保存资产引用，不管理真实媒体文件。
    """

    def __init__(self, path: str = ".storyos/artifacts.jsonl"):
        self.path = Path(path)

    def append(self, artifact: ArtifactContract) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(artifact), default=str, ensure_ascii=False) + "\n")

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

    def read_by_id(self, artifact_id: str) -> dict | None:
        """返回该 artifact_id 的最新一条记录（追加写，last-wins）。"""
        found = None
        for record in self.read_all():
            if record.get("artifact_id") == artifact_id:
                found = record
        return found
