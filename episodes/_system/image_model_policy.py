#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS image model policy.

Default production alias comes from config/storyos.yaml (currently GPT-Image-2.5 Flare).
The reproducible snapshot pins the current default family for deterministic reruns.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json
from pathlib import Path
import production_queue_store
import scheduler_core
import runtime_request
import storyos_config

_CONFIG=storyos_config.load_config()
DEFAULT_MODEL=str(storyos_config.get_path(_CONFIG,"image.model"))
DEFAULT_QUALITY=str(storyos_config.get_path(_CONFIG,"image.quality"))
FALLBACK_MODELS=tuple(str(x).strip() for x in storyos_config.get_path(_CONFIG,"image.fallback_models",[]) if str(x).strip())
REPRODUCIBLE_SNAPSHOT="gpt-image-2.5-flare-2026-09-08"
MODEL_UNAVAILABLE="MODEL_UNAVAILABLE"
PROVIDER_CAPACITY="PROVIDER_CAPACITY"
BACKEND_5XX="BACKEND_5XX"
RATE_LIMIT_429="RATE_LIMIT_429"
AUTH_401="AUTH_401"
PERMISSION_403="PERMISSION_403"
LOCAL_WORKSPACE_PERMISSION="LOCAL_WORKSPACE_PERMISSION"
NETWORK_ERROR="NETWORK_ERROR"
ARTIFACT_SAVE_COLLISION="PROVIDER_ARTIFACT_SAVE_COLLISION"
MODEL_UNAVAILABLE_PATTERNS=("model_unavailable","model unavailable","model is not available","requested model is not available","unknown model","unsupported model","model not found","does not exist","cannot honor the requested model")
# Provider/controller capacity is transient and must never masquerade as a generic
# image/content failure. Exact production evidence on 2026-09-15 was:
# "Selected model is at capacity. Please try a different model."
PROVIDER_CAPACITY_PATTERNS=("provider_capacity","selected model is at capacity","model is at capacity","provider is at capacity","capacity temporarily unavailable")
BACKEND_5XX_PATTERNS=("500 internal server error","502 bad gateway","503 service unavailable","504 gateway timeout","upstream_server_error","server_error")
RATE_LIMIT_PATTERNS=("429","too many requests","rate limit")
AUTH_401_PATTERNS=("401 unauthorized","http 401","status code 401","authentication required")
PERMISSION_403_PATTERNS=("403 forbidden","http 403","permission denied")
LOCAL_WORKSPACE_PERMISSION_PATTERNS=(
    "codex_user_runner_workspace_unavailable",
    "failed to grant runner access",
)
NETWORK_ERROR_PATTERNS=("network error","error sending request","connection reset","connection aborted","connection refused","connection closed","transport channel closed")
# STORY_OS_V2_6_2_ARTIFACT_COLLISION: the Codex image tool can generate a real picture and
# still fail its own local save (Windows os error 183 / ERROR_ALREADY_EXISTS). Story OS only
# observes "no valid image", so this signature must stay a technical failure that never
# consumes content repair and must never be mistaken for a model or content rejection.
ARTIFACT_SAVE_COLLISION_PATTERNS=("failed to save generated image","os error 183","error_already_exists","cannot create a file when that file already exists","当文件已存在时")

def classify_backend_error(text, *, source="image_backend"):
    low=str(text or "").lower()
    if source != "image_backend":
        return None
    if any(x in low for x in AUTH_401_PATTERNS): return AUTH_401
    # Local staging/ACL failures are recoverable infrastructure faults, not a
    # provider authorization verdict. Keep real HTTP/provider 403 fail-closed.
    if (any(x in low for x in LOCAL_WORKSPACE_PERMISSION_PATTERNS)
            or ("permission denied" in low and "story-os-image-" in low)):
        return LOCAL_WORKSPACE_PERMISSION
    if any(x in low for x in PERMISSION_403_PATTERNS): return PERMISSION_403
    if any(x in low for x in NETWORK_ERROR_PATTERNS): return NETWORK_ERROR
    if any(x in low for x in PROVIDER_CAPACITY_PATTERNS): return PROVIDER_CAPACITY
    if any(x in low for x in MODEL_UNAVAILABLE_PATTERNS): return MODEL_UNAVAILABLE
    if any(x in low for x in ARTIFACT_SAVE_COLLISION_PATTERNS): return ARTIFACT_SAVE_COLLISION
    if any(x in low for x in RATE_LIMIT_PATTERNS): return RATE_LIMIT_429
    if any(x in low for x in BACKEND_5XX_PATTERNS): return BACKEND_5XX
    return None

