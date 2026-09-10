from pathlib import Path
import json

from platform.core.clock import utc_now


class EpRuntimeObservationProbe:
    """EP运行旁路观测探针。

    只读取Episode现有事实，不修改任何meta状态文件。
    """

    def inspect(self, episode_path: str) -> dict:
        root = Path(episode_path)
        meta = root / "meta"

        files = {
            "episode_state": meta / "episode-state.json",
            "runtime_request": meta / "runtime-request.json",
            "workflow_observability": meta / "workflow-observability.json",
            "production_ledger": meta / "production-ledger.json",
        }

        result = {
            "episode": str(root),
            "checked_at": utc_now().isoformat(),
            "read_only": True,
            "facts": {},
        }

        for name, path in files.items():
            if path.exists():
                result["facts"][name] = json.loads(path.read_text(encoding="utf-8"))
            else:
                result["facts"][name] = None

        return result
