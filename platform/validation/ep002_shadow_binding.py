from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class EP002RuntimeBinding:
    """EP002 shadow binding descriptor.

    Shadow mode only. It does not mutate episode state or replace production runtime.
    """

    episode_id: str = "10-02"
    episode_path: str = "episodes/10_彼此的天上/02_玻璃另一边的手"
    mode: str = "SHADOW"

    def build_context(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "episode_path": self.episode_path,
            "mode": self.mode,
        }

    def validate_assets(self) -> bool:
        return Path(self.episode_path).exists()


def create_ep002_shadow_binding() -> EP002RuntimeBinding:
    return EP002RuntimeBinding()