def resolve_model(*,request=None,explicit=None,explicit_quality=None,reproducible=False):
    quality=str(explicit_quality or (request or {}).get("image_quality") or ((request or {}).get("image") or {}).get("quality") or DEFAULT_QUALITY).strip().lower()
    if quality != DEFAULT_QUALITY:
        raise ValueError(f"formal image quality must be {DEFAULT_QUALITY!r}; got {quality!r}")
    if explicit:
        return {"provider":"openai","model":explicit,"quality":quality,"source":"user_explicit","strict_model":True,"reproducible_snapshot":explicit==REPRODUCIBLE_SNAPSHOT}
    if request:
        image=request.get("image") or {}; model=str(request.get("image_model") or image.get("model") or "").strip()
        if model:
            return {"provider":str(image.get("provider") or "openai"),"model":model,"quality":quality,"source":str(image.get("source") or "runtime_request"),"strict_model":bool(image.get("strict_model")),"reproducible_snapshot":model==REPRODUCIBLE_SNAPSHOT}
    model=REPRODUCIBLE_SNAPSHOT if reproducible else DEFAULT_MODEL
    return {"provider":"openai","model":model,"quality":quality,"source":"system_default_reproducible" if reproducible else "system_default","strict_model":False,"reproducible_snapshot":reproducible}

def for_episode(ep,*,explicit=None,explicit_quality=None,reproducible=False):
    return resolve_model(request=runtime_request.effective_for_episode(ep.resolve()),explicit=explicit,explicit_quality=explicit_quality,reproducible=reproducible)


def next_fallback_model(current_model: str, *, strict_model: bool = False) -> str | None:
    """Next bounded availability fallback for a non-strict system-default model."""
    if strict_model:
        return None
    chain=(DEFAULT_MODEL,*FALLBACK_MODELS)
    current=str(current_model or "").strip()
    try:
        index=chain.index(current)
    except ValueError:
        return None
    return chain[index+1] if index+1<len(chain) else None


def _migrate_system_default_locked(episode_dir: Path, *, target_model: str | None = None) -> dict:
    """Explicitly migrate a non-strict system-default Episode to a new default model.

    Historical generated rows keep their original model evidence. Only pending or
    retryable queue work that inherited the same old system default is retargeted.
    User-explicit/strict model contracts are never rewritten.
    """
    ep=Path(episode_dir).resolve()
    request=runtime_request.effective_for_episode(ep)
    if not request:
        raise ValueError("RUNTIME_REQUEST_MISSING")
    image=request.get("image") or {}
    if str(image.get("source") or "")!="system_default" or bool(image.get("strict_model")):
        raise ValueError("IMAGE_MODEL_MIGRATION_FORBIDDEN: request is not a non-strict system_default")
    old_model=str(image.get("model") or request.get("image_model") or "").strip()
    target=str(target_model or DEFAULT_MODEL).strip()
    if not target:
        raise ValueError("IMAGE_MODEL_MIGRATION_TARGET_MISSING")
    import provider_capability
    provider_capability.resolve(target,"codex_subscription")

    queue=scheduler_core.load_queue(ep)
    active=[x for x in (queue.get("items") or []) if isinstance(x,dict) and x.get("status")=="running"]
    if active:
        raise ValueError(f"IMAGE_MODEL_MIGRATION_BLOCKED: {len(active)} image item(s) still running")

    stamp=dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    creative_projection_sha=runtime_request.preimage_authority_projection_sha256(request)
    mutable_statuses={"queued","tech_failed","external_blocked","blocked","interrupted_unknown"}
    updated=0
    reclassified=0
    for item in queue.get("items") or []:
        if not isinstance(item,dict) or item.get("status") not in mutable_statuses:
            continue
        # Older runs may have persisted the generic code before a more specific
        # provider signature was introduced. Normalize only the current summary;
        # the historical technical_failures array remains untouched evidence.
        current_code=str(item.get("technical_failure_code") or "").strip().upper()
        if current_code in {"", "IMAGE_BACKEND_ERROR"}:
            specific=classify_backend_error(str(item.get("last_error") or ""),source="image_backend")
            if specific and specific!=current_code:
                item["technical_failure_code"]=specific
                item["technical_failure_reclassified_at"]=stamp
                reclassified+=1
        if old_model==target:
            continue
        if bool(item.get("strict_model")) or str(item.get("model") or "")!=old_model:
            continue
        item["model"]=target
        item["model_migration"]={"from":old_model,"to":target,"at":stamp,"reason":"system_default_upgrade"}
        updated+=1

    if old_model==target:
        if reclassified:
            scheduler_core.save_queue(ep,queue)
        evidence_path=ep/"meta/runtime/image-model-migration.json"
        existing=runtime_request.read_json(evidence_path) if evidence_path.is_file() else {}
        migration=(request.get("provenance") or {}).get("image_model_migration") or {}
        if existing and migration:
            existing["preimage_authority_projection_sha256"]=creative_projection_sha
            existing["preimage_authority_preserved"]=True
            existing["evidence_upgraded_at"]=stamp
            runtime_request.write_json(evidence_path,existing)
        return {"status":"NO_CHANGE","episode":str(ep),"from":old_model,"to":target,
                "queue_items_updated":0,"technical_codes_reclassified":reclassified,
                "preimage_authority_projection_sha256":creative_projection_sha}

    corrected=json.loads(json.dumps(request,ensure_ascii=False))
    seed=f"{request.get('request_id')}|{old_model}|{target}|{stamp}"
    corrected["request_id"]=dt.datetime.now().strftime("%Y%m%d_%H%M%S")+"_"+hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    corrected["created_at"]=stamp
    corrected["image_model"]=target
    corrected.setdefault("image",{})["model"]=target
    corrected["image"]["source"]="system_default"
    corrected["image"]["strict_model"]=False
    provenance=corrected.setdefault("provenance",{})
    provenance["creative_request_id"]=(provenance.get("creative_request_id") or request.get("request_id"))
    provenance["image_model_migration"]={
        "from":old_model,"to":target,"at":stamp,
        "source_request_id":request.get("request_id"),"reason":"system_default_upgrade",
    }
    corrected_projection_sha=runtime_request.preimage_authority_projection_sha256(corrected)
    if corrected_projection_sha!=creative_projection_sha:
        raise ValueError("IMAGE_MODEL_MIGRATION_PREIMAGE_AUTHORITY_DRIFT")
    errors=runtime_request.validate_request(corrected)
    if errors:
        raise ValueError("; ".join(errors))
    compiled=runtime_request.write_compiled(corrected)
    runtime_request.bind_request(compiled,ep,force=True)
    if updated or reclassified:
        scheduler_core.save_queue(ep,queue)
    evidence={
        "schema_version":1,"status":"MIGRATED","episode":str(ep),"at":stamp,
        "from":old_model,"to":target,"source_request_id":request.get("request_id"),
        "request_id":corrected["request_id"],"request_path":str(compiled),
        "queue_items_updated":updated,"technical_codes_reclassified":reclassified,
        "historical_generated_rows_preserved":True,
        "preimage_authority_projection_sha256":creative_projection_sha,
        "preimage_authority_preserved":True,
    }
    runtime_request.write_json(ep/"meta/runtime/image-model-migration.json",evidence)
    return evidence


