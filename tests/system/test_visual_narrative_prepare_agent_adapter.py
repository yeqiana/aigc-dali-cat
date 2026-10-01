from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
sys.path.insert(0, str(SYSTEM))

import agent_shadow_compare
import preimage_authority_snapshot
import preimage_task_contract
import product_runtime_adapter
import model_policy
from agents import visual_narrative_prepare_adapter as adapter
from agents import visual_narrative_prepare_model_producer as producer


class VisualNarrativeAdapterTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="visual-agent-")
        self.ep = Path(self.temp.name)
        (self.ep / "meta").mkdir()
        (self.ep / "meta/story-gates.json").write_text(json.dumps({
            "story": {"locked": True, "climax_frame": 10, "payoff_frame": 20},
            "visual": {},
        }), encoding="utf-8")
        (self.ep / "meta/shot-progression-review.json").write_text(json.dumps({
            "schema_version": 3, "status": "LOCKED", "genre_family": "suspense_strange",
            "anomaly_applicable": True, "interaction_applicable": True,
            "rules": {"max_identical_setup_consecutive": 2, "frame10_requires_new_question_or_evidence": True},
            "frames": [{"frame": "01", "shot_scale": "wide", "scene_position_id": "room-door"}],
        }), encoding="utf-8")
        model_policy.freeze_for_episode(self.ep)
        snapshot = preimage_authority_snapshot.build(self.ep, write=False)
        self.task = preimage_task_contract.task_contract(self.ep, "VISUAL_NARRATIVE_PREPARE", snapshot)
        self.task = producer.freeze_task(self.ep, self.task)

    def tearDown(self):
        self.temp.cleanup()

    def _candidate(self):
        scopes = copy.deepcopy(self.task["input_contract"]["visual_narrative_capsule"]["obligations"]["scopes"])
        candidate = preimage_task_contract.candidate_template(self.task, scopes)
        candidate["model_execution"] = {
            "real_model_execution": True, "wall_seconds": 1.0, "input_tokens": 120,
            "cached_input_tokens": 0, "output_tokens": 25, "reasoning_output_tokens": 5,
            "repeated_reads": 0, "failure": False, "timeout": False,
            "provider": "test", "model": "test-model",
        }
        return candidate

    def test_execution_is_shadow_candidate_only_and_has_no_tools(self):
        item = adapter.build_execution(self.task, shadow=True, execution_id="exec_visual_shadow_test")
        self.assertTrue(item.shadow)
        self.assertEqual(item.plan.execution_type, "EPISODE_CANDIDATE_SHADOW")
        self.assertEqual(tuple(item.plan.steps[0].allowed_tools), ())
        self.assertEqual(item.allowed_writes, ())
        self.assertEqual(self.task["authority_scope"], list(agent_shadow_compare.VISUAL_SCOPES))

    def test_frozen_visual_obligations_require_exact_scope_and_locked_leaves(self):
        candidate = self._candidate()
        self.assertTrue(agent_shadow_compare.compare_visual_narrative_semantics(self.task, candidate)["pass"])
        candidate["payload"]["visual.capture_grammar"]["rules"]["frame10_requires_new_question_or_evidence"] = False
        result = agent_shadow_compare.compare_visual_narrative_semantics(self.task, candidate)
        self.assertFalse(result["pass"])
        self.assertTrue(any("differs from frozen value" in error for error in result["errors"]))

    def test_frozen_source_change_invalidates_capsule(self):
        self.assertTrue(producer.frozen_sources_unchanged(self.ep, self.task))
        with (self.ep / "meta/shot-progression-review.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
        self.assertFalse(producer.frozen_sources_unchanged(self.ep, self.task))

    def _valid_payload(self):
        obligations = agent_shadow_compare.visual_semantic_obligations(self.task)["scopes"]
        return {
            scope: {"proposal": {
                "summary": ("This proposal stays grounded in the frozen Visual Narrative contract and "
                            "preserves its locked meaning without changing story, frame order, or capture rules."),
                "anchors": sorted(obligations[scope]),
            }}
            for scope in agent_shadow_compare.VISUAL_SCOPES
        }

    def test_strict_single_document_parser_and_protocol_failure_classes(self):
        valid = self._valid_payload()
        encoded = json.dumps(valid, ensure_ascii=False)
        self.assertEqual(producer._parse_agent_payload(encoded), valid)
        self.assertEqual(producer._parse_agent_payload(" \n" + encoded + "\t\n"), valid)
        cases = (
            (encoded + " explanation", "VISUAL_OUTPUT_TRAILING_CONTENT"),
            (encoded + json.dumps(valid), "VISUAL_MULTIPLE_JSON_DOCUMENTS"),
            ("```json\n" + encoded + "\n```", "VISUAL_OUTPUT_MARKDOWN_FENCE"),
            ("```json\n{}\n```\n```json\n{}\n```", "VISUAL_OUTPUT_MARKDOWN_FENCE"),
            ('{"visual.narrative_core":', "VISUAL_OUTPUT_TRUNCATED_OR_INVALID_JSON"),
            ("[]", "VISUAL_OUTPUT_TOP_LEVEL_NOT_OBJECT"),
            ("true", "VISUAL_OUTPUT_TOP_LEVEL_NOT_OBJECT"),
            ("Explanation: " + encoded, "VISUAL_OUTPUT_LEADING_CONTENT"),
        )
        for raw, expected in cases:
            with self.subTest(expected=expected, raw=raw[:45]), self.assertRaisesRegex(ValueError, expected):
                producer._parse_agent_payload(raw)

    def test_missing_scope_is_syntactically_valid_but_candidate_verifier_rejects_it(self):
        payload = self._valid_payload()
        payload.pop("visual.capture_grammar")
        parsed = producer._parse_agent_payload(json.dumps(payload))
        candidate = preimage_task_contract.candidate_template(self.task, parsed)
        self.assertTrue(preimage_task_contract.verify_candidate(candidate, self.task))
        with self.assertRaisesRegex(ValueError, "VISUAL_PAYLOAD_SCOPE_SET_INVALID"):
            producer._validate_agent_payload(self.task, parsed)

    def test_model_cannot_supply_telemetry_or_extra_payload_fields(self):
        payload = self._valid_payload()
        payload["telemetry"] = {"input_tokens": 999999}
        with self.assertRaisesRegex(ValueError, "VISUAL_PAYLOAD_SCOPE_SET_INVALID"):
            producer._validate_agent_payload(self.task, payload)

    def test_jsonl_to_host_candidate_offline_chain_passes_and_uses_cli_schema(self):
        payload = self._valid_payload()
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(payload)}},
            {"type": "turn.completed", "usage": {
                "input_tokens": 1200, "cached_input_tokens": 100,
                "output_tokens": 240, "reasoning_output_tokens": 20,
            }},
        ]
        result = SimpleNamespace(
            output=("\n".join(json.dumps(row) for row in events)).encode("utf-8"),
            remote={"elapsed_seconds": 2.5, "timed_out": False}, returncode=0,
        )
        with mock.patch.object(producer.codex_user_runner, "resolve_codex", return_value=("codex", "test")), \
             mock.patch.object(producer.codex_user_runner, "bridge_required", return_value=False), \
             mock.patch.object(producer.codex_user_runner, "execute_task", return_value=result) as execute:
            produced = producer.run(self.ep, self.task, role="agent_shadow")
        self.assertIsNone(produced["failure_reason"])
        self.assertEqual(produced["payload"], payload)
        self.assertIn("--output-schema", execute.call_args.args[0].argv)
        candidate, errors, semantic = product_runtime_adapter.visual_narrative_host_candidate(
            self.task, produced,
        )
        self.assertEqual(errors, [])
        self.assertTrue(semantic["pass"])
        self.assertEqual(preimage_task_contract.verify_candidate(candidate, self.task), [])
        self.assertTrue(agent_shadow_compare.compare_visual_narrative_semantics(self.task, candidate)["pass"])
        self.assertEqual(candidate["model_execution"]["input_tokens"], 1200)
        self.assertNotIn("telemetry", candidate["payload"])

    def test_legacy_control_uses_frozen_shape_schema_not_agent_proposal_schema(self):
        payload = copy.deepcopy(agent_shadow_compare.visual_semantic_obligations(self.task)["scopes"])
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(payload)}},
            {"type": "turn.completed", "usage": {
                "input_tokens": 1400, "cached_input_tokens": 200,
                "output_tokens": 900, "reasoning_output_tokens": 80,
            }},
        ]
        result = SimpleNamespace(
            output=("\n".join(json.dumps(row) for row in events)).encode("utf-8"),
            remote={"elapsed_seconds": 3.5, "timed_out": False}, returncode=0,
        )

        def execute_with_schema(request):
            argv = request.argv
            schema_index = argv.index("--output-schema")
            schema_path = Path(argv[schema_index + 1])
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual(schema["title"], "StoryOS Visual Narrative legacy Candidate payload")
            self.assertEqual(schema["required"], list(self.task["authority_scope"]))
            self.assertNotIn("proposal", schema["properties"]["visual.narrative_core"]["properties"])
            self.assertFalse(schema["additionalProperties"])
            return result

        with mock.patch.object(producer.codex_user_runner, "resolve_codex", return_value=("codex", "test")), \
             mock.patch.object(producer.codex_user_runner, "bridge_required", return_value=False), \
             mock.patch.object(producer.codex_user_runner, "execute_task", side_effect=execute_with_schema):
            produced = producer.run(self.ep, self.task, role="legacy_control")
        self.assertIsNone(produced["failure_reason"])
        self.assertEqual(produced["payload"], payload)
        candidate = preimage_task_contract.candidate_template(self.task, produced["payload"])
        self.assertEqual(preimage_task_contract.verify_candidate(candidate, self.task), [])
        self.assertTrue(agent_shadow_compare.compare_visual_narrative_semantics(self.task, candidate)["pass"])


if __name__ == "__main__":
    unittest.main()
