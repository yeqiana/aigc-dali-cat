from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/p2_visual_narrative_cutover_gate.py"
SPEC = importlib.util.spec_from_file_location("visual_cutover_gate", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class VisualCutoverGateTests(unittest.TestCase):
    def fixture(self, root: Path):
        for rel in gate.SOURCES.values():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
        docs = {
            "p0": {"kind": "p0_agent_protocol_acceptance", "commit_gate_ready": True},
            "character_cutover": {"status": "PRODUCTION_ENABLED", "production_cutover_performed": True},
            "character_health": {"status": "PASS", "adapter_state": {"production_enabled": True, "shadow_enabled": False}},
            "world_gate": {"status": "BLOCKED", "blockers": ["WORLD_NO_MEASURABLE_AGENT_VALUE"]},
            "world_value_probe": {"final_decision": "WORLD_PRODUCTION_NO_GO"},
            "visual_smoke": {"episode": "episodes/test", "status": "PASS", "checks": {
                "candidate_parse": True, "candidate_valid": True, "semantic_pass": True,
                "current_host_pointer_unchanged": True, "image_generation_not_invoked": True,
            }, "telemetry": {"complete": True, "real_model_execution": True,
                "failure": False, "timeout": False, "returncode": 0}},
            "visual_benchmark": {"valid_pair_count": 5, "telemetry_complete": True,
                "semantic_equivalence": True, "authority_zero_regression": True,
                "safety_checks": {"all_valid_pairs_semantic_equivalent": True,
                    "authority_zero_regression": True, "fixed_provider_model_reasoning": True,
                    "wall_regression_within_5pct": True, "token_regression_within_10pct": True,
                    "no_failure_timeout": True, "telemetry_complete": True},
                "provider": "provider", "model": "model", "reasoning_effort": "medium",
                "performance": {"wall_regression_fraction": -0.68, "token_regression_fraction": 0.007},
                "value_checks": {"speed_value_ge_10pct": True}, "measurable_value": True},
        }
        for name, rel in gate.SOURCES.items():
            (root / rel).write_text(json.dumps(docs[name]), encoding="utf-8")
        cfg = root / "config/storyos.yaml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "config/storyos.yaml", cfg)
        config_text = cfg.read_text(encoding="utf-8")
        config_text = config_text.replace(
            "visual_narrative_prepare:\n      shadow_enabled: false\n      production_enabled: true",
            "visual_narrative_prepare:\n      shadow_enabled: true\n      production_enabled: false",
        )
        cfg.write_text(config_text, encoding="utf-8")
        (root / "episodes/test/meta").mkdir(parents=True)
        (root / "episodes/test/meta/episode-state.json").write_text(
            json.dumps({"current_state": "STORYBOARD_LOCKED"}), encoding="utf-8")

    def test_ready_happy_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            report = gate.evaluate(root, generated_at="2026-09-27T00:00:00+00:00")
            self.assertEqual(report["status"], "READY", report["blockers"])
            self.assertTrue(report["immutable"])
            self.assertFalse(report["production_cutover_performed"])

    def test_missing_smoke_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            (root / gate.SOURCES["visual_smoke"]).unlink()
            report = gate.evaluate(root)
            self.assertEqual(report["status"], "BLOCKED")

    def test_smoke_failure_is_blocked(self):
        self.assert_blocked("visual_smoke", lambda d: d.update(status="FAIL"))

    def test_fewer_than_five_pairs_is_blocked(self):
        self.assert_blocked("visual_benchmark", lambda d: d.update(valid_pair_count=4))

    def test_semantic_mismatch_is_blocked(self):
        self.assert_blocked("visual_benchmark", lambda d: d.update(semantic_equivalence=False))

    def test_incomplete_telemetry_is_blocked(self):
        self.assert_blocked("visual_benchmark", lambda d: d.update(telemetry_complete=False))

    def test_authority_regression_is_blocked(self):
        self.assert_blocked("visual_benchmark", lambda d: d.update(authority_zero_regression=False))

    def test_no_measurable_value_is_blocked(self):
        self.assert_blocked("visual_benchmark", lambda d: d.update(measurable_value=False))

    def test_unexpected_production_flag_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            cfg = root / "config/storyos.yaml"
            text = cfg.read_text(encoding="utf-8")
            text = text.replace("visual_narrative_prepare:\n      shadow_enabled: true\n      production_enabled: false",
                                "visual_narrative_prepare:\n      shadow_enabled: true\n      production_enabled: true", 1)
            cfg.write_text(text, encoding="utf-8")
            self.assertEqual(gate.evaluate(root)["status"], "BLOCKED")

    def test_immutable_evidence_write_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "gate.json"
            path.write_text("original", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                gate.write_immutable({"status": "READY"}, path)
            self.assertEqual(path.read_text(encoding="utf-8"), "original")

    def assert_blocked(self, doc_name, mutate):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); self.fixture(root)
            path = root / gate.SOURCES[doc_name]
            doc = json.loads(path.read_text(encoding="utf-8")); mutate(doc)
            path.write_text(json.dumps(doc), encoding="utf-8")
            self.assertEqual(gate.evaluate(root)["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
