#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_subscription_image
import image_payload_transport


class LoginAuthPayloadTransportTests(unittest.TestCase):
    @staticmethod
    def _catalog_payload(*models, tool_capability_state="UNKNOWN"):
        rows = []
        for index, item in enumerate(models, start=1):
            model, effort = item if isinstance(item, tuple) else (item, "low")
            rows.append({
                "model": model,
                "effort": effort,
                "priority": index,
                "candidate_catalog_member": True,
                "catalog_source": "LOGIN_ACCOUNT_MODEL_CATALOG",
                "catalog_sha256": "a" * 64,
                "catalog_entry_count": len(models),
                "tool_capability_state": tool_capability_state,
                "tool_capability_source": "TEST_INJECTED_ATTESTATION",
            })
        return {
            "catalog_source": "LOGIN_ACCOUNT_MODEL_CATALOG",
            "catalog_sha256": "a" * 64,
            "catalog_entry_count": len(models),
            "candidate_models": [row["model"] for row in rows],
            "candidates": rows,
        }

    @staticmethod
    def _provenance(model="transport-a", effort="low"):
        return {
            "model": model,
            "effort": effort,
            "priority": 1,
            "candidate_catalog_member": True,
            "catalog_source": "LOGIN_ACCOUNT_MODEL_CATALOG",
            "catalog_sha256": "a" * 64,
            "catalog_entry_count": 2,
            "tool_capability_state": "UNKNOWN",
        }

    def test_catalog_prefers_visible_provider_models_and_excludes_business_controller(self):
        payload = {
            "models": [
                {"slug": "gpt-6-luna", "visibility": "list", "priority": 1,
                 "default_reasoning_level": "high", "supported_reasoning_levels": ["high"]},
                {"slug": "gpt-hidden", "visibility": "hide", "priority": 2},
                {"slug": "transport-b", "visibility": "list", "priority": 8,
                 "default_reasoning_level": "medium", "supported_reasoning_levels": ["medium"],
                 "supported_tools": ["image_generation"]},
                {"slug": "transport-a", "visibility": "list", "priority": 3,
                 "default_reasoning_level": "medium",
                 "supported_reasoning_levels": [{"effort": "low"}, {"effort": "medium"}]},
            ]
        }
        rows = codex_subscription_image._catalog_candidates(payload)
        self.assertEqual([row["model"] for row in rows], ["transport-a", "transport-b"])
        self.assertEqual(rows[0]["effort"], "low")
        self.assertEqual(rows[0]["catalog_source"], "LOGIN_ACCOUNT_MODEL_CATALOG")
        self.assertTrue(all(row["candidate_catalog_member"] for row in rows))
        self.assertTrue(all(row["catalog_entry_count"] == 4 for row in rows))
        self.assertTrue(all(row["catalog_sha256"] == rows[0]["catalog_sha256"] for row in rows))
        self.assertEqual(rows[0]["tool_capability_state"], "UNKNOWN")
        self.assertEqual(rows[1]["tool_capability_state"], "UNKNOWN")

    def test_catalog_attestation_hash_is_stable_and_uses_safe_fields(self):
        payload = {"models": [
            {"slug": "transport-a", "visibility": "list", "priority": 1,
             "supported_reasoning_levels": ["low", "high"],
             "instructions_template": "DO NOT PERSIST THIS PRIVATE TEMPLATE"},
            {"slug": "gpt-6-luna", "visibility": "list", "priority": 2,
             "supported_reasoning_levels": ["high"]},
        ]}
        first = codex_subscription_image._catalog_candidates(payload)
        second = codex_subscription_image._catalog_candidates(payload)
        self.assertEqual(first[0]["catalog_source"], "LOGIN_ACCOUNT_MODEL_CATALOG")
        self.assertEqual(first[0]["catalog_entry_count"], 2)
        self.assertEqual(first[0]["catalog_sha256"], second[0]["catalog_sha256"])
        self.assertRegex(first[0]["catalog_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("instructions_template", json.dumps(first))

    def test_optional_catalog_tool_lists_do_not_prove_capability(self):
        rows = codex_subscription_image._catalog_candidates({"models": [
            {"slug": "tool-model", "visibility": "list", "priority": 1,
             "supported_tools": [{"name": "image_generation"}]},
            {"slug": "text-model", "visibility": "list", "priority": 2,
             "supported_tools": []},
            {"slug": "unknown-model", "visibility": "list", "priority": 3},
        ]})
        self.assertEqual([row["tool_capability_state"] for row in rows],
                         ["UNKNOWN", "UNKNOWN", "UNKNOWN"])

    def test_non_authoritative_catalog_metadata_does_not_claim_image_tool_support(self):
        rows = codex_subscription_image._catalog_candidates({"models": [
            {"slug": "omitted-experimental-tools", "visibility": "list", "priority": 1,
             "tool_mode": "code_mode_only"},
            {"slug": "empty-experimental-tools", "visibility": "list", "priority": 2,
             "experimental_supported_tools": [], "tool_mode": "code_mode_only"},
            {"slug": "experimental-image-tool", "visibility": "list", "priority": 3,
             "experimental_supported_tools": ["image_generation"]},
            {"slug": "authoritative-image-tool", "visibility": "list", "priority": 4,
             "supported_tools": ["image_generation"]},
            {"slug": "authoritative-no-tools", "visibility": "list", "priority": 5,
             "supported_tools": []},
        ]})
        self.assertEqual(
            [row["tool_capability_state"] for row in rows],
            ["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"],
        )

    def test_no_external_runner_for_fake_model_fixtures(self):
        """Ordinary preflight cannot probe UNKNOWN fixture models or become READY."""
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight", return_value={}),
            patch.object(codex_subscription_image, "_subscription_model_catalog_with_evidence",
                         return_value=self._catalog_payload(
                             ("transport-a", "low"), ("transport-b", "medium"))),
            patch.object(codex_subscription_image, "_probe_transport_model_diagnostic",
                         side_effect=AssertionError(
                             "ordinary preflight must not probe UNKNOWN fixture candidates")) as in_process_probe,
            patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                         side_effect=AssertionError(
                             "fake transport fixture reached the external Codex runner")) as external_runner,
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")

        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_IMAGE_TOOL_CAPABILITY_UNKNOWN")
        self.assertNotEqual(row["status"], "READY_FOR_REAL_CAPABILITY_PROOF")
        in_process_probe.assert_not_called()
        external_runner.assert_not_called()
        self.assertFalse(row["image_attempt_authority_called"])
        self.assertFalse(row["image_generation_called"])

    def test_unattested_fake_candidate_is_denied_before_external_runner(self):
        mismatched = self._provenance(model="transport-b")
        with (
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
            patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                         side_effect=AssertionError("unattested model crossed runner boundary")) as runner,
        ):
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low", candidate_provenance=mismatched)
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_TRANSPORT_PROBE_INVALID_CANDIDATE")
        self.assertFalse(row["candidate_catalog_member"])
        runner.assert_not_called()

    def test_unattested_candidate_missing_provenance_is_denied_before_external_runner(self):
        with patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                          side_effect=AssertionError("unattested model crossed runner boundary")) as runner:
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_TRANSPORT_PROBE_INVALID_CANDIDATE")
        self.assertFalse(row["candidate_catalog_member"])
        runner.assert_not_called()

    def test_bridge_execution_prefix_defers_executable_resolution_to_user_runner(self):
        with patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True):
            self.assertEqual(
                codex_subscription_image.execution_command_prefix(Path(r"C:/service/codex.exe")),
                ["codex"],
            )

    def test_direct_execution_prefix_keeps_local_codex_contract(self):
        with (
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=False),
            patch.object(codex_subscription_image, "command_prefix", return_value=["resolved-codex"]),
        ):
            self.assertEqual(
                codex_subscription_image.execution_command_prefix(Path("codex.exe")),
                ["resolved-codex"],
            )

    def test_login_preflight_failure_is_before_attempt_and_generation(self):
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight",
                         side_effect=codex_subscription_image.BackendError("runner unavailable")),
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_RUNNER_UNAVAILABLE")
        self.assertEqual(row["safe_failure_stage"], "runner_preflight")
        self.assertEqual(row["safe_failure_class"], "LOGIN_AUTH_RUNNER_UNAVAILABLE")
        self.assertEqual(row["exception_class"], "BackendError")
        self.assertNotIn("reason", row)
        self.assertFalse(row["image_attempt_authority_called"])
        self.assertFalse(row["image_generation_called"])

    def test_catalog_failure_has_safe_stage_and_does_not_return_exception_text(self):
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight", return_value={}),
            patch.object(codex_subscription_image, "_subscription_model_catalog_with_evidence",
                         side_effect=codex_subscription_image.BackendError(
                             "LOGIN_AUTH_MODEL_CATALOG_FAILED: private-config-detail")),
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_MODEL_CATALOG_FAILED")
        self.assertEqual(row["safe_failure_stage"], "model_catalog")
        self.assertEqual(row["safe_failure_class"], "LOGIN_AUTH_MODEL_CATALOG_FAILED")
        self.assertNotIn("private-config-detail", json.dumps(row))
        self.assertFalse(row["image_attempt_authority_called"])
        self.assertFalse(row["image_generation_called"])

    def test_cleanup_timeout_adopts_completed_sentinel_without_image_call(self):
        raw = (
            '{"type":"thread.started"}\n'
            '{"type":"turn.started"}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        exc = codex_subscription_image.codex_user_runner.CodexUserRunnerTimeout(
            ["codex"], 30, "cleanup timeout")
        exc.remote = {"request_id": "abc123", "timed_out": True, "returncode": 124}
        result = {
            "output_base64": base64.b64encode(raw.encode("utf-8")).decode("ascii"),
            "returncode": 124,
        }
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex", side_effect=exc) as runner,
            patch.object(codex_subscription_image.codex_user_runner, "read_task_result", return_value=result),
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low",
                candidate_provenance=self._provenance())
        self.assertEqual(row["status"], "PASS_WITH_CLEANUP_TIMEOUT")
        runner.assert_called_once()

    def test_timeout_diagnostic_keeps_only_safe_probe_metadata(self):
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        exc = codex_subscription_image.codex_user_runner.CodexUserRunnerTimeout(
            ["codex"], 30, "cleanup timeout")
        exc.remote = {"request_id": "safe-request-id", "timed_out": True, "returncode": 124}
        result = {"output_base64": base64.b64encode(raw.encode("utf-8")).decode("ascii")}
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex", side_effect=exc),
            patch.object(codex_subscription_image.codex_user_runner, "read_task_result", return_value=result),
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low",
                candidate_provenance=self._provenance())
        self.assertEqual(row["status"], "PASS_WITH_CLEANUP_TIMEOUT")
        self.assertTrue(row["timed_out"])
        self.assertEqual(row["request_id"], "safe-request-id")
        self.assertTrue(row["durable_result_found"])
        self.assertTrue(row["sentinel_completed"])
        self.assertTrue(row["turn_completed"])
        self.assertEqual(row["image_generation_call_count"], 0)
        self.assertNotIn("STORYOS_TRANSPORT_OK", json.dumps(row))
        self.assertNotIn("output_base64", json.dumps(row))

    def test_transport_nonzero_result_is_classified_without_raw_output(self):
        raw = '{"type":"error","message":"private-token-like-value"}\n'
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                         return_value=SimpleNamespace(returncode=1, stdout=raw)),
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low",
                candidate_provenance=self._provenance())
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_TRANSPORT_EXEC_FAILED")
        self.assertEqual(row["returncode"], 1)
        self.assertNotIn("private-token-like-value", json.dumps(row))

    def test_corrupt_durable_timeout_result_is_reported_found_but_fails_closed(self):
        exc = codex_subscription_image.codex_user_runner.CodexUserRunnerTimeout(
            ["codex"], 30, "cleanup timeout")
        exc.remote = {"request_id": "safe-request-id", "timed_out": True, "returncode": 124}
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex", side_effect=exc),
            patch.object(codex_subscription_image.codex_user_runner, "read_task_result",
                         return_value={"output_base64": "%%%"}) as read_result,
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low",
                candidate_provenance=self._provenance())
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_TRANSPORT_PROBE_TIMEOUT")
        self.assertTrue(row["durable_result_found"])
        self.assertFalse(row["sentinel_completed"])
        read_result.assert_called_once_with("safe-request-id")

    def test_websocket_upgrade_failure_is_safe_protocol_metadata(self):
        raw = "codex_api::endpoint::responses_websocket failed: HTTP error 426 Upgrade Required"
        facts = codex_subscription_image._safe_transport_failure_facts(raw, 1)
        self.assertEqual(facts["failure_class"], "LOGIN_AUTH_TRANSPORT_EXEC_FAILED")
        self.assertEqual(facts["http_status"], 426)
        self.assertTrue(facts["websocket_attempted"])
        self.assertEqual(facts["protocol_failure_class"], "TRANSPORT_WEBSOCKET_UPGRADE_REJECTED")
        self.assertNotIn(raw, json.dumps(facts))

    def test_unsupported_catalog_model_has_precise_failure_class(self):
        facts = codex_subscription_image._safe_transport_failure_facts(
            "HTTP 400: model gpt-example is not supported", 1)
        self.assertEqual(facts["failure_class"], "LOGIN_AUTH_TRANSPORT_MODEL_UNAVAILABLE")

    def test_missing_image_tool_configuration_has_precise_failure_class(self):
        facts = codex_subscription_image._safe_transport_failure_facts(
            "image_generation tool is not enabled for this provider", 1)
        self.assertEqual(facts["failure_class"], "LOGIN_AUTH_IMAGE_TOOL_CONFIG_UNAVAILABLE")

    def test_auth_rejection_is_distinct_from_runner_unavailability(self):
        facts = codex_subscription_image._safe_transport_failure_facts(
            "HTTP 401 Unauthorized: authentication failed", 1)
        self.assertEqual(facts["failure_class"], "LOGIN_AUTH_AUTH_FAILED")

    def test_runner_preflight_auth_failure_is_distinct_and_sanitized(self):
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight",
                         side_effect=codex_subscription_image.BackendError(
                             "IMAGE_RUNTIME_PREFLIGHT_FAILED: authentication context unavailable")),
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_AUTH_FAILED")
        self.assertEqual(row["safe_failure_stage"], "runner_preflight")
        self.assertNotIn("authentication context", json.dumps(row).lower())

    def test_normal_jsonl_exact_sentinel_and_completed_turn_passes(self):
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"  STORYOS_TRANSPORT_OK  "}}\n'
            '{"type":"turn.completed"}\n'
        )
        self.assertTrue(codex_subscription_image._transport_probe_completed(raw))
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                         return_value=SimpleNamespace(returncode=0, stdout=raw)) as run,
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low",
                candidate_provenance=self._provenance())
        self.assertEqual(row["status"], "PASS")
        self.assertTrue(row["candidate_catalog_member"])
        self.assertEqual(row["candidate_model"], "transport-a")
        self.assertEqual(row["candidate_effort"], "low")
        self.assertEqual(row["catalog_sha256"], "a" * 64)
        self.assertEqual(row["catalog_source"], "LOGIN_ACCOUNT_MODEL_CATALOG")
        run.assert_called_once()

    def _timeout_probe(self, *, remote, result=None):
        exc = codex_subscription_image.codex_user_runner.CodexUserRunnerTimeout(
            ["codex"], 30, "cleanup timeout")
        exc.remote = remote
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex", side_effect=exc) as run,
            patch.object(codex_subscription_image.codex_user_runner, "read_task_result",
                         return_value=result or {}) as read_result,
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            outcome = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low",
                candidate_provenance=self._provenance())
        run.assert_called_once()
        return outcome, read_result

    def test_cleanup_timeout_without_request_id_fails_without_readback(self):
        row, read_result = self._timeout_probe(remote={"timed_out": True})
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_TRANSPORT_PROBE_TIMEOUT")
        read_result.assert_not_called()

    def test_cleanup_timeout_reads_request_id_from_remote_object(self):
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        row, read_result = self._timeout_probe(
            remote=SimpleNamespace(request_id="request-object"),
            result={"output_base64": encoded},
        )
        self.assertEqual(row["status"], "PASS_WITH_CLEANUP_TIMEOUT")
        self.assertTrue(row["candidate_catalog_member"])
        self.assertEqual(row["catalog_sha256"], "a" * 64)
        self.assertEqual(row["catalog_source"], "LOGIN_ACCOUNT_MODEL_CATALOG")
        read_result.assert_called_once_with("request-object")

    def test_cleanup_timeout_without_durable_result_fails(self):
        row, read_result = self._timeout_probe(remote={"request_id": "abc123"})
        self.assertEqual(row["status"], "BLOCKED")
        read_result.assert_called_once_with("abc123")

    def test_cleanup_timeout_rejects_corrupt_durable_base64(self):
        row, _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": "%%%"})
        self.assertEqual(row["status"], "BLOCKED")

    def test_cleanup_timeout_rejects_invalid_utf8_durable_output(self):
        encoded = base64.b64encode(b"\xff").decode("ascii")
        row, _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": encoded})
        self.assertEqual(row["status"], "BLOCKED")

    def test_cleanup_timeout_requires_turn_completed(self):
        raw = '{"type":"item.completed","item":{"type":"agent_message","text":"STORYOS_TRANSPORT_OK"}}\n'
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        row, _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": encoded})
        self.assertEqual(row["status"], "BLOCKED")

    def test_cleanup_timeout_rejects_ordinary_text_sentinel(self):
        raw = 'Some ordinary text says STORYOS_TRANSPORT_OK\n{"type":"turn.completed"}\n'
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))
        encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
        row, _ = self._timeout_probe(
            remote={"request_id": "abc123"}, result={"output_base64": encoded})
        self.assertEqual(row["status"], "BLOCKED")

    def test_probe_rejects_malformed_json_protocol_frame(self):
        raw = (
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":broken-json}\n'
            '{"type":"turn.completed"}\n'
        )
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))

    def test_probe_accepts_non_json_stderr_diagnostics(self):
        raw = (
            '2026-10-01 ERROR failed to load skill: missing YAML frontmatter\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        facts = codex_subscription_image._inspect_transport_probe(raw)
        self.assertTrue(codex_subscription_image._transport_probe_completed(raw))
        self.assertFalse(facts["malformed_jsonl"])
        self.assertEqual(facts["diagnostic_noise_line_count"], 1)

    def test_visibility_probe_accepts_non_json_stderr_diagnostics(self):
        raw = (
            '2026-10-01 ERROR failed to load skill: missing YAML frontmatter\n'
            'another diagnostic warning\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"{\\\"image_generation_visible\\\":true}"}}\n'
            '{"type":"turn.completed"}\n'
        )
        facts = codex_subscription_image._inspect_tool_visibility_probe(raw)
        self.assertTrue(facts["probe_result_valid"])
        self.assertTrue(facts["image_generation_visible_secondary"])
        self.assertFalse(facts["malformed_jsonl"])
        self.assertEqual(facts["diagnostic_noise_line_count"], 2)

    def test_direct_probe_rejects_image_generation_tool_event(self):
        raw = (
            '{"type":"item.completed","item":{"type":"tool_call",'
            '"name":"image_generation"}}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        with (
            patch.object(codex_subscription_image.codex_user_runner, "run_codex",
                         return_value=SimpleNamespace(returncode=0, stdout=raw)),
            patch.object(codex_subscription_image, "execution_command_prefix", return_value=["codex"]),
        ):
            row = codex_subscription_image._probe_transport_model_diagnostic(
                Path("codex.exe"), "transport-a", "low",
                candidate_provenance=self._provenance())
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(row["image_generation_call_count"], 1)

    def test_probe_rejects_provider_image_generation_item_type(self):
        raw = (
            '{"type":"item.completed","item":{"type":"image_generation_call"}}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed"}\n'
        )
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))

    def test_cleanup_timeout_rejects_image_tool_event(self):
        raw = (
            '{"type":"item.completed","item":{"type":"tool_call","name":"image_generation"}}\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"STORYOS_TRANSPORT_OK"}}\n'
            '{"type":"turn.completed","usage":{}}\n'
        )
        self.assertFalse(codex_subscription_image._transport_probe_completed(raw))

    def test_login_preflight_selects_first_successful_catalog_transport(self):
        probes = []
        visibility_probes = []
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight", return_value={"transport": "user_runner"}),
            patch.object(codex_subscription_image, "_subscription_model_catalog_with_evidence",
                         return_value=self._catalog_payload(
                             ("transport-a", "low"), ("transport-b", "medium"),
                             tool_capability_state="EXPLICIT_SUPPORTED")),
            patch.object(codex_subscription_image, "_probe_transport_model_diagnostic",
                         side_effect=lambda _c, model, effort, *, candidate_provenance, tool_visibility_probe=False: (
                             visibility_probes.append(tool_visibility_probe) or
                             probes.append((model, effort)) or {
                                 "status": "PASS" if model == "transport-b" else "BLOCKED",
                                 "failure_class": None if model == "transport-b"
                                 else "LOGIN_AUTH_TRANSPORT_MODEL_UNAVAILABLE",
                                 "returncode": 0,
                                 "timed_out": False,
                                 "request_id": None,
                                 "durable_result_found": False,
                                 "sentinel_completed": model == "transport-b",
                                 "turn_completed": model == "transport-b",
                                 "image_generation_call_count": 0,
                                 "codex_resolution": "user_runner",
                                 "transport_model_source": "LOGIN_CATALOG_PROBE",
                                 "candidate_model": candidate_provenance["model"],
                                 "candidate_effort": candidate_provenance["effort"],
                                 "candidate_priority": candidate_provenance["priority"],
                                 "candidate_catalog_member": candidate_provenance["candidate_catalog_member"],
                                 "catalog_source": candidate_provenance["catalog_source"],
                                 "catalog_sha256": candidate_provenance["catalog_sha256"],
                                 "catalog_entry_count": candidate_provenance["catalog_entry_count"],
                             }
                         )),
            patch.object(codex_subscription_image.codex_user_runner, "run_codex") as external_runner,
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["status"], "PASS")
        self.assertEqual(row["transport_model"], "transport-b")
        self.assertEqual(row["transport_effort"], "medium")
        self.assertEqual(probes, [("transport-a", "low"), ("transport-b", "medium")])
        self.assertEqual(visibility_probes, [False, False])
        self.assertTrue(row["candidate_catalog_member"])
        self.assertEqual(row["catalog_source"], "LOGIN_ACCOUNT_MODEL_CATALOG")
        self.assertEqual(row["catalog_sha256"], "a" * 64)
        external_runner.assert_not_called()
        self.assertFalse(row["api_key_required"])
        self.assertFalse(row["image_attempt_authority_called"])
        self.assertFalse(row["image_generation_called"])

    def test_success_on_first_candidate_does_not_fan_out(self):
        probe = {
            "status": "PASS", "failure_class": None, "returncode": 0, "timed_out": False,
            "request_id": None, "durable_result_found": False, "sentinel_completed": True,
            "turn_completed": True, "image_generation_call_count": 0,
            "codex_resolution": "user_runner", "transport_model_source": "LOGIN_CATALOG_PROBE",
        }
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight", return_value={}),
            patch.object(codex_subscription_image, "_subscription_model_catalog_with_evidence",
                         return_value=self._catalog_payload(
                             ("transport-a", "low"), ("transport-b", "medium"),
                             tool_capability_state="EXPLICIT_SUPPORTED")),
            patch.object(codex_subscription_image, "_probe_transport_model_diagnostic",
                         return_value=probe) as transport_probe,
            patch.object(codex_subscription_image.codex_user_runner, "run_codex") as external_runner,
        ):
            result = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(transport_probe.call_count, 1)
        self.assertEqual(transport_probe.call_args.kwargs["candidate_provenance"]["model"], "transport-a")
        external_runner.assert_not_called()

    def test_timeout_or_invalid_result_does_not_probe_second_catalog_model(self):
        for failure_class in (
            "LOGIN_AUTH_TRANSPORT_PROBE_TIMEOUT",
            "LOGIN_AUTH_TRANSPORT_PROBE_INVALID_RESULT",
        ):
            with self.subTest(failure_class=failure_class):
                probe = {
                    "status": "BLOCKED", "failure_class": failure_class, "returncode": None,
                    "timed_out": failure_class.endswith("TIMEOUT"), "request_id": "safe-id",
                    "durable_result_found": False, "sentinel_completed": False,
                    "turn_completed": False, "image_generation_call_count": 0,
                }
                with (
                    patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
                    patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
                    patch.object(codex_subscription_image, "image_runtime_preflight", return_value={}),
                    patch.object(codex_subscription_image, "_subscription_model_catalog_with_evidence",
                                 return_value=self._catalog_payload(
                                     "transport-a", "transport-b",
                                     tool_capability_state="EXPLICIT_SUPPORTED")),
                    patch.object(codex_subscription_image, "_probe_transport_model_diagnostic",
                                 return_value=probe) as transport_probe,
                    patch.object(codex_subscription_image.codex_user_runner, "run_codex") as external_runner,
                ):
                    result = codex_subscription_image.payload_capability_preflight(
                        model="gpt-image-2.5-flare", quality="high")
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(transport_probe.call_count, 1)
                self.assertEqual(transport_probe.call_args.kwargs["candidate_provenance"]["model"], "transport-a")
                external_runner.assert_not_called()

    def test_blocked_transport_preflight_preserves_failure_class_and_no_raw_text(self):
        with (
            patch.object(codex_subscription_image, "resolve_codex", return_value=Path("codex.exe")),
            patch.object(codex_subscription_image.codex_user_runner, "bridge_required", return_value=True),
            patch.object(codex_subscription_image, "image_runtime_preflight", return_value={}),
            patch.object(codex_subscription_image, "_subscription_model_catalog_with_evidence",
                         return_value=self._catalog_payload(
                             "transport-a", tool_capability_state="EXPLICIT_SUPPORTED")),
            patch.object(codex_subscription_image, "_probe_transport_model_diagnostic", return_value={
                "status": "BLOCKED",
                "failure_class": "LOGIN_AUTH_TRANSPORT_PROBE_INVALID_RESULT",
                "failure_stage": "transport_probe",
                "candidate_model": "transport-a",
                "returncode": 0,
                "timed_out": False,
                "request_id": None,
                "durable_result_found": False,
                "sentinel_completed": False,
                "turn_completed": True,
                "image_generation_call_count": 0,
                "exception_class": None,
                "codex_resolution": "user_runner",
                "transport_model_source": "LOGIN_CATALOG_PROBE",
                "candidate_catalog_member": True,
                "catalog_source": "LOGIN_ACCOUNT_MODEL_CATALOG",
                "catalog_sha256": "a" * 64,
                "catalog_entry_count": 1,
            }),
            patch.object(codex_subscription_image.codex_user_runner, "run_codex") as external_runner,
        ):
            row = codex_subscription_image.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["failure_class"], "LOGIN_AUTH_TRANSPORT_PROBE_INVALID_RESULT")
        self.assertEqual(row["safe_failure_class"], "LOGIN_AUTH_TRANSPORT_PROBE_INVALID_RESULT")
        self.assertEqual(row["failure_stage"], "transport_probe")
        self.assertEqual(row["candidate_failures"][0]["candidate_model"], "transport-a")
        self.assertTrue(row["candidate_failures"][0]["candidate_catalog_member"])
        self.assertEqual(row["candidate_failures"][0]["catalog_sha256"], "a" * 64)
        external_runner.assert_not_called()
        self.assertFalse(row["image_attempt_authority_called"])
        self.assertFalse(row["image_generation_called"])

    def test_runner_artifact_evidence_distinguishes_zero_artifacts(self):
        with patch.object(
            codex_subscription_image.codex_user_runner,
            "read_task_result",
            return_value={
                "returncode": 0,
                "evidence": {"generated_artifacts": []},
            },
        ):
            row = codex_subscription_image.runner_generated_artifact_evidence("req-zero")
        self.assertTrue(row["result_found"])
        self.assertEqual(row["generated_artifact_count"], 0)
        self.assertEqual(row["returncode"], 0)

    def test_runner_artifact_evidence_counts_generated_artifacts(self):
        with patch.object(
            codex_subscription_image.codex_user_runner,
            "read_task_result",
            return_value={
                "returncode": 0,
                "evidence": {"generated_artifacts": [{"path": "a.png"}]},
            },
        ):
            row = codex_subscription_image.runner_generated_artifact_evidence("req-one")
        self.assertTrue(row["result_found"])
        self.assertEqual(row["generated_artifact_count"], 1)

    def test_runner_artifact_evidence_fails_closed_when_result_missing(self):
        with patch.object(
            codex_subscription_image.codex_user_runner,
            "read_task_result",
            side_effect=RuntimeError("missing"),
        ):
            row = codex_subscription_image.runner_generated_artifact_evidence("req-missing")
        self.assertFalse(row["result_found"])
        self.assertIsNone(row["generated_artifact_count"])

    def test_logged_backend_failure_preserves_provider_usage_limit(self):
        raw = (
            '{"type":"error","message":"You have hit your usage limit. '
            'Purchase more credits or try again later."}\n'
            '{"type":"turn.failed","error":{"message":"usage limit"}}\n'
        )
        self.assertEqual(
            codex_subscription_image.logged_backend_failure(
                raw, returncode=1, candidate_valid=False, candidate_viable=False
            ),
            codex_subscription_image.image_model_policy.PROVIDER_QUOTA_EXHAUSTED,
        )

    def test_transport_prompt_freezes_payload_and_calls_image_once(self):
        request = {
            "request_fingerprint": "f" * 64,
            "payload_model": "gpt-image-2.5-flare",
            "payload_quality": "high",
            "canvas": {"width": 1080, "height": 1350, "aspect_ratio": "4:5"},
            "scene_prompt": "eye-level wide documentary still; exact scene prompt",
        }
        prompt = codex_subscription_image.payload_transport_prompt(request, "1080x1350", 2)
        self.assertIn("image_generation exactly once", prompt)
        self.assertIn("EXACT_IMAGE_MODEL: gpt-image-2.5-flare", prompt)
        self.assertIn("EXACT_IMAGE_QUALITY: high", prompt)
        self.assertIn("EXACT_CANVAS: 1080x1350", prompt)
        self.assertIn("EXACT_ASPECT_RATIO: 4:5", prompt)
        self.assertIn("EXACT_ORIENTATION: PORTRAIT", prompt)
        self.assertIn("wide documentary still", prompt)
        self.assertIn("MUST NOT change canvas orientation or aspect ratio", prompt)
        self.assertIn("still call image_generation exactly once", prompt)
        self.assertIn("do not skip generation solely because exact canvas geometry is unavailable", prompt)
        self.assertIn("StoryOS validates actual output geometry after artifact commit", prompt)
        self.assertIn("Do not rewrite", prompt)

    def test_provider_adapter_delegates_to_selected_codex_login_route(self):
        with (
            patch.object(image_payload_transport, "selected_route", return_value={
                "provider": "codex_subscription", "api_key_required": False,
            }),
            patch.object(image_payload_transport.codex_subscription_image,
                         "payload_capability_preflight", return_value={
                             "status": "PASS", "provider": "codex_subscription",
                             "transport_model": "transport-a", "transport_effort": "low",
                         }),
        ):
            row = image_payload_transport.payload_capability_preflight(
                model="gpt-image-2.5-flare", quality="high")
        self.assertEqual(row["provider"], "codex_subscription")
        self.assertEqual(row["transport_model"], "transport-a")
        self.assertFalse(row["api_key_required"])


if __name__ == "__main__":
    unittest.main()
