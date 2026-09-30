from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import generation_attempt_authority as attempt_authority
import image_generation_gateway
import image_scheduler
import image_worker_pool
import logical_asset_identity
import model_policy
import frame_scout_persistence
import production_ledger
import production_ledger_persistence
import review_queue
import scheduler_core
import storage_config
from platform.repository.mysql.mysql_connection import MySqlConnection
from platform.repository.mysql.schema_v2 import DATABASE_NAME, DDL_STEPS


def _test_mysql_connection_factory():
    # Pin the destination to the TEST_ONLY local container. User/password still
    # come only from storage_config's approved environment-backed source.
    config = storage_config.mysql_connection_kwargs({
        "host": "127.0.0.1", "port": 3306, "database": DATABASE_NAME,
    })
    if str(config.get("database")).casefold() != "story_os_runtime":
        raise RuntimeError("TEST_ONLY MySQL must use story_os_runtime")
    return lambda: MySqlConnection(**config)


def _test_only_episode(tmp_root: Path) -> Path:
    ep = tmp_root / "phase5a-fake-subpath"
    (ep / "meta").mkdir(parents=True)
    (ep / "meta" / "test-only-marker.json").write_text(
        json.dumps(
            {
                "workspace_class": "TEST_ONLY",
                "promotion_class": "NON_PROMOTABLE",
                "canary_type": "PHASE5A_COLLABORATIVE_REGRESSION",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (ep / "meta" / "release-manifest.json").write_text(
        json.dumps({"episode": {"aspect_ratio": "4:5"}, "release": {"body_frame_count": 1}}),
        encoding="utf-8",
    )
    prompt = ep / "frame-01.prompt.md"
    prompt.write_text("TEST_ONLY production-subpath prompt; no canonical story or stage.", encoding="utf-8")
    return ep


def test_scheduler_worker_attempt_gateway_artifact_and_review_queue_fake_provider(monkeypatch):
    """Exercise the real dispatch/accounting/artifact/queue path with no Provider call."""
    try:
        connection_factory = _test_mysql_connection_factory()
        conn = connection_factory()
        conn.health_check()
        for name, sql in DDL_STEPS:
            if name in {"create_generation_asset_state", "create_generation_attempt"}:
                conn.execute(sql)
        conn.close()
    except Exception as exc:
        pytest.skip(f"TEST_ONLY MySQL 8.0 required for real Attempt Authority: {exc}")

    temp_root = ROOT / ".codex_tmp" / "phase5a"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fake-subpath-", dir=temp_root) as temp_dir:
        ep = _test_only_episode(Path(temp_dir))
        monkeypatch.setattr(attempt_authority, "_connect", connection_factory)

        # The TEST_ONLY episode has no Stage authority. Model policy resolution is
        # fixture input here; Attempt reservation/dispatch/terminal persistence stays MySQL-backed.
        bound_image_policy = {
            "model": "gpt-image-2.5-flare",
            "quality": "high",
            "strict_model": False,
            "model_policy_sha256": "a" * 64,
        }
        monkeypatch.setattr(image_worker_pool.image_model_policy, "for_episode", lambda *_a, **_k: dict(bound_image_policy))
        monkeypatch.setattr(image_worker_pool.backend.model_policy, "validate_bound_policy", lambda *_a: [])
        monkeypatch.setattr(
            image_worker_pool.backend.model_policy,
            "resolve",
            lambda role, episode=None: ({
                "model": "gpt-6-luna",
                "reasoning_effort": "high",
                "profile": "image_controller",
                "model_policy_sha256": "a" * 64,
            } if role == "image.controller" and episode else {}),
        )
        monkeypatch.setattr(image_worker_pool.runtime_router, "detect", lambda: ("CODEX", "test"))
        monkeypatch.setattr(image_worker_pool.runtime_router, "image_execution_runtime", lambda: ("CODEX", "test"))
        monkeypatch.setattr(image_worker_pool.resource_library, "ensure_fresh", lambda *_a: None)
        monkeypatch.setattr(image_worker_pool.prompt_package, "compile_frame", lambda *_a, **_k: {
            "package_sha256": "b" * 64,
            "scene_prompt_sha256": "c" * 64,
            "frame_contract_sha256": "d" * 64,
        })
        monkeypatch.setattr(image_worker_pool.runtime_circuit_breaker, "blocking", lambda *_a: None)
        monkeypatch.setattr(image_worker_pool.runtime_circuit_breaker, "record_success", lambda *_a: None)
        monkeypatch.setattr(image_worker_pool.runtime_trace, "current", lambda *_a: {})
        monkeypatch.setattr(image_worker_pool.runtime_trace, "start_span", lambda *_a, **_k: "test-span")
        monkeypatch.setattr(image_worker_pool.runtime_trace, "end_span", lambda *_a, **_k: None)
        monkeypatch.setattr(image_worker_pool.production_recovery, "write_lifecycle", lambda *_a, **_k: None)
        monkeypatch.setattr(image_worker_pool.backend, "compile_prompt_contract", lambda *_a, **_k: {
            "text": "TEST_ONLY visual contract",
            "profile_id": "test-profile",
            "profile_path": "TEST_ONLY",
            "profile_sha256": "e" * 64,
            "capture_profile": {},
        })
        monkeypatch.setattr(image_worker_pool.backend.resolved_frame_contract, "required", lambda *_a: False)

        dispatches = []

        def fake_invoke(_prompt_path, _refs, raw_output, _log, _size, _timeout, _codex,
                        _visual_contract=None, _frame_contract_text=None, _image_model=None,
                        _image_quality=None, _strict_model=False, **kwargs):
            lease = kwargs["generation_attempt_lease"]
            lease_copy = dict(lease)
            dispatches.append(lease_copy["generation_key"])

            def fake_provider():
                Image.new("RGB", (1024, 1280), color=(96, 128, 112)).save(raw_output, format="PNG")
                return {"provider_stub": "TEST_ONLY", "returncode": 0}

            image_generation_gateway.provider_generate(
                kwargs["episode_dir"], lease, lease["fencing_token"], "codex_subscription",
                fake_provider,
            )
            return 0.01

        monkeypatch.setattr(image_worker_pool.backend, "invoke_codex", fake_invoke)

        # Keep only the non-authoritative ledger projection local to this test. The
        # Generation Attempt Authority remains the real TEST_ONLY MySQL database.
        ledger_projection = {}
        monkeypatch.setattr(production_ledger_persistence, "mode", lambda: "mysql")
        monkeypatch.setattr(production_ledger_persistence, "persist_authority", lambda _ep, value: ledger_projection.update(value))
        monkeypatch.setattr(production_ledger_persistence, "load_authority", lambda _ep: dict(ledger_projection) or None)

        item = {
            "id": "phase5a-fake-item-01",
            "frame": 1,
            "kind": "original",
            "scope": "production",
            "status": "running",
            "attempts": 1,
            "prompt_file": (ep / "frame-01.prompt.md").relative_to(ROOT).as_posix(),
            "capture_id": "PHASE5A_TEST_ONLY",
            "model": bound_image_policy["model"],
            "quality": "high",
            "references": [],
        }
        result = asyncio.run(image_scheduler.async_backend_worker(ep, item, 30, "codex"))
        assert result["returncode"] == 0
        artifact = Path(result["output"])
        assert artifact.is_file()
        assert image_worker_pool.backend.valid_image(artifact)
        asset_key = logical_asset_identity.frame_asset_key(ep, 1)
        state = attempt_authority.load_asset_state(ep, asset_key)
        assert state["attempts_consumed"] == 1
        assert state["active_attempt_index"] is None
        assert len(dispatches) == 1
        generation_key = item["generation_key"]

        # Make current-candidate evidence explicit for stale-artifact protection.
        ledger_projection.update({
            "frames": {"01": {"current_candidate": {
                "path": str(artifact),
                "sha256": image_worker_pool.backend.provider_capability.sha256_file(artifact),
            }}}
        })
        queue = {"schema_version": 1, "items": [], "waves": []}
        monkeypatch.setattr(scheduler_core.hot_state_bridge, "read", lambda *_a: {"mode": "file", "value": None})
        monkeypatch.setattr(scheduler_core.hot_state_bridge, "mirror", lambda *_a: {"mode": "file", "redis_written": False})
        scheduler_core.save_queue(ep, queue)
        monkeypatch.setattr(model_policy, "resolve", lambda *_a, **_k: {
            "role": "vision.fast", "profile": "vision_fast", "model": "gpt-6-luna",
            "model_policy_sha256": bound_image_policy["model_policy_sha256"],
        })

        enqueued = review_queue.enqueue_generated(
            queue, episode=ep, source_item={**item, "generation_key": generation_key, "attempt_index": 1},
            artifact=artifact, artifact_path=artifact.relative_to(ROOT).as_posix(),
        )
        assert enqueued["status"] == "ENQUEUED"
        scheduler_core.save_queue(ep, queue)
        review_calls = []

        def fake_review(_ep, _frame, _image, **kwargs):
            review_calls.append(kwargs["review_context"]["generation_key"])
            return {
                "frame": "01",
                "asset_path": artifact.relative_to(ROOT).as_posix(),
                "asset_sha256": image_worker_pool.backend.provider_capability.sha256_file(artifact),
                "decision": "PASS_FAST", "issue_codes": [], "notes": "TEST_ONLY stub review",
                "model_called": False, "scout_status": "test_stub",
            }

        monkeypatch.setattr(review_queue, "telemetry", lambda *_a, **_k: None)
        monkeypatch.setattr(frame_scout_persistence, "save", lambda *_a, **_k: {"persisted": False})
        monkeypatch.setattr("fast_frame_scout.evaluate_candidate", fake_review)
        changed = asyncio.Event()
        progress = asyncio.Event()
        stop = asyncio.Event()
        stop.set()
        asyncio.run(review_queue.run_lane(
            ep, changed=changed, progress=progress, stop=stop, codex="codex",
            timeout=30, max_inflight=1,
        ))

        persisted = scheduler_core.load_queue(ep)
        review_rows = persisted.get(review_queue.QUEUE_KEY) or []
        assert len(review_rows) == 1
        assert review_rows[0]["status"] == "finalized"
        assert review_rows[0]["receipt"]["review_outcome"] == "PASS"
        assert review_rows[0]["generation_key"] == generation_key
        assert len(review_calls) == 1
        assert attempt_authority.load_asset_state(ep, asset_key)["attempts_consumed"] == 1

