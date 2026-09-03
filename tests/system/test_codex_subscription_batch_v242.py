#!/usr/bin/env python3
from __future__ import annotations
import os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes/_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))

import codex_logical_batch_worker
import codex_subscription_batch_runtime
import image_provider_runtime

class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        self.assertTrue(codex_subscription_batch_runtime.enabled())
        self.assertEqual(codex_subscription_batch_runtime.batch_size(),5)
        self.assertEqual(codex_subscription_batch_runtime.max_inflight(),5)
        self.assertEqual(codex_subscription_batch_runtime.adaptive_steps(),[5,3,1])

    def test_no_api_key_routes_logical_codex(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":""},clear=False):
            row=image_provider_runtime.select_batch_provider(5)
        self.assertEqual(row["provider"],"codex_subscription")
        self.assertEqual(row["execution_mode"],"logical_parallel_fanout")
        self.assertTrue(row["logical_batch"])
        self.assertFalse(row["native_multi_image"])
        self.assertFalse(row["api_key_required"])

class LogicalWorkerTests(unittest.TestCase):
    def test_parallel_five_success(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td)
            items=[{"id":f"id{i}","frame":i,"attempts":1} for i in range(1,6)]
            contract={"batch_id":"BATCH_TEST","planned_count":5}
            def fake_execute(ep,item,timeout,codex):
                out=ep/f"{item['id']}-{item['attempts']}.png"
                out.write_bytes(b"\x89PNG\r\n\x1a\n"+b"x"*64)
                return {"returncode":0,"stdout":"","output":out,"payload":{"backend":"codex_subscription"}}
            with patch("codex_logical_batch_worker.image_worker_pool.execute",side_effect=fake_execute), \
                 patch("codex_logical_batch_worker.runtime_trace.start_span",return_value="s"), \
                 patch("codex_logical_batch_worker.runtime_trace.end_span",return_value=None):
                row=codex_logical_batch_worker.execute(ep,contract,items,120,None)
            self.assertTrue(row["ok"])
            self.assertEqual(row["returned_count"],5)
            self.assertTrue(row["logical_batch"])
            self.assertFalse(row["native_multi_image"])
            self.assertFalse(row["single_http_request"])
            evidence=(ep/"meta/codex-subscription-batch-capability.json").read_text(encoding="utf-8")
            self.assertIn('"initial_max_inflight": 5', evidence)
            self.assertIn('"logical_batch": true', evidence)

    def test_partial_success_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td)
            items=[{"id":f"id{i}","frame":i,"attempts":1} for i in range(1,6)]
            contract={"batch_id":"BATCH_PARTIAL","planned_count":5}
            def fake_execute(ep,item,timeout,codex):
                if item["id"]=="id5":
                    return {"returncode":99,"stdout":"429","output":None,"payload":None}
                out=ep/f"{item['id']}-{item['attempts']}.png"
                out.write_bytes(b"\x89PNG\r\n\x1a\n"+b"x"*64)
                return {"returncode":0,"stdout":"","output":out,"payload":{"backend":"codex_subscription"}}
            with patch("codex_logical_batch_worker.image_worker_pool.execute",side_effect=fake_execute), \
                 patch("codex_logical_batch_worker.runtime_trace.start_span",return_value="s"), \
                 patch("codex_logical_batch_worker.runtime_trace.end_span",return_value=None):
                row=codex_logical_batch_worker.execute(ep,contract,items,120,None)
            self.assertFalse(row["ok"])
            self.assertTrue(row["partial_success"])
            self.assertEqual(row["returned_count"],4)
            self.assertEqual(set(row["results"]),{"id1","id2","id3","id4"})
            self.assertEqual(set(row["failures"]),{"id5"})

    def test_retry_clone_defers_scout(self):
        rows=codex_logical_batch_worker._round_items([{"id":"x","frame":1,"attempts":1}],1)
        self.assertTrue(rows[0]["_defer_scout"])
        self.assertEqual(rows[0]["attempts"],2)

if __name__=="__main__":unittest.main()
