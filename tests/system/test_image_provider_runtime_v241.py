#!/usr/bin/env python3
from __future__ import annotations
import base64, json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes/_system"
if str(SYSTEM) not in sys.path:sys.path.insert(0,str(SYSTEM))

import image_artifact_collector
import image_provider_runtime
import image_provider_router
import openai_images_provider

class ProviderRuntimeTests(unittest.TestCase):
    def test_native_n_contract(self):
        cfg=image_provider_runtime.load()
        self.assertEqual(cfg["openai_images_api"]["native_n_max"],10)
        self.assertTrue(cfg["openai_images_api"]["per_frame_review_required"])

    def test_no_key_routes_codex(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":""},clear=False):
            row=image_provider_runtime.select_batch_provider(5)
        self.assertEqual(row["provider"],"codex_subscription")
        self.assertFalse(row["native_multi_image"])
        self.assertEqual(row["max_images"],1)

    def test_key_routes_openai(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-not-a-real-key"},clear=False):
            row=image_provider_runtime.select_batch_provider(5)
        self.assertEqual(row["provider"],"openai_images_api")
        self.assertTrue(row["native_multi_image"])

    def test_release_canvas_provider_size(self):
        self.assertEqual(openai_images_provider.provider_size_for_release(1080,1350),(1088,1360))
        self.assertEqual(openai_images_provider.provider_size_for_release(1080,1920),(1152,2048))

    def test_artifact_atomic_write(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"x.png"
            fake=b"\x89PNG\r\n\x1a\n"+b"x"*64
            row=image_artifact_collector.atomic_write_bytes(p,fake)
            self.assertTrue(p.is_file())
            self.assertEqual(row["bytes"],len(fake))

    def test_exact_native_n_response_decode(self):
        fake=b"\x89PNG\r\n\x1a\n"+b"z"*64
        body=json.dumps({"data":[{"b64_json":base64.b64encode(fake).decode("ascii")} for _ in range(5)]}).encode()
        rows=openai_images_provider._decode_response(body,5)
        self.assertEqual(len(rows),5)
        with self.assertRaises(openai_images_provider.OpenAIImagesProviderError):
            openai_images_provider._decode_response(body,4)

    def test_artifact_recovery_from_worker_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            generated=root/".codex/generated_images/x.png"
            generated.parent.mkdir(parents=True)
            generated.write_bytes(b"\x89PNG\r\n\x1a\n"+b"q"*64)
            log=root/"worker.jsonl"
            log.write_text("no explicit path needed for safe workdir fallback",encoding="utf-8")
            self.assertEqual(image_artifact_collector.recover_codex_generated(log,root),generated.resolve())

class RouterTests(unittest.TestCase):
    def test_router_is_not_stage_authority(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-not-a-real-key"},clear=False):
            row=image_provider_router.select_for_batch(5,has_references=False)
        self.assertFalse(row["route_is_stage_authority"])

if __name__=="__main__":unittest.main()
