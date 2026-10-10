"""Even with a production ACK, plan/status are strictly observational."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import storyos_multi_episode as multi


def test_ack_argument_does_not_turn_plan_into_start(tmp_path, capsys):
    a, b = (tmp_path / "episodes" / name for name in ("alpha", "beta"))
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    with (patch.object(multi, "ROOT", tmp_path),
          patch.object(multi, "start_episodes", side_effect=AssertionError("production started")) as start,
          patch.object(multi, "multi_status", return_value={
              "authority": "DIAGNOSTIC_ONLY", "model_calls": 0,
              "episode_count": 2, "episodes": [],
              "global_image_capacity": {"global_max_inflight_images": 5,
                                        "advisory_snapshot_only": True}})):
        assert multi.main(["plan", "--episode", str(a), "--episode", str(b),
                           "--ack-real-production"]) == 0
    assert '"model_calls": 0' in capsys.readouterr().out
    start.assert_not_called()


def test_status_always_avoids_production_launch(tmp_path, capsys):
    a, b = (tmp_path / "episodes" / name for name in ("alpha", "beta"))
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    with (patch.object(multi, "ROOT", tmp_path),
          patch.object(multi, "start_episodes", side_effect=AssertionError("production started")) as start,
          patch.object(multi, "multi_status", return_value={
              "authority": "DIAGNOSTIC_ONLY", "model_calls": 0,
              "episode_count": 2, "episodes": [],
              "global_image_capacity": {"advisory_snapshot_only": True}})):
        assert multi.main(["status", "--episode", str(a), "--episode", str(b)]) == 0
    start.assert_not_called()
