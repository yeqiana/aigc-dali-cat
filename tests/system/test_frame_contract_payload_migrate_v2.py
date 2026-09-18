from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_contract_payload_migrate_v2 as migrate  # noqa: E402


def _payload():
    return {"frame": "03", "contract_sha256": "a" * 64, "hash_material": {"large": "x" * 10000}}


def test_plan_reports_compaction_savings_without_writing(monkeypatch, tmp_path):
    payload = _payload()

    class Repository:
        def list_versions(self):
            return [{"frame_contract_id": "FC_1", "episode_id": "EPU_1", "payload": payload}]

    monkeypatch.setattr(migrate, "episode_map", lambda _root: {"EPU_1": tmp_path})
    result = migrate.plan(Repository(), tmp_path)

    assert result["errors"] == []
    assert result["rows"][0]["status"] == "READY"
    assert result["rows"][0]["projected_bytes"] < result["rows"][0]["payload_bytes"]
    assert not list(tmp_path.rglob("*.json"))


def test_apply_externalizes_then_updates_and_reconciles(monkeypatch, tmp_path):
    payload = _payload()
    captured = {}

    class Repository:
        def compact_payload(self, contract_id, value, ref):
            captured.update({"contract_id": contract_id, "payload": value, "ref": ref})

        def get_by_id(self, contract_id):
            return {
                "frame_contract_id": contract_id,
                "payload": {
                    "projection_type": "FRAME_CONTRACT_REF",
                    "document": {"sha256": captured["ref"]["sha256"]},
                },
            }

    monkeypatch.setattr(migrate, "episode_map", lambda _root: {"EPU_1": tmp_path})
    plan = migrate.plan(
        type("PlanRepository", (), {"list_versions": lambda _self: [
            {"frame_contract_id": "FC_1", "episode_id": "EPU_1", "payload": payload}
        ]})(),
        tmp_path,
    )
    monkeypatch.setattr(
        migrate.frame_contract_persistence,
        "externalize",
        lambda _ep, _payload: {"rel": "meta/runtime/contracts/frames/03-a.json", "sha256": "b" * 64, "bytes": 10},
    )

    result = migrate.apply(plan, Repository(), reconcile=True)

    assert result == {"compacted": 1, "reconciled": 1}
    assert captured["contract_id"] == "FC_1"
