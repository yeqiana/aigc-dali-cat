#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Host-agent adapter for WORK/WEB Story OS execution.

This module deliberately does not invoke a model. It prepares machine-readable,
idempotent requests for the surrounding ChatGPT product runtime. Local Python
must never silently fall back to Codex while WORK/WEB is selected.

V2.6.1.1 keeps immutable request history under meta/runtime/host-requests/ while
maintaining meta/runtime/product-host-request.json as a compatibility/current
pointer.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import episode_performance
import preproduction_handoff
import storyos_config

ROOT = Path(__file__).resolve().parents[2]
REQUEST_REL = Path("meta/runtime/product-host-request.json")
REQUEST_HISTORY_REL = Path("meta/runtime/host-requests")
HOST_ACTION_REQUIRED_RC = 20
STAGES = ("IDEA_LOCKED","STORYBOARD_LOCKED","VISUAL_CALIBRATED","PRODUCTION_PASSED","PUBLISH_READY","PUBLISHED","DATA_REVIEWED")

STATE_TO_STEP = {
    "IDEA_LOCKED": ("CREATIVE_STORY", "STORYBOARD_LOCKED"),
    "VISUAL_CALIBRATED": ("PRODUCTION", "PRODUCTION_PASSED"),
    "PRODUCTION_PASSED": ("RELEASE", "PUBLISH_READY"),
}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _stable_hash(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def episode_state(ep: Path) -> str:
    path = ep / "meta/episode-state.json"
    return str(_read_json(path).get("current_state") or "") if path.is_file() else ""


def _state_at_least(current: str, target: str) -> bool:
    return current in STAGES and target in STAGES and STAGES.index(current) >= STAGES.index(target)


def reconcile(ep: Path) -> dict | None:
    """Finalize a stale current host pointer when canonical evidence already proves completion."""
    current_path = ep / REQUEST_REL
    if not current_path.is_file():
        return None
    current = _read_json(current_path)
    if current.get("status") != "HOST_ACTION_REQUIRED":
        return current
    request_id = str(current.get("request_id") or "")
    if not request_id:
        return current
    step = str(current.get("next_step") or "")
    target = str(current.get("target_state") or "")
    cur_state = episode_state(ep)
    complete = bool(target and _state_at_least(cur_state, target))
    if step == "PREIMAGE_COMPILE":
        try:
            complete = (ep / "meta/preproduction-handoff.json").is_file() and not preproduction_handoff.verify(ep)
        except Exception:
            complete = False
    if complete:
        return mark_complete(ep, request_id, result={"reconciled_from_canonical_evidence": True, "episode_state": cur_state, "step": step})
    return current


def next_host_step(ep: Path, mode: str = "full_auto") -> tuple[str, str | None]:
    state = episode_state(ep)
    if state == "STORYBOARD_LOCKED":
        try:
            handoff_valid = (ep / "meta/preproduction-handoff.json").is_file() and not preproduction_handoff.verify(ep)
        except Exception:
            handoff_valid = False
        if not handoff_valid:
            return "PREIMAGE_COMPILE", None
        if mode == "preproduction_only":
            return "COMPLETE", "STORYBOARD_LOCKED"
        return "VISUAL_LOCK", "VISUAL_CALIBRATED"
    if state == "PUBLISH_READY":
        return "COMPLETE", "PUBLISH_READY"
    return STATE_TO_STEP.get(state, ("READ_EPISODE_STATE", None))


def _persist_request(ep: Path, payload: dict, *, category: str) -> dict:
    fingerprint_basis = {
        key: value for key, value in payload.items()
        if key not in {"created_at", "request_id", "request_fingerprint", "request_path", "current_request_path"}
    }
    fingerprint = _stable_hash(fingerprint_basis)
    request_id = f"{category}-{fingerprint[:16]}"
    history_path = ep / REQUEST_HISTORY_REL / f"{request_id}.json"
    if history_path.is_file():
        existing = _read_json(history_path)
        if existing.get("request_fingerprint") != fingerprint:
            raise RuntimeError(f"host request id collision: {request_id}")
        stored = existing
    else:
        stored = {
            **payload,
            "schema_version": 2,
            "request_id": request_id,
            "request_fingerprint": fingerprint,
            "created_at": now(),
        }
        _write_json(history_path, stored)
    current = {
        **stored,
        "request_path": history_path.relative_to(ROOT).as_posix(),
    }
    _write_json(ep / REQUEST_REL, current)
    return {
        **stored,
        "request_path": history_path.relative_to(ROOT).as_posix(),
        "current_request_path": (ep / REQUEST_REL).relative_to(ROOT).as_posix(),
    }


def build_request(
    ep: Path,
    *,
    runtime: str,
    mode: str,
    resume: bool,
    request_data: dict | None = None,
    source: str = "workflow_runner",
) -> dict:
    runtime = str(runtime).upper()
    if runtime not in {"WORK", "WEB"}:
        raise ValueError("product runtime adapter only supports WORK/WEB")
    step, target = next_host_step(ep, mode)
    rel = ep.resolve().relative_to(ROOT.resolve()).as_posix()
    try:
        index=storyos_config.load_index(); required_read=((index.get("stage_read_sets") or {}).get(step) or [])
    except Exception:
        required_read=[]
    step_instructions=[]
    if step=="CREATIVE_STORY":
        step_instructions += [
            "Read config/profiles/account_creative/default.json as the account default topic/style profile, without overriding explicit user constraints or recent-5 anti-homogeneity evidence.",
            "For new/unlocked work author meta/shot-progression-review.json schema_version=3 using standards/directing_grammar_v1.json: large+small shot scales, globally unique scene_position_id, at least two translated classic shot-structure references, practical-light narrative design, and at least one physically valid concealed anomaly carrier for suspense/strange genres. Run shot_progression_gate.py validate before completing CREATIVE_STORY."
        ]
    if step=="RELEASE":
        step_instructions += [
            "Inspect approved images before subtitle rendering. Prefer left-middle 42%-62% height, x=72; if moving outside that band, write safe_zone_override_reason per frame. Never cover faces, anomaly evidence, hands/actions, key props, native text or causal clues.",
            "Keep captions first-person, conversational, concise and eye-catching; canonical renderer maximum remains two lines."
        ]
    data = {
        "runtime": runtime,
        "status": "COMPLETE" if step == "COMPLETE" else "HOST_ACTION_REQUIRED",
        "source": source,
        "episode": rel,
        "episode_state": episode_state(ep),
        "execution_mode": mode,
        "resume": bool(resume),
        "next_step": step,
        "target_state": target,
        "required_read": required_read,
        "local_codex_spawn_allowed": False,
        "local_codex_fallback_allowed": False,
        "host_contract": {
            "actor": "chatgpt_product_runtime",
            "workspace_access": "use DevSpace/workspace tools directly",
            "critic_provenance": f"{runtime}_ISOLATED",
            "image_generation": "delegate only the image execution substep according to runtime.image_execution_runtime; CODEX image mode must not take ownership of Story/PREIMAGE/Review/Release",
            "deterministic_scripts": "may run locally when they do not invoke a model backend",
            "stage_authority": "meta/episode-state.json",
            "must_not_claim_pass_without_evidence": True,
        },
        "instructions": [
            "Execute the declared non-image host step in the surrounding product runtime; do not hand Story/PREIMAGE/Review/Release ownership to local Codex.",
            "Reuse valid SHA-bound evidence and obey existing Story OS gates.",
            "For independent critics, prepare the product review request, author the candidate in a fresh isolated product review turn, then finalize it.",
            "When a later image scheduler runs, honor runtime.image_execution_runtime. CODEX there means image generation/repair only, not CODEX full-auto.",
            *step_instructions,
        ],
    }
    if request_data:
        data["runtime_request_id"] = request_data.get("request_id")
    stored = _persist_request(ep, data, category="host")
    if stored.get("status") == "HOST_ACTION_REQUIRED":
        episode_performance.safe_begin_named_span(
            ep, f"HOST_ACTION_{step}", source=source,
            metadata={"request_id": stored.get("request_id"), "runtime": runtime, "next_step": step})
    return stored


def build_image_request(
    ep: Path,
    *,
    runtime: str,
    queue_items: list[dict],
    source: str,
) -> dict:
    runtime = str(runtime).upper()
    if runtime not in {"WORK", "WEB"}:
        raise ValueError("product image request supports WORK/WEB only")
    rel = ep.resolve().relative_to(ROOT.resolve()).as_posix()
    items = []
    for row in queue_items:
        items.append({
            "id": row.get("id"),
            "frame": int(row.get("frame") or 0),
            "kind": row.get("kind"),
            "scope": row.get("scope"),
            "prompt_file": row.get("prompt_file"),
            "references": row.get("references") or [],
            "model": row.get("model"),
            "quality": row.get("quality"),
            "frame_contract": row.get("frame_contract"),
        })
    items.sort(key=lambda x: (int(x.get("frame") or 0), str(x.get("id") or "")))
    data = {
        "runtime": runtime,
        "status": "HOST_ACTION_REQUIRED",
        "source": source,
        "episode": rel,
        "episode_state": episode_state(ep),
        "next_step": "IMAGE_GENERATION",
        "local_codex_spawn_allowed": False,
        "local_codex_fallback_allowed": False,
        "items": items,
        "host_contract": {
            "actor": "chatgpt_product_runtime",
            "image_model_contract": "use each queue item's locked model/quality",
            "continuity_contract": "respect Frame Contract and reference arbitration",
            "file_transport": "save/import real generated RAW assets when the product runtime supports workspace file transfer",
            "on_missing_file_transport": "pause as HOST_ACTION_REQUIRED; never fall back to local Codex",
        },
    }
    stored = _persist_request(ep, data, category="image")
    episode_performance.safe_begin_named_span(
        ep, "HOST_ACTION_IMAGE_GENERATION", source=source,
        metadata={"request_id": stored.get("request_id"), "runtime": runtime, "count": len(items)})
    return stored


def mark_complete(ep: Path, request_id: str, *, result: dict | None = None) -> dict:
    path = ep / REQUEST_HISTORY_REL / f"{request_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"host request missing: {path}")
    data = _read_json(path)
    data["status"] = "FINALIZED"
    data["finalized_at"] = now()
    span_name = "HOST_ACTION_IMAGE_GENERATION" if str(data.get("next_step") or "") == "IMAGE_GENERATION" else f"HOST_ACTION_{str(data.get('next_step') or 'UNKNOWN')}"
    episode_performance.safe_end_named_span(ep, span_name, status="PASS", metadata={"request_id": request_id})
    if result is not None:
        data["result"] = result
    _write_json(path, data)
    current_path = ep / REQUEST_REL
    if current_path.is_file():
        current = _read_json(current_path)
        if current.get("request_id") == request_id:
            current.update({
                "status": "FINALIZED",
                "finalized_at": data["finalized_at"],
            })
            if result is not None:
                current["result"] = result
            _write_json(current_path, current)
    return data


def print_request(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def self_test() -> None:
    assert HOST_ACTION_REQUIRED_RC == 20
    assert _state_at_least("PUBLISH_READY", "STORYBOARD_LOCKED")
    assert not _state_at_least("IDEA_LOCKED", "STORYBOARD_LOCKED")
    assert STATE_TO_STEP["IDEA_LOCKED"] == ("CREATIVE_STORY", "STORYBOARD_LOCKED")
    assert REQUEST_HISTORY_REL.as_posix() == "meta/runtime/host-requests"
    assert next_host_step.__name__ == "next_host_step"
    print("PRODUCT RUNTIME ADAPTER V2.6.1.1 SELF-TEST PASS")


if __name__ == "__main__":
    self_test()
