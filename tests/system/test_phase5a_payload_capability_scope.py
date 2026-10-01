"""Contract tests for the narrowly scoped Phase 5A payload dispatch grant."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SYSTEM_DIR = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM_DIR) not in sys.path:
    sys.path.insert(0, str(SYSTEM_DIR))

import codex_subscription_image as backend


CANARY_ID = "phase5a-collab-retry-087b52d549aa"
QUEUE_ITEM_ID = "4cb8234988e2"
LOGICAL_ASSET_KEY = "_external/76251ec2bfb424e9/frame-01"
POLICY_SHA = "4bc59107d83cf3900162dc09b925e49f6b2657d59d351f0804ea4546d64118c5"
PAYLOAD_MODEL = "gpt-image-2.5-flare"
PAYLOAD_QUALITY = "high"


class Phase5APayloadCapabilityScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="phase5a-payload-scope-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / ".codex_tmp" / "phase5a" / CANARY_ID
        (self.workspace / "meta").mkdir(parents=True)
        (self.workspace / "meta" / "phase5a-canary.json").write_text(
            json.dumps({
                "workspace_class": "TEST_ONLY",
                "promotion_class": "NON_PROMOTABLE",
                "canary_type": backend._PHASE5A_CANARY_TYPE,
                "canary_id": CANARY_ID,
            }),
            encoding="utf-8",
        )

        claims = self.root / ".codex_tmp" / "phase5a"
        claims.mkdir(parents=True, exist_ok=True)
        (claims / ".phase5a-collaborative-canary-claim.json").write_text(
            json.dumps({
                "canary_type": backend._PHASE5A_CANARY_TYPE,
                "canary_id": "phase5a-collab-fixture-d032d38510",
                "workspace": str(self.root / ".codex_tmp" / "phase5a" / "phase5a-collab-fixture-d032d38510"),
            }),
            encoding="utf-8",
        )
        (claims / ".phase5a-collaborative-canary-replacement.json").write_text(
            json.dumps({
                "canary_type": backend._PHASE5A_CANARY_TYPE,
                "canary_id": CANARY_ID,
                "workspace": str(self.workspace),
                "previous_canary_id": "phase5a-collab-fixture-d032d38510",
                "previous_workspace": str(self.root / ".codex_tmp" / "phase5a" / "phase5a-collab-fixture-d032d38510"),
            }),
            encoding="utf-8",
        )

        self.queue_item = {
            "id": QUEUE_ITEM_ID,
            "frame": 1,
            "kind": "original",
            "scope": "batch",
            "status": "queued",
        }
        self.queue = {"items": [self.queue_item]}
        self.asset_state = {
            "attempts_consumed": 0,
            "remaining_attempts": 2,
            "active_attempt_index": None,
        }
        self.policy_patches = [
            patch.object(backend, "ROOT", self.root),
        ]
        for item in self.policy_patches:
            item.start()
            self.addCleanup(item.stop)

        # Exercise the scope validator while keeping all authority reads mocked:
        # these tests never touch MySQL, Redis, Attempt reservation, or a provider.
        import generation_attempt_authority
        import logical_asset_identity
        import model_policy
        import scheduler_core

        self.authority_patches = [
            patch.object(model_policy, "validate_bound_policy", return_value=None),
            patch.object(model_policy, "resolve", side_effect=self._resolve_policy),
            patch.object(scheduler_core, "load_queue", side_effect=lambda _ep: self.queue),
            patch.object(logical_asset_identity, "frame_asset_key", return_value=LOGICAL_ASSET_KEY),
            patch.object(generation_attempt_authority, "load_asset_state", side_effect=lambda *_args: self.asset_state),
        ]
        for item in self.authority_patches:
            item.start()
            self.addCleanup(item.stop)

    @staticmethod
    def _resolve_policy(role: str, *, episode=None) -> dict:
        del episode
        if role == "image.controller":
            return {"model_policy_sha256": POLICY_SHA, "model": "gpt-6-luna", "reasoning_effort": "high"}
        if role == "image.payload":
            return {"model_policy_sha256": POLICY_SHA, "model": PAYLOAD_MODEL, "quality": PAYLOAD_QUALITY}
        raise AssertionError(f"unexpected policy role: {role}")

    def _scope(self, canary_id: str = CANARY_ID) -> dict | None:
        episode = self.root / ".codex_tmp" / "phase5a" / canary_id
        return backend._validated_phase5a_canary_scope(episode, canary_id, require_claim=True)

    def _readiness(self, scope: dict) -> dict:
        result = {
            "status": "READY_FOR_REAL_CAPABILITY_PROOF",
            "tool_capability_state": "UNKNOWN",
            "tool_capability_source": "NO_AUTHORITATIVE_CATALOG_CAPABILITY",
            "session_start": "PASS",
            "candidate_catalog_member": True,
            "catalog_source": "LOGIN_ACCOUNT_MODEL_CATALOG",
            "catalog_sha256": "a" * 64,
            "transport_model": "gpt-5.6-sol",
            "transport_effort": "low",
            "payload_model": PAYLOAD_MODEL,
            "payload_quality": PAYLOAD_QUALITY,
            "image_generation_called": False,
            "image_attempt_authority_called": False,
            "phase5a_scope": scope,
        }
        result["_phase5a_readiness_signature"] = backend._phase5a_readiness_signature(result)
        return result

    def _grant(self):
        scope = self._scope()
        self.assertIsNotNone(scope)
        readiness = self._readiness(scope)
        return backend.phase5a_payload_dispatch_context(
            self.workspace, CANARY_ID, scope, readiness,
        )

    def test_visibility_text_probe_requires_exact_completed_json_and_zero_tool_calls(self) -> None:
        visible = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"{\\"image_generation_visible\\":true}"}}\n'
            '{"type":"turn.completed"}\n'
        )
        facts = backend._inspect_tool_visibility_probe(visible)
        self.assertTrue(facts["probe_result_valid"])
        self.assertTrue(facts["image_generation_visible_secondary"])
        self.assertEqual(facts["image_generation_call_count"], 0)

        no_tool_call = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"{\\"image_generation_visible\\":false}"}}\n'
            '{"type":"turn.completed"}\n'
        )
        facts = backend._inspect_tool_visibility_probe(no_tool_call)
        self.assertTrue(facts["probe_result_valid"])
        self.assertFalse(facts["image_generation_visible_secondary"])

        incomplete = visible.replace('{"type":"turn.completed"}\n', "")
        self.assertFalse(backend._inspect_tool_visibility_probe(incomplete)["probe_result_valid"])

        tool_called = (
            '{"type":"item.started","item":{"type":"function_call",'
            '"name":"image_generation"}}\n' + visible
        )
        facts = backend._inspect_tool_visibility_probe(tool_called)
        self.assertFalse(facts["probe_result_valid"])
        self.assertEqual(facts["image_generation_call_count"], 1)

        ordinary_text = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"Tools include image_generation; I think it is visible."}}\n'
            '{"type":"turn.completed"}\n'
        )
        self.assertFalse(backend._inspect_tool_visibility_probe(ordinary_text)["probe_result_valid"])

    def test_visibility_probe_is_read_only_and_explicitly_enables_tool_session(self) -> None:
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"{\\"image_generation_visible\\":true}"}}\n'
            '{"type":"turn.completed"}\n'
        )
        with (
            patch.object(backend.codex_user_runner, "bridge_required", return_value=True),
            patch.object(backend, "execution_command_prefix", return_value=["codex"]),
            patch.object(backend.codex_user_runner, "run_codex", return_value=type(
                "Result", (), {"stdout": raw, "returncode": 0}
            )()) as runner,
        ):
            result = backend._probe_transport_model_diagnostic(
                Path("codex.exe"), "gpt-5.6-sol", "low",
                candidate_provenance={
                    "model": "gpt-5.6-sol", "effort": "low", "priority": 1,
                    "candidate_catalog_member": True,
                    "catalog_source": "LOGIN_ACCOUNT_MODEL_CATALOG",
                    "catalog_sha256": "a" * 64,
                    "catalog_entry_count": 55,
                    "tool_capability_state": "UNKNOWN",
                },
                tool_visibility_probe=True,
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["probe_kind"], "TOOL_VISIBILITY_TEXT_PROBE")
        self.assertEqual(result["tool_visibility_evidence_level"], "SECONDARY_ATTESTATION")
        self.assertFalse(result["image_generation_called"])
        self.assertFalse(result["image_attempt_authority_called"])
        command = runner.call_args.args[0]
        self.assertIn("image_generation", command)
        self.assertEqual(runner.call_args.kwargs["input"].startswith("Do not call any tool."), True)

    def test_unknown_capability_can_be_ready_when_session_runs_but_registry_answer_is_unavailable(self) -> None:
        scope = self._scope()
        self.assertIsNotNone(scope)
        rows = backend._catalog_candidates({"models": [
            {"slug": "gpt-5.6-sol", "visibility": "list", "priority": 1,
             "supported_reasoning_levels": ["low"], "tool_mode": "code_mode_only"},
        ]})
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"The tool registry cannot be inspected here."}}\n'
            '{"type":"turn.completed"}\n'
        )
        with (
            patch.object(backend, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(backend.codex_user_runner, "bridge_required", return_value=True),
            patch.object(backend, "image_runtime_preflight", return_value={}),
            patch.object(backend, "_subscription_model_catalog_with_evidence", return_value={
                "catalog_source": "LOGIN_ACCOUNT_MODEL_CATALOG",
                "catalog_sha256": rows[0]["catalog_sha256"],
                "catalog_entry_count": rows[0]["catalog_entry_count"],
                "candidate_models": ["gpt-5.6-sol"],
                "candidates": rows,
            }),
            patch.object(backend, "execution_command_prefix", return_value=["codex"]),
            patch.object(backend.codex_user_runner, "run_codex", return_value=type(
                "Result", (), {"stdout": raw, "returncode": 0}
            )()) as runner,
        ):
            result = backend.payload_capability_preflight(
                model=PAYLOAD_MODEL,
                quality=PAYLOAD_QUALITY,
                codex_raw=None,
                phase5a_canary_id=CANARY_ID,
                phase5a_canary_context=scope,
            )

        self.assertEqual(result["status"], "READY_FOR_REAL_CAPABILITY_PROOF")
        self.assertEqual(result["tool_capability_state"], "UNKNOWN")
        self.assertEqual(result["session_start"], "PASS")
        self.assertEqual(result["transport_model"], "gpt-5.6-sol")
        self.assertTrue(result["candidate_catalog_member"])
        self.assertFalse(result["image_generation_called"])
        self.assertFalse(result["image_attempt_authority_called"])
        self.assertEqual(runner.call_count, 1)

    def test_only_fixed_replacement_canary_with_ready_authorities_gets_grant(self) -> None:
        scope = self._scope()
        self.assertIsNotNone(scope)
        self.assertEqual(scope["canary_id"], CANARY_ID)
        self.assertEqual(scope["queue_item_id"], QUEUE_ITEM_ID)
        self.assertEqual(scope["attempts_consumed"], 0)
        self.assertEqual(scope["remaining_attempts"], 2)

        with self._grant():
            evidence = backend.consume_phase5a_payload_dispatch_grant(
                self.workspace, self.queue_item,
                payload_model=PAYLOAD_MODEL,
                payload_quality=PAYLOAD_QUALITY,
                policy_sha256=POLICY_SHA,
            )
        self.assertTrue(evidence["phase5a_dispatch_grant_consumed"])

    def test_fake_canary_id_and_ordinary_path_cannot_get_grant(self) -> None:
        self.assertIsNone(self._scope("phase5a-fake-canary"))
        self.assertIsNone(backend.consume_phase5a_payload_dispatch_grant(
            self.workspace, self.queue_item,
            payload_model=PAYLOAD_MODEL,
            payload_quality=PAYLOAD_QUALITY,
            policy_sha256=POLICY_SHA,
        ))
        with self.assertRaisesRegex(backend.BackendError, "PHASE5A_PAYLOAD_DISPATCH_GRANT_DENIED"):
            with backend.phase5a_payload_dispatch_context(
                self.root / "ordinary-episode", "ordinary-episode", {}, self._readiness({}),
            ):
                self.fail("ordinary work must not receive a Phase 5A grant")

    def test_grant_is_bound_to_queue_item_model_quality_policy_and_consumed_once(self) -> None:
        wrong_bindings = [
            ({**self.queue_item, "id": "other-item"}, PAYLOAD_MODEL, PAYLOAD_QUALITY, POLICY_SHA),
            (self.queue_item, "other-image-model", PAYLOAD_QUALITY, POLICY_SHA),
            (self.queue_item, PAYLOAD_MODEL, "medium", POLICY_SHA),
            (self.queue_item, PAYLOAD_MODEL, PAYLOAD_QUALITY, "b" * 64),
        ]
        with self._grant():
            for item, model, quality, policy_sha in wrong_bindings:
                self.assertIsNone(backend.consume_phase5a_payload_dispatch_grant(
                    self.workspace, item,
                    payload_model=model,
                    payload_quality=quality,
                    policy_sha256=policy_sha,
                ))
            accepted = backend.consume_phase5a_payload_dispatch_grant(
                self.workspace, self.queue_item,
                payload_model=PAYLOAD_MODEL,
                payload_quality=PAYLOAD_QUALITY,
                policy_sha256=POLICY_SHA,
            )
            self.assertTrue(accepted["phase5a_dispatch_grant_consumed"])
            self.assertIsNone(backend.consume_phase5a_payload_dispatch_grant(
                self.workspace, self.queue_item,
                payload_model=PAYLOAD_MODEL,
                payload_quality=PAYLOAD_QUALITY,
                policy_sha256=POLICY_SHA,
            ))

    def test_grant_context_propagates_through_asyncio_to_thread(self) -> None:
        with self._grant():
            evidence = asyncio.run(asyncio.to_thread(
                backend.consume_phase5a_payload_dispatch_grant,
                self.workspace,
                self.queue_item,
                payload_model=PAYLOAD_MODEL,
                payload_quality=PAYLOAD_QUALITY,
                policy_sha256=POLICY_SHA,
            ))
        self.assertIsNotNone(evidence)
        self.assertTrue(evidence["phase5a_dispatch_grant_consumed"])
        self.assertEqual(evidence["phase5a_canary_id"], CANARY_ID)

    def test_authority_drift_fails_closed_before_consumption(self) -> None:
        self.asset_state["attempts_consumed"] = 1
        with self.assertRaisesRegex(backend.BackendError, "PHASE5A_PAYLOAD_DISPATCH_GRANT_DENIED"):
            with backend.phase5a_payload_dispatch_context(
                self.workspace, CANARY_ID, {}, self._readiness({}),
            ):
                self.fail("attempt drift must deny the grant")


if __name__ == "__main__":
    unittest.main()
