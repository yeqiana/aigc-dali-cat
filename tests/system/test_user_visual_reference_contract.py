from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import image_scheduler  # noqa: E402
import user_visual_reference_contract as overlay  # noqa: E402


def test_overlay_is_sha_bound_and_frame_scoped(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    ep = repo / "episodes" / "e"
    ep.mkdir(parents=True)
    image = repo / "ref.png"
    image.write_bytes(b"frame04")
    sha = hashlib.sha256(b"frame04").hexdigest()
    payload = {
        "schema_version": 1,
        "items": [{
            "id": "JINGYU",
            "path": "ref.png",
            "sha256": sha,
            "frames": [4, 5],
            "scopes": ["repair"],
            "role": "jingyu_architecture_style_anchor",
            "kind": "location",
            "decision": "locked",
        }],
    }
    monkeypatch.setattr(overlay, "ROOT", repo)
    monkeypatch.setattr(overlay.episode_contract_persistence, "load_latest", lambda *_args, **_kwargs: payload)

    refs = overlay.references_for_frame(ep, 5, "repair")
    assert refs[0]["path"] == "ref.png"
    assert refs[0]["sha256"] == sha
    assert overlay.references_for_frame(ep, 6, "repair") == []
    assert overlay.references_for_frame(ep, 5, "visual_lock") == []


def test_user_overlay_keeps_identity_then_replaces_lower_priority_context():
    base = [
        {"path": "identity.png", "role": "identity", "kind": "identity"},
        {"path": "prop.png", "role": "prop", "kind": "prop"},
    ]
    user = [{"path": "frame04.png", "role": "jingyu_architecture_style_anchor", "kind": "location"}]
    merged = image_scheduler._merge_execution_references(base, user)
    assert [x["path"] for x in merged] == ["identity.png", "frame04.png"]
