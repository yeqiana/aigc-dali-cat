#!/usr/bin/env python3
from __future__ import annotations
import base64, json, mimetypes, os, uuid
from pathlib import Path
from urllib import request, error

import image_artifact_collector
import image_provider_runtime
import image_generation_gateway

class OpenAIImagesProviderError(RuntimeError):
    pass


def payload_capability_preflight(*, model: str, quality: str) -> dict:
    """Check whether the independent API payload route is configured and callable.

    This is intentionally a non-generation preflight.  A successful result only
    proves that the route, credentials, and static model/quality contract are
    present; actual Flare capability remains unconfirmed until a real dispatch.
    """
    configured_model = str(model or "").strip()
    configured_quality = str(quality or "").strip().lower()
    if configured_model != "gpt-image-2.5-flare":
        return {"status": "BLOCKED", "failure_class": "PAYLOAD_MODEL_UNSUPPORTED",
                "provider": "openai_images_api", "requested_model": configured_model,
                "requested_quality": configured_quality, "credential_available": False}
    if configured_quality != "high":
        return {"status": "BLOCKED", "failure_class": "PAYLOAD_QUALITY_UNSUPPORTED",
                "provider": "openai_images_api", "requested_model": configured_model,
                "requested_quality": configured_quality, "credential_available": False}
    try:
        runtime = image_provider_runtime.load()
        api = runtime.get("openai_images_api") or {}
        static = image_provider_runtime.capability_snapshot()["openai_images_api"]
    except Exception as exc:
        return {"status": "BLOCKED", "failure_class": "PAYLOAD_ROUTE_CONFIGURATION_INVALID",
                "provider": "openai_images_api", "detail": type(exc).__name__}
    if api.get("enabled") is not True:
        return {"status": "BLOCKED", "failure_class": "NO_AUTOMATABLE_IMAGE_PAYLOAD_PROVIDER",
                "provider": "openai_images_api", "credential_available": False}
    if str(api.get("model") or "") != configured_model:
        return {"status": "BLOCKED", "failure_class": "PAYLOAD_MODEL_UNSUPPORTED",
                "provider": "openai_images_api", "requested_model": configured_model,
                "configured_model": str(api.get("model") or ""),
                "credential_available": bool(static.get("credential_available"))}
    capability_id = "OPENAI_GPT_IMAGE_2_5_FLARE_API_V1"
    try:
        registry = json.loads((Path(__file__).resolve().parents[2] / "config/providers/gpt-image-2.5-flare-api.json").read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "BLOCKED", "failure_class": "PAYLOAD_CAPABILITY_REGISTRY_INVALID",
                "provider": "openai_images_api", "detail": type(exc).__name__}
    supported_quality = set((registry.get("quality") or {}).get("provider_supported") or [])
    if (registry.get("capability_id") != capability_id
            or registry.get("model") != configured_model
            or configured_quality not in supported_quality
            or (registry.get("quality") or {}).get("formal_required") != "high"):
        return {"status": "BLOCKED", "failure_class": "PAYLOAD_CAPABILITY_CONTRACT_MISMATCH",
                "provider": "openai_images_api", "credential_available": bool(static.get("credential_available"))}
    if not static.get("credential_available"):
        return {"status": "BLOCKED", "failure_class": "NO_AUTOMATABLE_IMAGE_PAYLOAD_PROVIDER",
                "provider": "openai_images_api", "requested_model": configured_model,
                "requested_quality": configured_quality, "credential_available": False,
                "capability_evidence": "STATIC_REGISTRY_ONLY"}
    return {"status": "PASS", "provider": "openai_images_api",
            "requested_model": configured_model, "requested_quality": configured_quality,
            "credential_available": True,
            "capability_evidence": "PAYLOAD_CAPABILITY_UNKNOWN_UNTIL_REAL_DISPATCH",
            "image_generation_available": None}

