"""Artifact 持久化抽象（与 event_repository.py 对称）。"""

from typing import Protocol

from platform.core.contracts.artifact_contract import ArtifactContract

__all__ = ["ArtifactRepository"]


class ArtifactRepository(Protocol):
    """Artifact 索引事实持久化抽象。

    只要求 save(artifact)，可由 JSONL / MySQL / DualWrite 任意实现承担。
    """

    def save(self, artifact: ArtifactContract) -> None:
        ...

