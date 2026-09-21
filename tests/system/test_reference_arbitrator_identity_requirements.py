from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import reference_arbitrator as arbitrator  # noqa: E402


def test_batch_uses_frame_contract_interaction_identity_requirements(monkeypatch, tmp_path):
    contract = {
        "identity_requirements": [
            {"character_id": "P02", "anchor_state": "bound"},
            {"character_id": "P01", "anchor_state": "bound"},
        ],
        "hash_material": {
            "shot_progression": {
                "primary_subject": "老屋门框、门槛与两个人",
                "human_present": True,
                "interaction": {
                    "actor": "P02",
                    "target": "P01",
                    "action": "P02把钥匙递给P01",
                },
            },
            "capture_event": {},
            "frame_directive": {"narrative_role": "setup"},
            "references": [],
        },
    }
    monkeypatch.setattr(
        arbitrator.frame_contract,
        "compile_frame",
        lambda *_args, **_kwargs: contract,
    )
    monkeypatch.setattr(
        arbitrator.character_visual_contract,
        "load",
        lambda _ep: {"members": {"P01": {}, "P02": {}}},
    )
    monkeypatch.setattr(
        arbitrator.character_visual_contract,
        "series_identity_reference",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        arbitrator.character_visual_contract,
        "pixel_master_reference",
        lambda *_args, **_kwargs: {
            "path": "master.png",
            "role": "character_pixel_master",
            "kind": "identity",
            "frame": "01",
        },
    )
    monkeypatch.setattr(
        arbitrator.character_visual_contract,
        "crop_reference",
        lambda _ep, cid, **_kwargs: {
            "path": f"{cid}.png",
            "role": f"character_crop:{cid}",
            "kind": "identity",
            "character_id": cid,
        },
    )

    refs, meta = arbitrator.select(tmp_path, 2, scope="batch")

    assert [row["path"] for row in refs] == ["P02.png", "P01.png"]
    assert meta["identity_needed"] is True
    assert meta["identity_reason"] == "frame_contract_identity_requirements"


def test_identity_need_without_contract_or_human_signal_stays_false(monkeypatch, tmp_path):
    monkeypatch.setattr(
        arbitrator.character_visual_contract,
        "load",
        lambda _ep: {"members": {"P01": {}, "P02": {}}},
    )
    needed, character_id, reason = arbitrator._identity_need(
        tmp_path,
        {"shot_progression": {"primary_subject": "老屋木门", "human_present": False}},
        [],
        scope="batch",
        identity_requirements=[],
    )
    assert needed is False
    assert character_id is None
    assert reason == "no_human_identity_signal"
