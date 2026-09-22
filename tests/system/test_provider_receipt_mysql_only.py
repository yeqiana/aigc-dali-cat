from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import provider_capability  # noqa: E402


def test_mysql_mode_write_and_finalize_do_not_create_receipt_json(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    (ep / "meta").mkdir(parents=True)
    output = ep / "media/01.png"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"final-pixels")
    receipt = {
        "recorded_at_epoch": 123,
        "frame": "01",
        "provider": "test-provider",
        "capability_id": "CAP-1",
        "raw_sha256": "a" * 64,
    }
    persisted = []
    monkeypatch.setattr(
        provider_capability.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        provider_capability.provider_receipt_persistence,
        "persist",
        lambda episode, payload, **kwargs: persisted.append((Path(episode), dict(payload), dict(kwargs))) or {"mysql_written": True},
    )

    info = provider_capability.write_receipt(ep, 1, receipt)
    receipt_path = Path(info["path"])
    assert not receipt_path.exists()
    assert persisted[-1][2]["status"] == "RECORDED"

    monkeypatch.setattr(
        provider_capability.provider_receipt_persistence,
        "load_by_path",
        lambda _episode, _path: {"source": "mysql", "payload": receipt},
    )
    finalized = provider_capability.finalize_receipt(
        receipt_path,
        {
            "operation": "resize",
            "ratio_delta": 0.0,
            "crop_applied": False,
            "reencoded": True,
            "local_attempts": 1,
            "target_size": (1080, 1440),
        },
        output,
    )
    assert not receipt_path.exists()
    assert finalized["receipt"]["release_canvas"]["width"] == 1080
    assert persisted[-1][2]["status"] == "FINALIZED"
