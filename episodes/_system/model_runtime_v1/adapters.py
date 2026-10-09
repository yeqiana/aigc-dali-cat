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
from urllib import request

NATIVE_CODEX_BASE = "https://chatgpt.com/backend-api/codex"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
MAX_PROMPT_BYTES = 131072

class TransportDispatchBlocked(RuntimeError):
    pass

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
    return {"verified_capability": True, "transport": binding["transport"], "requested_model": binding["requested_model"],
            "role": binding["role"], "policy_sha256": binding["policy_sha256"],
            "modality": "text_generation", "status": "PLANNED",
            "actual_model": None, "fallback_automatic": False}

def _validate_prompt(prompt: str) -> None:
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise TransportDispatchBlocked("MODEL_PROMPT_INVALID")

def dispatch_codex_text(plan: dict, *, prompt: str, authorized: bool = False, runner=None,
                        codex_command: str = "codex", timeout: int = 120) -> dict:
    _validate_prompt(prompt)
    if plan.get("transport") != "CODEX_NATIVE" or plan.get("modality") != "text_generation":
        raise TransportDispatchBlocked("MODEL_TRANSPORT_MISMATCH")
    if not authorized:
        raise TransportDispatchBlocked("MODEL_DISPATCH_NOT_AUTHORIZED")
    if plan.get("verified_capability") is not True:
        raise TransportDispatchBlocked("MODEL_CAPABILITY_NOT_ATTESTED")
    if runner is None:
        import codex_user_runner
        runner = codex_user_runner.run_codex
    argv = [codex_command, "-c", 'openai_base_url="' + NATIVE_CODEX_BASE + '"',
            "exec", "--json", "--skip-git-repo-check", "-m", plan["requested_model"], "-"]
    clean_env = dict(os.environ)
    clean_env.pop("OPENAI_BASE_URL", None)
    clean_env.pop("STORY_OS_IMAGE_PROVIDER_ROUTE", None)
    try:
        result = runner(argv, stdin_text=prompt, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, timeout=timeout, check=False,
                        env=clean_env, task_type="generic_codex")
    except Exception as exc:
        raise TransportDispatchBlocked("CODEX_NATIVE_OUTCOME_UNKNOWN") from None
    if getattr(result, "returncode", 1) != 0:
        raise TransportDispatchBlocked("CODEX_NATIVE_RESULT_NOT_VERIFIED")
    output = getattr(result, "stdout", b"") or b""
    if isinstance(output, str):
        output = output.encode("utf-8")
    return {"status": "REQUIRES_VALIDATION", "transport": "CODEX_NATIVE",
            "requested_model": plan["requested_model"], "actual_model": None,
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "output_bytes": len(output)}

def dispatch_openai_text(plan: dict, *, prompt: str, authorized: bool = False,
                         api_key: str | None = None, sender=None, timeout: int = 120) -> dict:
    _validate_prompt(prompt)
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
            with request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
        else:
            raw = sender(req, timeout)
        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict) or not isinstance(result.get("id"), str):
            raise ValueError("invalid response")
    except Exception:
        # Never include HTTP exception bodies/headers or keys in exceptions.
        # A timeout may have reached the provider: forbid blind retries.
        raise TransportDispatchBlocked("API_DIRECT_OUTCOME_UNKNOWN") from None
    return {"status": "REQUIRES_VALIDATION", "transport": "API_KEY_DIRECT",
            "requested_model": plan["requested_model"], "reported_model": result.get("model"),
            "actual_model": None, "provider_response_id": result["id"],
            "output_sha256": hashlib.sha256(raw).hexdigest(), "output_bytes": len(raw)}