def provider_size_for_release(width: int, height: int) -> tuple[int, int]:
    # GPT-Image-2 flexible dimensions must be divisible by 16.
    # Preserve Story OS release ratio and prefer downscaling after generation.
    if (width, height) == (1080, 1350):
        return (1088, 1360)  # exact 4:5
    if (width, height) == (1080, 1920):
        return (1152, 2048)  # exact 9:16
    pw = ((int(width) + 15) // 16) * 16
    ph = ((int(height) + 15) // 16) * 16
    return pw, ph

def _headers(api_key: str, *, content_type: str) -> dict[str, str]:
    out = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": content_type,
        "User-Agent": "story-os/2.4.1",
    }
    org = os.environ.get("OPENAI_ORG_ID", "").strip()
    project = os.environ.get("OPENAI_PROJECT_ID", "").strip()
    if org:
        out["OpenAI-Organization"] = org
    if project:
        out["OpenAI-Project"] = project
    return out

def _api_key() -> str:
    env = str((image_provider_runtime.load().get("selection") or {}).get("api_key_env") or "OPENAI_API_KEY")
    value = os.environ.get(env, "").strip()
    if not value:
        raise OpenAIImagesProviderError(f"OPENAI_API_KEY_MISSING: environment variable {env} is not set")
    return value

def _decode_response(raw: bytes, expected: int) -> list[bytes]:
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise OpenAIImagesProviderError("OPENAI_IMAGE_RESPONSE_INVALID_JSON") from exc
    rows = data.get("data") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise OpenAIImagesProviderError("OPENAI_IMAGE_RESPONSE_DATA_MISSING")
    images: list[bytes] = []
    for row in rows:
        b64 = (row or {}).get("b64_json") if isinstance(row, dict) else None
        if not isinstance(b64, str) or not b64:
            raise OpenAIImagesProviderError("OPENAI_IMAGE_RESPONSE_B64_MISSING")
        try:
            images.append(base64.b64decode(b64, validate=True))
        except Exception as exc:
            raise OpenAIImagesProviderError("OPENAI_IMAGE_RESPONSE_B64_INVALID") from exc
    if len(images) != int(expected):
        raise OpenAIImagesProviderError(
            f"OPENAI_IMAGE_COUNT_MISMATCH: requested={expected} returned={len(images)}"
        )
    return images

class _RejectRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _request(req: request.Request, timeout: int) -> tuple[bytes, dict]:
    # Direct official API transport: do not follow redirects with a bearer
    # token or silently inherit machine HTTP(S)_PROXY configuration.
    opener = request.build_opener(request.ProxyHandler({}), _RejectRedirect())
    try:
        with opener.open(req, timeout=timeout) as rsp:
            body = rsp.read()
            headers = {str(k).lower(): str(v) for k, v in rsp.headers.items()}
            return body, headers
    except error.HTTPError as exc:
        # Provider errors may echo prompts/identifiers: never log response body.
        raise OpenAIImagesProviderError(f"OPENAI_IMAGE_HTTP_{exc.code}") from None
    except error.URLError:
        raise OpenAIImagesProviderError("OPENAI_IMAGE_NETWORK_ERROR") from None


def _multipart(fields: dict[str, str], images: list[Path]) -> tuple[bytes, str]:
    boundary = "----StoryOS" + uuid.uuid4().hex
    chunks: list[bytes] = []
    def add(raw: bytes) -> None:
        chunks.append(raw)
    for name, value in fields.items():
        add(f"--{boundary}\r\n".encode())
        add(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        add(str(value).encode("utf-8"))
        add(b"\r\n")
    for image in images:
        mime = mimetypes.guess_type(image.name)[0] or "image/png"
        add(f"--{boundary}\r\n".encode())
        add(f'Content-Disposition: form-data; name="image[]"; filename="{image.name}"\r\n'.encode())
        add(f"Content-Type: {mime}\r\n\r\n".encode())
        add(image.read_bytes())
        add(b"\r\n")
    add(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"

def generate_native_batch(
    *,
    prompt: str,
    references: list[Path],
    count: int,
    model: str,
    quality: str,
    release_width: int,
    release_height: int,
    timeout: int,
    raw_paths: list[Path],
    generation_attempt_leases: list[dict] | None = None,
    episode_dir: Path | None = None,
) -> dict:
    if not 1 <= int(count) <= 10:
        raise OpenAIImagesProviderError("OPENAI_IMAGE_N_OUT_OF_RANGE: n must be 1..10")
    if len(raw_paths) != int(count):
        raise OpenAIImagesProviderError("raw_paths count must match n")
    if not prompt.strip():
        raise OpenAIImagesProviderError("batch prompt is empty")
    api_key = _api_key()
    base = image_provider_runtime.base_url()
    pw, ph = provider_size_for_release(release_width, release_height)
    size = f"{pw}x{ph}"

    if references:
        endpoint = base + "/images/edits"
        fields = {
            "model": model,
            "prompt": prompt,
            "n": str(int(count)),
            "size": size,
            "quality": quality,
            "output_format": "png",
        }
        body, content_type = _multipart(fields, references)
    else:
        endpoint = base + "/images/generations"
        payload = {
            "model": model,
            "prompt": prompt,
            "n": int(count),
            "size": size,
            "quality": quality,
            "output_format": "png",
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        content_type = "application/json"

    req = request.Request(endpoint, data=body, headers=_headers(api_key, content_type=content_type), method="POST")
    if not isinstance(generation_attempt_leases, list) or len(generation_attempt_leases) != int(count):
        raise OpenAIImagesProviderError("GENERATION_ATTEMPT_LEASE_REQUIRED")
    episode = Path(episode_dir or Path.cwd())

    def dispatch_payload():
        def event(name: str, *, status: str, **extra) -> None:
            try:
                import runtime_observability
                runtime_observability.safe_record_runtime_event(
                    episode, name, source="openai_images_provider",
                    step="IMAGE_PAYLOAD_DISPATCH", status=status,
                    provider="openai_images_api", payload_model=model,
                    payload_quality=quality,
                    generation_keys=[str(x.get("generation_key") or "")
                                     for x in generation_attempt_leases],
                    attempt_indices=[x.get("attempt_index") for x in generation_attempt_leases],
                    logical_asset_keys=[str(x.get("logical_asset_key") or "")
                                        for x in generation_attempt_leases], **extra)
            except Exception:
                return

        event("IMAGE_PAYLOAD_DISPATCH_STARTED", status="RUNNING", request_size=[pw, ph],
              endpoint_kind="edits" if references else "generations")
        try:
            response = _request(req, timeout)
        except Exception as exc:
            event("IMAGE_PAYLOAD_DISPATCH_FINISHED", status="FAILED",
                  failure_class=type(exc).__name__)
            raise
        event("IMAGE_PAYLOAD_DISPATCH_FINISHED", status="SUCCESS",
              request_id=response[1].get("x-request-id"))
        return response

    raw, headers = image_generation_gateway.provider_generate_many(
        episode, generation_attempt_leases, "openai_images_api", dispatch_payload)
    images = _decode_response(raw, int(count))
    artifacts = []
    for path, data in zip(raw_paths, images):
        artifacts.append(image_artifact_collector.atomic_write_bytes(path, data))
    return {
        "provider": "openai_images_api",
        "transport": "openai_images_api_native_n",
        "native_multi_image": True,
        "single_http_request": True,
        "requested_count": int(count),
        "returned_count": len(artifacts),
        "provider_request_size": [pw, ph],
        "release_size": [int(release_width), int(release_height)],
        "request_id": headers.get("x-request-id"),
        "endpoint_kind": "edits" if references else "generations",
        "artifacts": artifacts,
    }

def self_test() -> None:
    assert provider_size_for_release(1080, 1350) == (1088, 1360)
    assert provider_size_for_release(1080, 1920) == (1152, 2048)
    print("OPENAI IMAGES PROVIDER V2.4.1 SELF-TEST PASS")

if __name__ == "__main__":
    self_test()
