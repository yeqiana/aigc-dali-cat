from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import formal_evidence_bridge  # noqa: E402
import episode_identity  # noqa: E402
import runtime_asset_policy  # noqa: E402


def _write(ep: Path, rel: str, value: dict) -> None:
    path = ep / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_bridge_indexes_formal_evidence_not_runtime_state(tmp_path):
    ep = tmp_path / "ep"
    _write(ep, "meta/episode-state.json", {"episode_id": "EP-X", "current_state": "IDEA_LOCKED"})
    _write(ep, "meta/provider-receipts/01-1.json", {"receipt": True})
    _write(ep, "meta/production-ledger.json", {"frames": {}})
    _write(ep, "meta/runtime/runtime-evidence-contract.json", {"contract": "x"})
    _write(ep, "meta/runtime/next-action.json", {"action": "x"})
    _write(ep, "meta/runtime/contracts/frames/01.json", {"derived": True})

    index = formal_evidence_bridge.build_index(ep)
    paths = {row["path"] for row in index["evidence"]}
    assert "meta/provider-receipts/01-1.json" in paths
    assert "meta/production-ledger.json" in paths
    assert "meta/runtime/runtime-evidence-contract.json" in paths
    assert "meta/runtime/next-action.json" not in paths
    assert "meta/runtime/contracts/frames/01.json" not in paths
    assert all(row["artifact_type"] == "EVIDENCE" for row in index["artifact_registration_rows"])
    expected_owner_id = episode_identity.storage_episode_id(ep)
    assert expected_owner_id != "EP-X"
    assert index["owner_id"] == expected_owner_id
    assert all(row["owner_id"] == expected_owner_id for row in index["artifact_registration_rows"])


def test_index_is_formal_evidence_but_not_self_hashed(tmp_path):
    ep = tmp_path / "ep"
    _write(ep, "meta/episode-state.json", {"current_state": "IDEA_LOCKED"})
    _write(ep, "meta/provider-receipts/01-1.json", {"receipt": True})
    existing = ep / formal_evidence_bridge.INDEX_REL
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("{}", encoding="utf-8")

    assert runtime_asset_policy.classify(formal_evidence_bridge.INDEX_REL).category == runtime_asset_policy.FORMAL_EVIDENCE
    index = formal_evidence_bridge.build_index(ep)
    assert formal_evidence_bridge.INDEX_REL.as_posix() not in {row["path"] for row in index["evidence"]}


def test_build_is_read_only(tmp_path):
    ep = tmp_path / "ep"
    _write(ep, "meta/provider-receipts/01-1.json", {"receipt": True})
    formal_evidence_bridge.build_index(ep)
    assert not (ep / formal_evidence_bridge.INDEX_REL).exists()