def migrate_system_default(episode_dir: Path, *, target_model: str | None = None) -> dict:
    ep = Path(episode_dir).resolve()
    with scheduler_core.queue_transaction(ep):
        return _migrate_system_default_locked(ep, target_model=target_model)


def self_test():
    assert resolve_model()["model"]==DEFAULT_MODEL
    assert resolve_model()["quality"]=="high"
    assert resolve_model(reproducible=True)["model"]==REPRODUCIBLE_SNAPSHOT
    assert resolve_model(explicit="gpt-image-2")["strict_model"] is True
    assert classify_backend_error("unknown model")=="MODEL_UNAVAILABLE"
    assert classify_backend_error("Selected model is at capacity. Please try a different model.")=="PROVIDER_CAPACITY"
    assert classify_backend_error("PROVIDER_CAPACITY: requested=gpt-image-2")=="PROVIDER_CAPACITY"
    assert classify_backend_error("502 Bad Gateway upstream_server_error")=="BACKEND_5XX"
    assert classify_backend_error("429 Too Many Requests")=="RATE_LIMIT_429"
    assert classify_backend_error("image generation failed: network error: error sending request")=="NETWORK_ERROR"
    assert next_fallback_model(DEFAULT_MODEL,strict_model=False)==FALLBACK_MODELS[0]
    assert next_fallback_model(DEFAULT_MODEL,strict_model=True) is None
    assert next_fallback_model(FALLBACK_MODELS[-1],strict_model=False) is None
    assert classify_backend_error("failed to save generated image: cannot create a file when that file already exists. (os error 183)")=="PROVIDER_ARTIFACT_SAVE_COLLISION"
    print("IMAGE MODEL POLICY V2.1 SELF-TEST PASS")

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("resolve");p.add_argument("--episode-dir",type=Path);p.add_argument("--image-model");p.add_argument("--image-quality",choices=["high"]);p.add_argument("--reproducible",action="store_true")
    p=sub.add_parser("migrate-system-default");p.add_argument("episode_dir",type=Path);p.add_argument("--model")
    sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    if a.cmd=="migrate-system-default":
        print(json.dumps(migrate_system_default(a.episode_dir,target_model=a.model),ensure_ascii=False,indent=2));return 0
    data=for_episode(a.episode_dir,explicit=a.image_model,explicit_quality=a.image_quality,reproducible=a.reproducible) if a.episode_dir else resolve_model(explicit=a.image_model,explicit_quality=a.image_quality,reproducible=a.reproducible)
    print(json.dumps(data,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
