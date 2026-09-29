from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_scheduler  # noqa: E402


def test_scheduler_does_not_admit_when_episode_budget_has_no_capacity(tmp_path):
    ep = tmp_path
    q = {
        "items": [
            {"id": "r1", "frame": 4, "kind": "repair", "scope": "repair", "status": "queued", "depends_on": []},
        ]
    }
    saved = []

    async def fake_runtime(*_args, **_kwargs):
        raise AssertionError("worker runtime must not start when budget is exhausted")

    with patch.object(image_scheduler.resource_library, "ensure_fresh"), \
         patch.object(image_scheduler.production_recovery, "reconcile_locked"), \
         patch.object(image_scheduler.scheduler_core, "terminalize_superseded_history"), \
         patch.object(image_scheduler, "load_queue", return_value=q), \
         patch.object(image_scheduler, "save_queue", side_effect=lambda _ep, data: saved.append(data.copy())), \
         patch.object(image_scheduler, "ready_items", return_value=([q["items"][0]], [])), \
         patch.object(image_scheduler.runtime_router, "detect", return_value=("CODEX", "test")), \
         patch.object(image_scheduler.runtime_router, "image_execution_runtime", return_value=("CODEX", "test")), \
         patch.object(image_scheduler.raw_candidate_budget, "summary", return_value={"available": 0}), \
         patch.object(image_scheduler, "async_backend_worker", side_effect=fake_runtime):
        rc = asyncio.run(image_scheduler._run_scheduler_async(ep, 4, 30, None))

    assert rc in {0, 20, 22, 24}
    assert q["items"][0]["status"] == "queued"
