#!/usr/bin/env python3
from __future__ import annotations
import json, sys, tempfile, time, unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes/_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))

import provider_capability, request_intent, request_router, runtime_request, runtime_trace, story_os_contract

class ProviderCapabilityTests(unittest.TestCase):
    def test_smoke_4_5(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.png";Image.new("RGB",(1122,1402)).save(p)
            r=provider_capability.inspect(p,1080,1350,model="gpt-image-2",route="codex_subscription",frame=1)
            self.assertFalse(r["provider_raw_canvas"]["exact_requested_canvas"])
            self.assertEqual(r["normalize_decision"],"AUTO_NORMALIZE")
            self.assertEqual(r["provider_raw_canvas"]["resize_direction_to_release"],"downscale")
    def test_smoke_9_16(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"raw.png";Image.new("RGB",(941,1672)).save(p)
            r=provider_capability.inspect(p,1080,1920,model="gpt-image-2",route="codex_subscription",frame=1)
            self.assertFalse(r["provider_raw_canvas"]["exact_requested_canvas"])
            self.assertEqual(r["normalize_decision"],"AUTO_NORMALIZE")
            self.assertEqual(r["provider_raw_canvas"]["resize_direction_to_release"],"upscale")

class IntentTests(unittest.TestCase):
    def test_rules(self):
        self.assertEqual(request_intent.resolve("不要生成图片，只做前期")["intent"],"PREPRODUCTION")
        self.assertEqual(request_intent.resolve("接管前期资产，从生图开始")["intent"],"IMAGE_CONTINUE")
        self.assertEqual(request_intent.resolve("只返修13")["intent"],"REPAIR")
    def test_runtime_request_contains_intent(self):
        req=runtime_request.compile_request("全自动做一篇「Agent Runtime Test」。")
        self.assertEqual(req["intent"]["intent"],"CREATE_EPISODE")
        self.assertEqual(runtime_request.validate_request(req),[])

class RouterTests(unittest.TestCase):
    def test_route_not_stage_authority(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td);(ep/"meta").mkdir()
            (ep/"meta/episode-state.json").write_text(json.dumps({"current_state":"STORYBOARD_LOCKED"}),encoding="utf-8")
            req=runtime_request.compile_request("接管「Agent Runtime Test」已经完成的前期资产，不要重写剧情，从生图开始继续做到最终交付。")
            d=request_router.decide(ep,req)
            self.assertEqual(d["workflow_mode"],"image_continue")
            self.assertEqual(d["entry_step"],"VISUAL_LOCK")
            self.assertFalse(d["route_is_stage_authority"])
            self.assertIn("story",d["preserve"])

class TraceTests(unittest.TestCase):
    def test_trace_jsonl(self):
        with tempfile.TemporaryDirectory() as td:
            ep=Path(td);(ep/"meta/runtime").mkdir(parents=True)
            trace=runtime_trace.start_run(ep,"run-test",{"request_id":"req-test"},"CODEX",None)
            t0=time.monotonic();sp=runtime_trace.start_span(ep,"UNIT",category="test",trace_id=trace,run_id="run-test")
            runtime_trace.end_span(ep,sp,name="UNIT",category="test",status="PASS",started_monotonic=t0,trace_id=trace,run_id="run-test")
            s=runtime_trace.finish_run(ep,trace,"run-test","COMPLETE")
            self.assertGreaterEqual(s["span_end_count"],1)
            self.assertFalse(s["stage_authority"])

class PlatformTests(unittest.TestCase):
    def test_platform(self):
        # V2.3 Agent Runtime regression must survive later platform releases.
        manifest=json.loads((ROOT/"story_os_manifest.json").read_text(encoding="utf-8-sig"))
        self.assertEqual(story_os_contract.story_os_version(),manifest["platform_version"])
        self.assertGreaterEqual(tuple(int(x) for x in story_os_contract.story_os_version().split(".")),(2,3,0))

if __name__=="__main__":unittest.main()
