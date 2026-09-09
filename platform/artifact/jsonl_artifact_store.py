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
