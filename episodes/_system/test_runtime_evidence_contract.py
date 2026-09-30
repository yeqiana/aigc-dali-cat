from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import runtime_evidence_contract as contract
import runtime_observability
import storage_config


class RuntimeEvidenceMysqlTests(unittest.TestCase):
    def test_mysql_sinks_are_read_from_canonical_stores_without_backfill(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp)
            contract.story_json.write_json(ep / contract.REL, {
                "schema_version": 1,
                "contract": "runtime_evidence_complete_before_production_pass",
                "required_sinks": list(contract.REQUIRED_SINKS),
                "historical_backfill_allowed": False,
            })
            for rel in contract.REQUIRED_SINKS:
                if rel not in {
                    runtime_observability.EPISODE_PERFORMANCE_REL.as_posix(),
                    runtime_observability.TRACE_EVENTS_REL.as_posix(),
                }:
                    path = ep / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("{}\n" if rel.endswith(".json") else '{"event":"ok"}\n', encoding="utf-8")

            with mock.patch.object(storage_config, "episode_meta_store_config", return_value={"mode": "mysql"}), \
                 mock.patch.object(runtime_observability, "read_summary", return_value={"kind": "episode"}), \
                 mock.patch("runtime_fact_store.load_trace_events", return_value=[{"event": "TRACE_START"}]):
                self.assertEqual(contract.verify(ep), [])
            self.assertFalse((ep / runtime_observability.EPISODE_PERFORMANCE_REL).exists())
            self.assertFalse((ep / runtime_observability.TRACE_EVENTS_REL).exists())

    def test_missing_mysql_records_still_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            ep = Path(tmp)
            contract.story_json.write_json(ep / contract.REL, {
                "schema_version": 1,
                "contract": "runtime_evidence_complete_before_production_pass",
                "required_sinks": list(contract.REQUIRED_SINKS),
                "historical_backfill_allowed": False,
            })
            with mock.patch.object(storage_config, "episode_meta_store_config", return_value={"mode": "mysql"}), \
                 mock.patch.object(runtime_observability, "read_summary", return_value={}), \
                 mock.patch("runtime_fact_store.load_trace_events", return_value=[]):
                errors = contract.verify(ep)
            self.assertIn("RUNTIME_EVIDENCE_MISSING:meta/episode-performance-ledger.json", errors)
            self.assertIn("RUNTIME_EVIDENCE_MISSING:meta/runtime/trace-events.jsonl", errors)


if __name__ == "__main__":
    unittest.main()
