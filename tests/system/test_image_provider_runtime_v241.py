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
    def test_no_automatic_api_to_other_provider_fallback(self):
        assert image_provider_runtime.load()["openai_images_api"]["fallback_on_transport_failure"] is False

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

    def test_disabled_api_route_ignores_present_key(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-not-a-real-key","STORY_OS_IMAGE_RUNTIME":"AUTO"},clear=False):
            row=image_provider_runtime.select_batch_provider(5)
        self.assertNotEqual(row["provider"],"openai_images_api")
        self.assertFalse(image_provider_runtime.capability_snapshot()["openai_images_api"]["configured"])

    def test_api_key_cannot_override_locked_codex(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-only","STORY_OS_IMAGE_RUNTIME":"CODEX"}):
            self.assertEqual(image_provider_runtime.select_batch_provider(5)["provider"],"codex_subscription")

    def test_repository_fallback_never_picks_other_worker_image(self):
        with tempfile.TemporaryDirectory(prefix="repository-") as td:
            root=Path(td); p=root/"unrelated.png"
            p.write_bytes(b"\x89PNG\r\n\x1a\n"+b"q"*64)
            self.assertIsNone(image_artifact_collector.recover_codex_generated(root/"missing.log",root))

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
        with tempfile.TemporaryDirectory(prefix="story-os-image-") as td:
            root=Path(td)
            generated=root/".codex/generated_images/x.png"
            generated.parent.mkdir(parents=True)
            generated.write_bytes(b"\x89PNG\r\n\x1a\n"+b"q"*64)
            log=root/"worker.jsonl"
            log.write_text("no explicit path needed for safe workdir fallback",encoding="utf-8")
            self.assertEqual(image_artifact_collector.recover_codex_generated(log,root),generated.resolve())


    def test_official_api_image_endpoint_rejects_third_party_base_url(self):
        with patch.dict(os.environ, {"OPENAI_BASE_URL": "http://127.0.0.1:10100/v1"}):
            with self.assertRaisesRegex(RuntimeError, "IMAGE_API_BASE_URL_FORBIDDEN"):
                image_provider_runtime.base_url()
        with patch.dict(os.environ, {"OPENAI_BASE_URL": "https://api.openai.com/v1"}):
            self.assertEqual(image_provider_runtime.base_url(), "https://api.openai.com/v1")

    def test_image_provider_redirect_and_http_error_do_not_expose_body(self):
        from urllib.error import HTTPError
        req = openai_images_provider.request.Request(
            "https://api.openai.com/v1/images/generations", data=b"{}", method="POST")
        with patch.object(openai_images_provider.request, "build_opener") as opener:
            opener.return_value.open.side_effect = HTTPError(
                req.full_url, 307, "secret backend details", {},
                __import__("io").BytesIO(b"secret-model-response"))
            with self.assertRaisesRegex(openai_images_provider.OpenAIImagesProviderError,
                                       "OPENAI_IMAGE_HTTP_307") as caught:
                openai_images_provider._request(req, 2)
            self.assertNotIn("secret-model-response", str(caught.exception))
            args = opener.call_args.args
            self.assertTrue(any(isinstance(x, openai_images_provider.request.ProxyHandler)
                                and x.proxies == {} for x in args))
            self.assertTrue(any(isinstance(x, openai_images_provider._RejectRedirect)
                                for x in args))


    def test_dual_only_auto_on_work_skips_product_image_host(self):
        with patch.dict(os.environ, {"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY",
                    "STORY_OS_IMAGE_RUNTIME":"AUTO","OPENAI_API_KEY":""},clear=False), \
             patch.object(image_provider_runtime.runtime_router,"detect",return_value=("WORK",{})), \
             patch.object(image_provider_runtime.runtime_router,"image_execution_runtime",
                          return_value=("AUTO",{})):
            row=image_provider_runtime.select_batch_provider(2)
        self.assertEqual(row["provider"],"codex_subscription")
        self.assertFalse(row["api_key_required"])

    def test_dual_only_explicit_product_runtime_is_blocked(self):
        with patch.dict(os.environ, {"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY"},clear=False), \
             patch.object(image_provider_runtime.runtime_router,"detect",return_value=("WORK",{})), \
             patch.object(image_provider_runtime.runtime_router,"image_execution_runtime",
                          return_value=("PRODUCT_RUNTIME",{})):
            with self.assertRaisesRegex(RuntimeError,"DUAL_ONLY_PRODUCT_IMAGE_FORBIDDEN"):
                image_provider_runtime.select_batch_provider(1)

    def test_dual_only_does_not_auto_dispatch_api_for_secret_alone(self):
        with patch.dict(os.environ, {"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY",
                    "OPENAI_API_KEY":"fake-test-secret"},clear=False), \
             patch.object(image_provider_runtime.runtime_router,"detect",return_value=("WORK",{})), \
             patch.object(image_provider_runtime.runtime_router,"image_execution_runtime",
                          return_value=("AUTO",{})):
            row=image_provider_runtime.select_batch_provider(1)
        # Official API is disabled in config: key presence is never capability proof.
        self.assertEqual(row["provider"],"codex_subscription")

    def test_dual_only_unrecognized_image_runtime_blocks(self):
        with patch.dict(os.environ,{"STORY_OS_MODEL_TRANSPORT_POLICY":"DUAL_ONLY"},clear=False), \
             patch.object(image_provider_runtime.runtime_router,"image_execution_runtime",return_value=("UNKNOWN",{})):
            with self.assertRaisesRegex(RuntimeError,"DUAL_ONLY_PRODUCT_IMAGE_FORBIDDEN"):
                image_provider_runtime.select_batch_provider(1)

class RouterTests(unittest.TestCase):
    def test_router_is_not_stage_authority(self):
        with patch.dict(os.environ,{"OPENAI_API_KEY":"test-not-a-real-key"},clear=False):
            row=image_provider_router.select_for_batch(5,has_references=False)
        self.assertFalse(row["route_is_stage_authority"])

if __name__=="__main__":unittest.main()
