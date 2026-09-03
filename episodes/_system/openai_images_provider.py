#!/usr/bin/env python3
from __future__ import annotations
import base64, json, mimetypes, os, uuid
from pathlib import Path
from urllib import request, error

import image_artifact_collector
import image_provider_runtime

class OpenAIImagesProviderError(RuntimeError):
    pass

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

def _request(req: request.Request, timeout: int) -> tuple[bytes, dict]:
    try:
        with request.urlopen(req, timeout=timeout) as rsp:
            body = rsp.read()
            headers = {str(k).lower(): str(v) for k, v in rsp.headers.items()}
            return body, headers
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[-4000:]
        raise OpenAIImagesProviderError(f"OPENAI_IMAGE_HTTP_{exc.code}: {body}") from exc
    except error.URLError as exc:
        raise OpenAIImagesProviderError(f"OPENAI_IMAGE_NETWORK_ERROR: {exc.reason}") from exc

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
    raw, headers = _request(req, timeout)
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
