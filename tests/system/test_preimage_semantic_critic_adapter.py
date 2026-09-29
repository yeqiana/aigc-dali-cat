from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))
sys.path.insert(0, str(ROOT / "episodes/_system/agents"))

import preimage_authority_snapshot as snapshots
import preimage_task_contract as contract
import preimage_semantic_critic_adapter as critic


class PreimageSemanticCriticAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p3-preimage-critic-", dir=ROOT / ".storyos")
        self.ep = Path(self.temp.name)
        (self.ep / "meta").mkdir(parents=True, exist_ok=True)
        (self.ep / "meta/story-gates.json").write_text(
            json.dumps({"schema_version": 1, "story": {"source": "frozen"}, "visual": {}}), encoding="utf-8"
        )
        self.snapshot = snapshots.build(self.ep)
        rows = contract.plan_tasks(self.ep, self.snapshot)
        for task in rows:
            candidate = contract.candidate_template(task, contract.valid_payload(task))
            self.assertEqual(contract.write_candidate(self.ep, task, candidate), [])
            contract.update_task_state(self.ep, task, "COMPLETED")
        self.rows = contract.plan_tasks(self.ep, self.snapshot, resume=True)

    def tearDown(self):
        self.temp.cleanup()

    def capsule(self):
        return critic.build_frozen_candidate_set(self.ep, self.snapshot, self.rows)

    def test_frozen_candidate_set_binds_all_four_canonical_scopes(self):
        capsule = self.capsule()
        self.assertEqual(set(capsule["candidate_set"]), set(contract.TASK_TYPES))
        self.assertTrue(all(row["status"] == "REUSED" for row in self.rows))
        self.assertEqual(capsule["canonical_checks"]["all_task_contract_verifiers_pass"], True)
        self.assertEqual(capsule["authority_write"], False)

    def test_source_sha_drift_fails_closed(self):
        gates = self.ep / "meta/story-gates.json"
        gates.write_text(json.dumps({"schema_version": 1, "story": {"source": "changed"}, "visual": {}}), encoding="utf-8")
        with self.assertRaisesRegex(critic.PreimageCriticError, "stale"):
            self.capsule()

    def test_applicability_not_applicable_scope_is_not_flagged(self):
        capsule = self.capsule()
        world = capsule["candidate_set"]["WORLD_PREPARE"]["candidate"]["payload"]
        for value in world.values():
            value.clear()
            value["applicable"] = False
        capsule["applicability"] = {
            scope: {"applicability": "NOT_APPLICABLE"}
            for scope in world
        }
        self.assertEqual(critic.cross_scope_fact_conflicts(capsule), [])

    def test_two_individually_valid_candidates_surface_cross_scope_conflict(self):
        capsule = self.capsule()
        character = capsule["candidate_set"]["CHARACTER_FINALIZE"]["candidate"]["payload"]["character.finalize"]
        character["identity"] = "person-a"
        world = capsule["candidate_set"]["WORLD_PREPARE"]["candidate"]["payload"]
        world["visual.world_identity"]["applicable"] = True
        world["visual.world_identity"]["identity"] = "person-b"
        capsule["applicability"]["visual.world_identity"]["applicability"] = "APPLICABLE"
        self.assertEqual(critic.cross_scope_fact_conflicts(capsule)[0]["issue_code"], "PREIMAGE_CROSS_SCOPE_FACT_CONFLICT")

    def test_missing_task_or_invalid_candidate_set_rejected(self):
        with self.assertRaisesRegex(critic.PreimageCriticError, "incomplete"):
            critic.build_frozen_candidate_set(self.ep, self.snapshot, self.rows[:-1])
        candidate = contract.read_candidate(self.ep, self.rows[0])
        candidate["authority_scope"] = []
        contract.candidate_path(self.ep, self.rows[0]["task_type"]).write_text(json.dumps(candidate), encoding="utf-8")
        with self.assertRaisesRegex(critic.PreimageCriticError, "not finalized|verifier"):
            self.capsule()

    def test_visual_missing_required_scope_fails_before_request_creation(self):
        visual_task = next(row for row in self.rows if row["task_type"] == "VISUAL_NARRATIVE_PREPARE")
        candidate_path = contract.candidate_path(self.ep, visual_task["task_type"])
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        candidate["payload"].pop("visual.shot_progression")
        candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        with patch.object(critic, "adapter_config", return_value={"shadow_enabled": True, "production_enabled": False}), \
             patch.object(critic.product_review_adapter, "prepare") as prepare:
            with self.assertRaisesRegex(critic.PreimageCriticError, "canonical candidate verifier"):
                critic.prepare_after_candidate_set(self.ep, self.snapshot, self.rows)
        prepare.assert_not_called()

    def test_candidate_or_obligation_binding_drift_rejected(self):
        capsule = self.capsule()
        changed = dict(capsule)
        changed["obligation_sha256"] = "f" * 64
        with patch.object(critic, "adapter_config", return_value={"shadow_enabled": True, "production_enabled": False}):
            with self.assertRaisesRegex(critic.PreimageCriticError, "SHA mismatch"):
                critic.prepare_shadow_request(self.ep, changed)
        character_task = next(row for row in self.rows if row["task_type"] == "CHARACTER_FINALIZE")
        path = contract.candidate_path(self.ep, character_task["task_type"])
        candidate = json.loads(path.read_text(encoding="utf-8"))
        candidate["payload"]["character.finalize"]["identity"] = "updated-after-freeze"
        path.write_text(json.dumps(candidate), encoding="utf-8")
        with patch.object(critic, "adapter_config", return_value={"shadow_enabled": True, "production_enabled": False}):
            with self.assertRaisesRegex(critic.PreimageCriticError, "changed after freeze"):
                critic.prepare_shadow_request(self.ep, capsule)

    def test_missing_applicability_binding_fails_closed(self):
        capsule = self.capsule()
        capsule["applicability"].pop("visual.world_identity")
        with self.assertRaisesRegex(critic.PreimageCriticError, "SHA mismatch"):
            critic.verify_capsule_integrity(capsule)

    def test_shared_decision_contract_rejects_extra_gate_fields(self):
        payload = {"decision": "ACCEPT_CANDIDATE", "issue_codes": [], "severity": "LOW",
                   "repair_scope": [], "evidence": [], "gate_pass": True}
        with self.assertRaisesRegex(critic.PreimageCriticError, "gate_pass"):
            critic.validate_decision(payload)

    def test_request_sha_uses_persisted_payload_without_local_request_file(self):
        logical_path = self.ep / "meta/runtime/reviews/preimage-semantic-critic-shadow-request.json"
        request = {"request_id": "persisted-only", "task_type": "preimage_semantic_critic"}
        self.assertFalse(logical_path.exists())
        with patch.object(critic, "sha_file", side_effect=AssertionError("must not read logical path")):
            actual = critic.request_sha256(logical_path, request)
        self.assertEqual(actual, critic.digest(request))

    def test_request_snapshot_sha_comes_from_immutable_file_when_not_inline(self):
        snapshot = self.ep / "meta/runtime/agent-shadow/preimage-semantic-critic/attempt-1-request-snapshot.json"
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_text('{"request":{"request_id":"persisted-only"}}\n', encoding="utf-8")
        expected = critic.sha_file(snapshot)
        self.assertEqual(critic.request_snapshot_sha256(snapshot), expected)
        with self.assertRaisesRegex(critic.PreimageCriticError, "snapshot missing"):
            critic.request_snapshot_sha256(snapshot.with_name("missing.json"))

    def test_shadow_off_and_conflicting_flags_fail_closed(self):
        with patch.object(critic, "adapter_config", return_value={"shadow_enabled": False, "production_enabled": False}):
            self.assertIsNone(critic.prepare_after_candidate_set(self.ep, self.snapshot, self.rows))
        with patch.object(critic, "adapter_config", return_value={"shadow_enabled": True, "production_enabled": True}):
            with self.assertRaisesRegex(critic.PreimageCriticError, "production"):
                critic.prepare_after_candidate_set(self.ep, self.snapshot, self.rows)

    def test_shadow_request_records_frozen_contract_and_uses_existing_product_review(self):
        captured = {}

        def prepare(*args, **kwargs):
            captured.update(kwargs)
            return {"request_id": "req-1", "request_metadata": kwargs["request_metadata"], "request_path": "meta/runtime/reviews/request.json"}

        with patch.object(critic, "adapter_config", return_value={"shadow_enabled": True, "production_enabled": False}), \
             patch.object(critic.product_review_adapter, "prepare", side_effect=prepare):
            result = critic.prepare_after_candidate_set(self.ep, self.snapshot, self.rows)
        self.assertEqual(result["request_id"], "req-1")
        self.assertEqual(captured["kind"], critic.REQUEST_KIND)
        self.assertTrue(captured["request_metadata"]["shadow_only"])
        self.assertEqual(captured["request_metadata"]["candidate_authority"], "runtime_evidence_only")
        self.assertEqual(len(captured["source_paths"]), 2)

    def test_duplicate_shadow_dispatch_reuses_same_immutable_request(self):
        with patch.object(critic, "adapter_config", return_value={"shadow_enabled": True, "production_enabled": False}):
            first = critic.prepare_after_candidate_set(self.ep, self.snapshot, self.rows)
            second = critic.prepare_after_candidate_set(self.ep, self.snapshot, self.rows)
        self.assertEqual(first["request_id"], second["request_id"])
        self.assertEqual(first["request_fingerprint"], second["request_fingerprint"])
        self.assertEqual(first["request_snapshot_sha256"], second["request_snapshot_sha256"])
        self.assertEqual(first["request_path"], second["request_path"])

    def test_repair_is_advisory_and_does_not_authorize_state_or_mutation(self):
        result = critic.compare_with_existing(self.capsule(), {
            "decision": "REPAIR", "issue_codes": ["PREIMAGE_CROSS_SCOPE_FACT_CONFLICT"],
            "severity": "HIGH", "repair_scope": ["visual.world_identity"], "evidence": ["source-bound"],
        })
        self.assertFalse(result["authority_write"])
        self.assertFalse(result["gate_pass"])
        self.assertFalse(result["episode_transition"])


if __name__ == "__main__":
    unittest.main()
