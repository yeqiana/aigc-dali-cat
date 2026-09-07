#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import story_json
import runtime_observability as obs


class RuntimeObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="obs-test-")
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name)

    def test_constants_match_existing_single_paths(self):
        import critic_runtime_v211
        import episode_performance
        import performance_guard_v211
        import quota_observability
        import runtime_daemon_event_bridge
        import workflow_observability
        import workflow_performance

        self.assertEqual(obs.EPISODE_PERFORMANCE_REL,
                         episode_performance.REL)
        self.assertEqual(obs.EPISODE_PERFORMANCE_REL,
                         critic_runtime_v211.EP_PERF_REL)
        self.assertEqual(obs.WORKFLOW_PERFORMANCE_REL,
                         workflow_performance.REL)
        self.assertEqual(obs.WORKFLOW_PERFORMANCE_REL,
                         performance_guard_v211.WORKFLOW_REL)
        self.assertEqual(obs.WORKFLOW_OBSERVABILITY_REL,
                         workflow_observability.REL)
        self.assertEqual(obs.QUOTA_OBSERVABILITY_REL,
                         quota_observability.REL)
        self.assertEqual(obs.TRACE_EVENTS_REL,
                         runtime_daemon_event_bridge.TRACE_REL)

    def test_write_summary_stamps_envelope(self):
        out = obs.write_summary(self.ep, obs.EPISODE_PERFORMANCE_REL,
                                kind="episode",
                                payload={"active_wall_seconds": 12.5})
        data = story_json.read_json(out)
        self.assertEqual(data["kind"], "episode")
        self.assertEqual(data["schema_version"], 1)
        self.assertIn("generated_at", data)
        self.assertEqual(data["active_wall_seconds"], 12.5)
        raw = out.read_bytes()
        self.assertTrue(raw.endswith(b"\n"))

    def test_write_summary_preserves_existing_fields(self):
        out = obs.write_summary(self.ep, obs.WORKFLOW_PERFORMANCE_REL,
                                kind="workflow",
                                payload={"schema_version": 3,
                                         "generated_at": "2026-01-01T00:00:00",
                                         "rows": []})
        data = story_json.read_json(out)
        self.assertEqual(data["schema_version"], 3)
        self.assertEqual(data["generated_at"], "2026-01-01T00:00:00")

    def test_unregistered_path_rejected(self):
        with self.assertRaises(ValueError):
            obs.write_summary(self.ep, Path("meta/other.json"), kind="x",
                              payload={})

    def test_trace_events_append_lines(self):
        a = obs.append_trace_event(self.ep, {"event": "a", "n": 1})
        b = obs.append_trace_event(self.ep, {"event": "b", "n": 2})
        self.assertEqual(a, b)
        lines = [line for line in a.read_text(encoding="utf-8").splitlines()
                 if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertEqual(story_json.read_json(a, default=None), None)


if __name__ == "__main__":
    unittest.main()
