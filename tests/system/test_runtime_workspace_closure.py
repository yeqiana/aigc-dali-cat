from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import product_runtime_adapter
import production_orchestrator
import runtime_asset_policy
import runtime_execution
import runtime_resume_capsule
import runtime_workspace
import runtime_workspace_migration


def _configure(monkeypatch, tmp_path: Path) -> Path:
    ep = tmp_path / "episode"
    (ep / "meta").mkdir(parents=True)
    (ep / "meta/episode-state.json").write_text(
        json.dumps({"current_state": "IDEA_LOCKED"}), encoding="utf-8"
    )
    monkeypatch.setenv(runtime_workspace.ENV_ROOT, str(tmp_path / "runtime"))
    return ep


def test_runtime_execution_overlay_writes_only_workspace(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    runtime_execution.set_mode(ep, "resume")
    target = runtime_workspace.workspace_path(ep, runtime_execution.REL)
    assert target.is_file()
    assert not (ep / runtime_execution.REL).exists()
    assert runtime_execution.effective_mode(ep) == "resume"


def test_resume_capsule_writes_only_workspace(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    data = runtime_resume_capsule.compile_capsule(ep, write=True)
    target = runtime_workspace.workspace_path(ep, runtime_resume_capsule.REL)
    assert target.is_file()
    assert not (ep / runtime_resume_capsule.REL).exists()
    assert runtime_resume_capsule.load_fresh(ep, write=False)["source_fingerprint"] == data["source_fingerprint"]


def test_product_host_request_and_history_write_only_workspace(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    stored = product_runtime_adapter._persist_request(
        ep,
        {"next_step": "CREATIVE_STORY", "status": "HOST_ACTION_REQUIRED", "host_contract": {"actor": "chatgpt_product_runtime"}},
        category="host",
    )
    history_rel = product_runtime_adapter.REQUEST_HISTORY_REL / f"{stored['request_id']}.json"
    assert runtime_workspace.workspace_path(ep, history_rel).is_file()
    assert runtime_workspace.workspace_path(ep, product_runtime_adapter.REQUEST_REL).is_file()
    assert not (ep / history_rel).exists()
    assert not (ep / product_runtime_adapter.REQUEST_REL).exists()


def test_full_auto_status_writes_only_workspace(monkeypatch, tmp_path):
    ep = _configure(monkeypatch, tmp_path)
    document = production_orchestrator._emit(
        tmp_path,
        ep,
        status=production_orchestrator.FULL_AUTO_STATUS_RUNNING,
        intent={},
        selection={},
        profile_id="M00_REAL_WORLD_DOCUMENTARY_V1",
        lifecycle_state="LOCKED",
        stage="IDEA_LOCKED",
        created=True,
        production={"status": "RUNNING"},
        review="not_run",
        repair="not_run",
    )
    assert document["written"] is True
    assert runtime_workspace.workspace_path(ep, production_orchestrator.STATUS_DOC_REL).is_file()
    assert not (ep / production_orchestrator.STATUS_DOC_REL).exists()


def test_closure_assets_are_classified_and_copy_ready():
    expected = {
        "meta/runtime-execution.json": (runtime_asset_policy.OPERATIONAL_STATE, True),
        "meta/runtime/resume-capsule.json": (runtime_asset_policy.DERIVED_CACHE, True),
        "meta/runtime/product-host-request.json": (runtime_asset_policy.OPERATIONAL_STATE, True),
        "meta/runtime/host-requests/host-1.json": (runtime_asset_policy.FORMAL_EVIDENCE, False),
        "meta/runtime/full-auto-status.json": (runtime_asset_policy.DERIVED_CACHE, True),
    }
    for rel, (category, copy_ready) in expected.items():
        assert runtime_asset_policy.classify(rel).category == category
        assert runtime_workspace_migration.copy_ready(rel) is copy_ready
