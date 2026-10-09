"""Explicit dual-transport *text* dispatch, shadow-only and opt-in.

Never called from production DAG today. Existing official API image adapter
and native image worker remain unchanged pending independent cutover evidence.
No automatic transport fallback and no shadow call side effects.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from urllib.error import HTTPError
import weakref
from collections.abc import Mapping
from types import MappingProxyType
from urllib import request

NATIVE_CODEX_BASE = "https://chatgpt.com/backend-api/codex"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
MAX_PROMPT_BYTES = 131072
MAX_API_RESPONSE_BYTES = 8 * 1024 * 1024

class _RejectRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _post_official(req, *, timeout: int) -> bytes:
    # No environment HTTP_PROXY override and no redirect to a third party
    # carrying a credential. A regular enterprise proxy isn't an API provider.
    opener = request.build_opener(request.ProxyHandler({}), _RejectRedirect())
    with opener.open(req, timeout=timeout) as response:
        raw = response.read(MAX_API_RESPONSE_BYTES + 1)
    if len(raw) > MAX_API_RESPONSE_BYTES:
        raise ValueError("response exceeded size limit")
    return raw


class TransportDispatchBlocked(RuntimeError):
    pass

class TextDispatchPlan(Mapping):
    """Immutable, locally minted plan. An ordinary dict cannot authorize execution."""
    __slots__ = ("_fields", "__weakref__")
    __hash__ = object.__hash__
    __eq__ = object.__eq__
    def __init__(self, fields: dict):
        object.__setattr__(self, "_fields", MappingProxyType(dict(fields)))
    def __setattr__(self, name, value):
        raise AttributeError("MODEL_EXECUTION_PLAN_IMMUTABLE")
    def __getitem__(self, key):
        return self._fields[key]
    def __iter__(self):
        return iter(self._fields)
    def __len__(self):
        return len(self._fields)

_APPROVED_PLANS = weakref.WeakSet()

def _require_minted(plan) -> None:
    if not isinstance(plan, TextDispatchPlan) or plan not in _APPROVED_PLANS:
        raise TransportDispatchBlocked("MODEL_EXECUTION_PLAN_UNTRUSTED")

def plan_text(binding: dict, *, proof: dict | None = None, trusted_verify=None) -> dict:
    from . import capability
    capability_result = capability.resolve(binding, required={"text_generation"},
                                           proof=proof, trusted_verify=trusted_verify)
    if binding.get("transport") not in {"CODEX_NATIVE", "API_KEY_DIRECT"}:
        raise TransportDispatchBlocked("MODEL_TRANSPORT_FORBIDDEN")
    if "text_generation" not in (binding.get("declared_capabilities") or ()):
        raise TransportDispatchBlocked("MODEL_MODALITY_UNSUPPORTED_IN_TEXT_ADAPTER")
    if capability_result.get("status") != "AVAILABLE" or capability_result.get("available") is not True:
        raise TransportDispatchBlocked("MODEL_CAPABILITY_NOT_ATTESTED")
    for key in ("role", "requested_model", "policy_sha256"):
        if not binding.get(key):
            raise TransportDispatchBlocked("MODEL_BINDING_INCOMPLETE")
    fields = {"transport": binding["transport"], "requested_model": binding["requested_model"],
            "role": binding["role"], "policy_sha256": binding["policy_sha256"],
            "modality": "text_generation", "status": "PLANNED",
            "actual_model": None, "fallback_automatic": False}
    plan = TextDispatchPlan(fields)
    _APPROVED_PLANS.add(plan)
    return plan

def _validate_prompt(prompt: str) -> None:
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise TransportDispatchBlocked("MODEL_PROMPT_INVALID")

def dispatch_codex_text(plan: dict, *, prompt: str, authorized: bool = False, runner=None,
                        codex_command: str = "codex", timeout: int = 120) -> dict:
    _validate_prompt(prompt)
    _require_minted(plan)
    if plan.get("transport") != "CODEX_NATIVE" or plan.get("modality") != "text_generation":
        raise TransportDispatchBlocked("MODEL_TRANSPORT_MISMATCH")
    if not authorized:
        raise TransportDispatchBlocked("MODEL_DISPATCH_NOT_AUTHORIZED")
    if runner is None:
        import codex_user_runner
        runner = codex_user_runner.run_codex
    argv = [codex_command, "-c", 'model_provider="openai"',
            "-c", 'openai_base_url="' + NATIVE_CODEX_BASE + '"',
            "exec", "--json", "--skip-git-repo-check", "-m", plan["requested_model"], "-"]
    clean_env = dict(os.environ)
    clean_env.pop("OPENAI_BASE_URL", None)
    clean_env.pop("STORY_OS_IMAGE_PROVIDER_ROUTE", None)
    clean_env["STORY_OS_MODEL_TRANSPORT_POLICY"] = "DUAL_ONLY"
    try:
        result = runner(argv, input=prompt, text=True, encoding="utf-8",
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        timeout=timeout, check=False, env=clean_env,
                        task_type="generic_codex")
    except Exception as exc:
        raise TransportDispatchBlocked("CODEX_NATIVE_OUTCOME_UNKNOWN") from None
    if getattr(result, "returncode", 1) != 0:
        raise TransportDispatchBlocked("CODEX_NATIVE_RESULT_NOT_VERIFIED")
    output = getattr(result, "stdout", b"") or b""
    if isinstance(output, str):
        output = output.encode("utf-8")
    if not output.strip():
        raise TransportDispatchBlocked("CODEX_NATIVE_EMPTY_OUTPUT")
    from . import native_result_evidence
    observed = native_result_evidence.inspect(result)
    if observed["reason"] == "NATIVE_ROUTE_NOT_ATTESTED":
        raise TransportDispatchBlocked("CODEX_NATIVE_ROUTE_UNVERIFIED")
    if observed["status"] != "OBSERVED":
        raise TransportDispatchBlocked("CODEX_NATIVE_PROVENANCE_UNVERIFIED")
    return {"status": "REQUIRES_VALIDATION", "transport": "CODEX_NATIVE",
            "native_runtime_evidence": observed,
            "requested_model": plan["requested_model"], "actual_model": None,
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "output_bytes": len(output)}

def dispatch_openai_text(plan: dict, *, prompt: str, authorized: bool = False,
                         api_key: str | None = None, sender=None, timeout: int = 120) -> dict:
    _validate_prompt(prompt)
    _require_minted(plan)
    if plan.get("transport") != "API_KEY_DIRECT" or plan.get("modality") != "text_generation":
        raise TransportDispatchBlocked("MODEL_TRANSPORT_MISMATCH")
    if not authorized:
        raise TransportDispatchBlocked("MODEL_DISPATCH_NOT_AUTHORIZED")
    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    if not isinstance(key, str) or not key.strip():
        raise TransportDispatchBlocked("OPENAI_API_KEY_MISSING")
    data = json.dumps({"model": plan["requested_model"], "input": prompt},
                      ensure_ascii=False).encode("utf-8")
    req = request.Request(OPENAI_RESPONSES_URL, data=data, method="POST",
                          headers={"Authorization": "Bearer " + key,
                                   "Content-Type": "application/json"})
    try:
        if sender is None:
            raw = _post_official(req, timeout=timeout)
        else:
            raw = sender(req, timeout)
        if not isinstance(raw, bytes) or len(raw) > MAX_API_RESPONSE_BYTES:
            raise ValueError("api response too large or invalid")
        result = json.loads(raw.decode("utf-8"))
        if (not isinstance(result, dict) or not isinstance(result.get("id"), str)
            or not result["id"].strip()):
            raise ValueError("invalid response")
    except HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            raise TransportDispatchBlocked("API_DIRECT_REDIRECT_FORBIDDEN") from None
        # A definite 4xx API refusal is not a successful generation. Never leak body.
        if exc.code in {400, 401, 403, 404, 413, 422, 429}:
            raise TransportDispatchBlocked("API_DIRECT_REQUEST_REJECTED") from None
        raise TransportDispatchBlocked("API_DIRECT_OUTCOME_UNKNOWN") from None
    except Exception:
        # Unknown network outcome may have reached provider. No automatic retry.
        raise TransportDispatchBlocked("API_DIRECT_OUTCOME_UNKNOWN") from None
    status = result.get("status")
    if status in {"in_progress", "queued"}:
        return {"status": "PENDING_RECONCILIATION", "transport": "API_KEY_DIRECT",
                "provider_response_id": result["id"], "actual_model": None}
    if result.get("error") or status != "completed":
        raise TransportDispatchBlocked("API_DIRECT_RESPONSE_NOT_COMPLETE")
    outputs = result.get("output")
    if (not isinstance(outputs, list) or not any(
        isinstance(item, dict) and item.get("type") == "message"
        and isinstance(item.get("content"), list)
        and any(isinstance(part, dict) and part.get("type") == "output_text"
                and isinstance(part.get("text"), str) and part["text"].strip()
                for part in item["content"]) for item in outputs)):
        raise TransportDispatchBlocked("API_DIRECT_OUTPUT_NOT_VERIFIED")
    return {"status": "REQUIRES_VALIDATION", "transport": "API_KEY_DIRECT",
            "requested_model": plan["requested_model"], "reported_model": result.get("model"),
            "actual_model": None, "provider_response_id": result["id"],
            "output_sha256": hashlib.sha256(raw).hexdigest(), "output_bytes": len(raw)}

def reconcile_openai_text(plan, *, response_id: str, authorized: bool = False,
                          api_key: str | None = None, sender=None,
                          timeout: int = 30) -> dict:
    """Read-only GET for a known response ID; never repeats the original POST."""
    import re
    _require_minted(plan)
    if plan.get("transport") != "API_KEY_DIRECT" or plan.get("modality") != "text_generation":
        raise TransportDispatchBlocked("MODEL_TRANSPORT_MISMATCH")
    if not authorized:
        raise TransportDispatchBlocked("MODEL_RECONCILIATION_NOT_AUTHORIZED")
    if not isinstance(response_id, str) or not re.fullmatch(r"resp_[A-Za-z0-9_-]{1,128}", response_id):
        raise TransportDispatchBlocked("API_DIRECT_RESPONSE_ID_INVALID")
    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    if not isinstance(key, str) or not key.strip():
        raise TransportDispatchBlocked("OPENAI_API_KEY_MISSING")
    req = request.Request(
        OPENAI_RESPONSES_URL + "/" + response_id, method="GET",
        headers={"Authorization": "Bearer " + key},
    )
    try:
        if sender is None:
            raw = _post_official(req, timeout=timeout)
        else:
            raw = sender(req, timeout)
        if not isinstance(raw, bytes) or len(raw) > MAX_API_RESPONSE_BYTES:
            raise ValueError("oversized or invalid response")
        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict) or result.get("id") != response_id:
            raise ValueError("response id mismatch")
    except HTTPError as exc:
        if exc.code in {301,302,303,307,308}:
            raise TransportDispatchBlocked("API_DIRECT_REDIRECT_FORBIDDEN") from None
        if exc.code in {400,401,403,404,429}:
            raise TransportDispatchBlocked("API_DIRECT_LOOKUP_REJECTED") from None
        raise TransportDispatchBlocked("API_DIRECT_LOOKUP_OUTCOME_UNKNOWN") from None
    except Exception:
        raise TransportDispatchBlocked("API_DIRECT_LOOKUP_OUTCOME_UNKNOWN") from None
    if result.get("status") in {"queued","in_progress"}:
        return {"status":"PENDING_RECONCILIATION","provider_response_id":response_id,
                "actual_model":None}
    if result.get("error") or result.get("status") != "completed":
        return {"status":"RECONCILED_NON_SUCCESS","provider_response_id":response_id,
                "actual_model":None}
    outputs=result.get("output")
    if not isinstance(outputs,list) or not any(
        isinstance(item,dict) and item.get("type")=="message"
        and isinstance(item.get("content"),list)
        and any(isinstance(part,dict) and part.get("type")=="output_text"
                and isinstance(part.get("text"),str) and part["text"].strip()
                for part in item["content"])
        for item in outputs
    ):
        raise TransportDispatchBlocked("API_DIRECT_OUTPUT_NOT_VERIFIED")
    return {"status":"REQUIRES_VALIDATION","provider_response_id":response_id,
            "actual_model":None,"reported_model":result.get("model"),
            "output_sha256":hashlib.sha256(raw).hexdigest(),"output_bytes":len(raw)}
