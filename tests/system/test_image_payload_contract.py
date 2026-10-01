from __future__ import annotations

import copy
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_payload_request


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _valid_fields() -> dict:
    return {
        "episode_id": "canary/phase5a-contract",
        "logical_asset_key": "canary/phase5a-contract/frame-01",
        "frame_id": "frame-1",
        "authority_input_sha256": _sha("authority"),
        "source_prompt_sha256": _sha("source-prompt"),
        "frame_contract_sha256": _sha("frame-contract"),
        "visual_contract_sha256": _sha("visual-contract"),
        "controller_receipt_id": "controller-call-001",
        "controller_output_sha256": _sha("controller-output"),
        "payload_model": "gpt-image-2.5-flare",
        "payload_quality": "high",
        "canvas": {"width": 1080, "height": 1350, "aspect_ratio": "4:5"},
        "references": [
            {
                "authority_id": "references/style/M00",
                "path": "assets/references/m00.png",
                "sha256": _sha("reference"),
            }
        ],
        "scene_prompt": "Preserve the locked frame contract and depict the specified scene.",
        "model_policy_version": "frozen-test-policy-v1",
        "model_policy_sha256": _sha("frozen-policy"),
    }


class ImagePayloadRequestContractTests(unittest.TestCase):
    def test_build_binds_exact_flare_high_and_frozen_policy(self) -> None:
        fields = _valid_fields()
        request = image_payload_request.build_request(**fields)

        self.assertEqual(request["payload_model"], "gpt-image-2.5-flare")
        self.assertEqual(request["payload_quality"], "high")
        self.assertEqual(request["model_policy_sha256"], fields["model_policy_sha256"])
        self.assertEqual(request["canvas"], {"width": 1080, "height": 1350, "aspect_ratio": "4:5"})
        self.assertEqual(
            image_payload_request.validate_request(
                request, expected_policy_sha256=fields["model_policy_sha256"]
            ),
            [],
        )

    def test_fingerprint_is_deterministic_and_ignores_runtime_only_metadata(self) -> None:
        request = image_payload_request.build_request(**_valid_fields())
        expected = request["request_fingerprint"]

        runtime_decorated = copy.deepcopy(request)
        runtime_decorated.update(
            {
                "timestamp": "2099-01-01T00:00:00Z",
                "worker_pid": 4312,
                "worker_id": "worker-new",
                "queue_wait_ms": 300,
                "absolute_temp_path": r"D:\temp\codex-worker-uuid\request.json",
            }
        )

        self.assertEqual(image_payload_request.request_fingerprint(request), expected)
        self.assertEqual(image_payload_request.request_fingerprint(runtime_decorated), expected)

    def test_semantic_change_changes_fingerprint_and_invalidates_existing_request(self) -> None:
        request = image_payload_request.build_request(**_valid_fields())
        changed_fields = _valid_fields()
        changed_fields["scene_prompt"] += " Add one clearly visible paper lantern."
        changed = image_payload_request.build_request(**changed_fields)

        self.assertNotEqual(changed["request_fingerprint"], request["request_fingerprint"])
        tampered = copy.deepcopy(request)
        tampered["scene_prompt"] = changed["scene_prompt"]
        tampered["scene_prompt_sha256"] = changed["scene_prompt_sha256"]
        self.assertIn(
            "IMAGE_PAYLOAD_REQUEST_FINGERPRINT_MISMATCH",
            image_payload_request.validate_request(tampered),
        )

    def test_rejects_non_flare_payload_model_and_non_high_quality(self) -> None:
        for field, value, expected_error in (
            ("payload_model", "gpt-image-2.5-sunburst", "PAYLOAD_MODEL_MISMATCH"),
            ("payload_quality", "medium", "PAYLOAD_QUALITY_MISMATCH"),
        ):
            with self.subTest(field=field):
                fields = _valid_fields()
                fields[field] = value
                with self.assertRaisesRegex(ValueError, expected_error):
                    image_payload_request.build_request(**fields)

    def test_rejects_missing_or_malformed_authority_sha_and_policy_drift(self) -> None:
        fields = _valid_fields()
        fields["frame_contract_sha256"] = "not-a-sha"
        with self.assertRaisesRegex(ValueError, "SHA_INVALID:frame_contract_sha256"):
            image_payload_request.build_request(**fields)

        request = image_payload_request.build_request(**_valid_fields())
        self.assertIn(
            "IMAGE_PAYLOAD_REQUEST_POLICY_SHA_MISMATCH",
            image_payload_request.validate_request(request, expected_policy_sha256=_sha("other-policy")),
        )

    def test_rejects_unstable_reference_paths_and_missing_reference_identity(self) -> None:
        for reference in (
            {"path": r"D:\assets\reference.png", "sha256": _sha("reference")},
            {"path": "assets/.codex_tmp/reference.png", "sha256": _sha("reference")},
            {"sha256": _sha("reference")},
        ):
            with self.subTest(reference=reference):
                fields = _valid_fields()
                fields["references"] = [reference]
                with self.assertRaises(ValueError):
                    image_payload_request.build_request(**fields)

    def test_rejects_inconsistent_canvas_contract(self) -> None:
        fields = _valid_fields()
        fields["canvas"] = {"width": 1080, "height": 1350, "aspect_ratio": "9:16"}
        with self.assertRaisesRegex(ValueError, "CANVAS_ASPECT_RATIO_MISMATCH"):
            image_payload_request.build_request(**fields)

    def test_rejects_fingerprint_tampering(self) -> None:
        request = image_payload_request.build_request(**_valid_fields())
        request["request_fingerprint"] = "0" * 64
        self.assertIn(
            "IMAGE_PAYLOAD_REQUEST_FINGERPRINT_MISMATCH",
            image_payload_request.validate_request(request),
        )


if __name__ == "__main__":
    unittest.main()
