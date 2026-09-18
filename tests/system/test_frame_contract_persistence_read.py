from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import frame_contract_persistence as persistence  # noqa: E402


def test_json_mode_reads_legacy_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    path = ep / "meta/runtime/contracts/frames/03.json"
    path.parent.mkdir(parents=True)
    persistence.story_json.write_json(path, {"frame": "03", "source": "file"})
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "json"},
    )
    assert persistence.load_latest(ep, 3) == {"frame": "03", "source": "file"}


def test_dual_mode_falls_back_to_file_when_mysql_fails(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    path = ep / "frame.json"
    persistence.story_json.write_json(path, {"frame": "03", "source": "file"})
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "dual"},
    )
    monkeypatch.setattr(
        persistence.storage_config,
        "mysql_connection_kwargs",
        lambda *_args, **_kwargs: {"host": "invalid"},
    )

    class BrokenConnection:
        def __init__(self, **_kwargs):
            raise RuntimeError("offline")

    import platform.repository.mysql.mysql_connection as mysql_connection

    monkeypatch.setattr(mysql_connection, "MySqlConnection", BrokenConnection)
    assert persistence.load_latest(ep, 3, legacy_path=path) == {"frame": "03", "source": "file"}


def test_mysql_mode_reads_database_without_legacy_file(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        persistence.storage_config,
        "mysql_connection_kwargs",
        lambda *_args, **_kwargs: {},
    )

    class FakeConnection:
        def __init__(self, **_kwargs):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeRepository:
        def __init__(self, _connection):
            pass

        def get_latest(self, _episode_id, frame_no):
            assert frame_no == 3
            return {"payload": {"frame": "03", "source": "mysql"}}

    import platform.repository.mysql.mysql_connection as mysql_connection
    import platform.repository.mysql.mysql_frame_contract_repository as frame_repository

    monkeypatch.setattr(mysql_connection, "MySqlConnection", FakeConnection)
    monkeypatch.setattr(frame_repository, "MySqlFrameContractRepository", FakeRepository)
    assert persistence.load_latest(ep, 3) == {"frame": "03", "source": "mysql"}


def test_mysql_mode_reads_full_document_from_bounded_projection(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    full = {
        "frame": "03",
        "contract_sha256": "a" * 64,
        "hash_material": {"scene": "x" * 10000},
        "prompt_contract": "prompt " * 1000,
    }
    monkeypatch.setattr(persistence.runtime_workspace, "runtime_root", lambda: tmp_path / "runtime")
    ref = persistence.externalize(ep, full)
    newer_ref = persistence.externalize(ep, {**full, "contract_sha256": "b" * 64})
    assert ref["rel"] != newer_ref["rel"]
    projection = {
        "projection_type": "FRAME_CONTRACT_REF",
        "projection_version": 1,
        "document": ref,
        "frame": "03",
        "contract_sha256": "a" * 64,
    }
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        persistence.storage_config,
        "mysql_connection_kwargs",
        lambda *_args, **_kwargs: {},
    )

    class FakeConnection:
        def close(self):
            pass

    class FakeRepository:
        def __init__(self, _connection):
            pass

        def get_latest(self, _episode_id, frame_no):
            assert frame_no == 3
            return {"sha256": "a" * 64, "payload": projection}

    import platform.repository.mysql.mysql_connection as mysql_connection
    import platform.repository.mysql.mysql_frame_contract_repository as frame_repository

    monkeypatch.setattr(mysql_connection, "MySqlConnection", FakeConnection)
    monkeypatch.setattr(frame_repository, "MySqlFrameContractRepository", FakeRepository)

    assert persistence.load_latest(ep, 3) == full


def test_mysql_persist_writes_external_document_and_bounded_reference(monkeypatch, tmp_path):
    ep = tmp_path / "ep"
    row = {
        "frame": "03",
        "contract_sha256": "a" * 64,
        "hash_material": {"scene": "x" * 10000},
    }
    monkeypatch.setattr(persistence.runtime_workspace, "runtime_root", lambda: tmp_path / "runtime")
    monkeypatch.setattr(
        persistence.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    monkeypatch.setattr(
        persistence.storage_config,
        "mysql_connection_kwargs",
        lambda *_args, **_kwargs: {},
    )

    class FakeConnection:
        def close(self):
            pass

    captured = {}

    class FakeRepository:
        def __init__(self, _connection):
            pass

        def save_version(self, record):
            captured.update(record)
            return {"frame_contract_id": "FC_TEST"}

    import platform.repository.mysql.mysql_connection as mysql_connection
    import platform.repository.mysql.mysql_frame_contract_repository as frame_repository

    monkeypatch.setattr(mysql_connection, "MySqlConnection", FakeConnection)
    monkeypatch.setattr(frame_repository, "MySqlFrameContractRepository", FakeRepository)

    result = persistence.persist(ep, row)
    ref = result["document_ref"]
    assert captured["payload_ref"] == ref
    assert ref["rel"].startswith("meta/runtime/contracts/frames/03-")
    assert ref["bytes"] > len(row["hash_material"]["scene"])
    assert persistence.runtime_workspace.read_json(ep, ref["rel"]) == row
