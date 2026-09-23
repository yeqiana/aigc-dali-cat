from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_contract  # noqa: E402
import story_json  # noqa: E402


def test_verify_all_compiles_each_frame_once(monkeypatch, tmp_path):
    compile_calls = []
    cache_calls = []
    rows = {}
    for number in (1, 2):
        frame = f"{number:02d}"
        rows[number] = {
            "frame": frame,
            "contract_sha256": f"contract-{frame}",
            "hash_material": {
                "storyboard_frame_sha256": f"storyboard-{frame}",
                "environment_frame_sha256": f"environment-{frame}",
                "frame_directive_sha256": f"directive-{frame}",
            },
        }

    monkeypatch.setattr(frame_contract, "required", lambda _ep: True)
    monkeypatch.setattr(frame_contract, "frame_count", lambda _ep: 2)
    monkeypatch.setattr(frame_contract.environment_contract, "verify", lambda _ep: [])

    def compile_once(_ep, number, *, write_cache):
        assert write_cache is False
        compile_calls.append(number)
        return rows[number]

    def cached_contract(_ep, number):
        cache_calls.append(number)
        return {
            "frame": f"{number:02d}",
            "derived_cache": True,
            "contract_sha256": f"contract-{number:02d}",
        }

    monkeypatch.setattr(frame_contract, "compile_frame", compile_once)
    monkeypatch.setattr(frame_contract, "load_cached_contract", cached_contract)
    monkeypatch.setattr(
        frame_contract, "recorded_contract_matches_current", lambda *_args: False
    )
    expected = [
        {
            "frame": rows[number]["frame"],
            "path": (frame_contract.CACHE_ROOT / f"{rows[number]['frame']}.json").as_posix(),
            "contract_sha256": rows[number]["contract_sha256"],
            "storyboard_frame_sha256": rows[number]["hash_material"]["storyboard_frame_sha256"],
            "environment_frame_sha256": rows[number]["hash_material"]["environment_frame_sha256"],
            "frame_directive_sha256": rows[number]["hash_material"]["frame_directive_sha256"],
        }
        for number in (1, 2)
    ]
    index_path = tmp_path / frame_contract.INDEX_REL
    story_json.write_json(index_path, {
        "frames": [{}, {}],
        "index_sha256": frame_contract.sha256_json(expected),
    })
    monkeypatch.setattr(frame_contract, "INDEX_REL", index_path.relative_to(tmp_path))

    assert frame_contract.verify_all(tmp_path) == []
    assert compile_calls == [1, 2]
    assert cache_calls == [1, 2]
