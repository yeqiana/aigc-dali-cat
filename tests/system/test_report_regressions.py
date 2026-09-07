"""Behavior checks for the September repository audit fixes."""
import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"episodes/_system"))
import batch_runtime_config as config
import batch_scheduler
import batch_result_mapper
import batch_repair_arbiter
import batch_runtime_metrics
import image_scheduler
import production_ledger
import visual_profile
import visual_profile_bridge_v224 as bridge


class ReportTests(unittest.TestCase):
    def test_queue_seed_honors_configured_concurrency(self):
        with tempfile.TemporaryDirectory() as td, patch.object(image_scheduler,"MAX_SUPPORTED_WORKERS",1):
            ep=Path(td)
            self.assertEqual(image_scheduler.load_queue(ep)["max_parallel"],1)
            queue=image_scheduler.init_queue(ep)
            self.assertEqual(queue["max_parallel"],1)
            self.assertEqual(queue["adaptive_parallel"],1)

    def test_subscription_route_does_not_inherit_global_gateway(self):
        import os
        import codex_subscription_image as backend
        with patch.dict(os.environ,{"STORY_OS_IMAGE_PROVIDER_ROUTE":"","OPENAI_BASE_URL":"http://127.0.0.1:10100/v1"}):
            args=backend.controller_args()
            self.assertIn('openai_base_url="https://chatgpt.com/backend-api/codex"',args)
            self.assertIn('gpt-5.6-luna',args)
            self.assertIn('model_reasoning_effort="medium"',args)
            self.assertFalse(any('10100' in x for x in args))
        with patch.dict(os.environ,{"STORY_OS_IMAGE_PROVIDER_ROUTE":"api_http","OPENAI_BASE_URL":"http://127.0.0.1:9999/v1"}):
            self.assertTrue(any('9999' in x for x in backend.controller_args()))

    def test_invalid_config_does_not_silently_default(self):
        for value in (None,0,False,"5",11):
            with patch.object(config,"load",return_value={"images_per_batch":value}):
                with self.assertRaises(ValueError): config.images_per_batch()
        with patch.object(config,"load",return_value={"repair_gate":{"deviation_high_min":0,"criticality_high_min":100}}):
            self.assertEqual(config.repair_thresholds(),(0,100))

    def test_frozen_repair_policy(self):
        self.assertEqual(production_ledger.content_repair_limit({}),1)
        self.assertEqual(production_ledger.content_repair_limit({"policy":{"max_content_repairs_per_frame":0}}),0)
        with self.assertRaises(ValueError):
            production_ledger.content_repair_limit({"policy":{"max_content_repairs_per_frame":3}})

    def test_visual_compiler_entrypoints_agree(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td)
            self.assertEqual(visual_profile.resolve_profile(ep),bridge.resolve_profile(ep))
            self.assertEqual(visual_profile.compile_prompt_contract(ep),bridge.compile_prompt_contract(ep))

    def test_configured_subscription_is_probeable_not_verified(self):
        snapshot={"codex_subscription":{"configured":True,"runtime_eligible":True}}
        with tempfile.TemporaryDirectory() as td, patch.object(batch_scheduler.image_provider_runtime,"capability_snapshot",return_value=snapshot):
            self.assertTrue(batch_scheduler.ensure_image_capability(Path(td)))
            self.assertFalse(batch_scheduler.verified_image_lane(Path(td)))

    def test_empty_single_scheduler_finishes(self):
        with patch.object(image_scheduler.resource_library,"ensure_fresh"), patch.object(image_scheduler,"load_queue",return_value={}), patch.object(image_scheduler,"ready_items",return_value=([],[])):
            self.assertEqual(asyncio.run(image_scheduler._run_scheduler_async(Path("."),3,60,None)),0)

    def test_real_mapper_checks(self): batch_result_mapper.self_test()

    def test_real_arbiter_checks(self): batch_repair_arbiter.self_test()

    def test_real_metrics_checks(self): batch_runtime_metrics.self_test()


if __name__=="__main__": unittest.main()
