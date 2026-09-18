from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import approval_persistence  # noqa: E402
import delegated_release_persistence  # noqa: E402
import frame_contract_persistence  # noqa: E402
import frame_review_persistence  # noqa: E402
import frame_scout_persistence  # noqa: E402
import host_request_persistence  # noqa: E402
import prompt_package_persistence  # noqa: E402
import provider_receipt_persistence  # noqa: E402
import rolling_review_persistence  # noqa: E402
import runtime_review_persistence  # noqa: E402
import validation_report_persistence  # noqa: E402


class FakeConnection:
    def __init__(self, **_kwargs):
        pass

    def close(self):
        pass


def _mysql_mode(module, monkeypatch):
    monkeypatch.setattr(
        module.storage_config,
        "episode_meta_store_config",
        lambda: {"mode": "mysql"},
    )
    if hasattr(module.storage_config, "mysql_connection_kwargs"):
        monkeypatch.setattr(
            module.storage_config,
            "mysql_connection_kwargs",
            lambda *_args, **_kwargs: {},
        )
    if hasattr(module, "episode_identity"):
        monkeypatch.setattr(
            module.episode_identity,
            "storage_episode_id",
            lambda _ep: "EPU_authority_test",
        )


def _patch_connection(monkeypatch):
    import platform.repository.mysql.mysql_connection as mysql_connection

    monkeypatch.setattr(mysql_connection, "MySqlConnection", FakeConnection)


def test_approval_mysql_missing_ignores_stale_json(monkeypatch, tmp_path):
    module = approval_persistence
    ep = tmp_path / "ep"
    legacy = ep / module.REL_BY_TYPE[module.FINAL_ACCEPTANCE]
    legacy.parent.mkdir(parents=True)
    module.story_json.write_json(legacy, {"decision": "stale-file"})
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_approval_record_repository as repo

    monkeypatch.setattr(repo.MySqlApprovalRecordRepository, "get_current", lambda *_a, **_k: None)
    assert module.load(ep, module.FINAL_ACCEPTANCE) is None


def test_delegated_release_mysql_missing_ignores_stale_json(monkeypatch, tmp_path):
    module = delegated_release_persistence
    ep = tmp_path / "ep"
    legacy = ep / module.REL
    legacy.parent.mkdir(parents=True)
    module.story_json.write_json(legacy, {"status": "stale-file"})
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_release_record_repository as repo

    monkeypatch.setattr(repo.MySqlReleaseRecordRepository, "get_current", lambda *_a, **_k: None)
    assert module.load(ep) is None


def test_frame_contract_mysql_missing_ignores_stale_json(monkeypatch, tmp_path):
    module = frame_contract_persistence
    ep = tmp_path / "ep"
    legacy = ep / "meta/runtime/contracts/frames/03.json"
    legacy.parent.mkdir(parents=True)
    module.story_json.write_json(legacy, {"frame": "03", "contract_sha256": "stale"})
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_frame_contract_repository as repo

    monkeypatch.setattr(repo.MySqlFrameContractRepository, "get_latest", lambda *_a, **_k: None)
    assert module.load_latest(ep, 3, legacy_path=legacy) is None


@pytest.mark.parametrize(
    "module,frame,attempt",
    [
        (frame_review_persistence, 3, None),
        (frame_scout_persistence, 3, None),
        (rolling_review_persistence, 8, 123),
    ],
)
def test_frame_review_families_mysql_missing_ignore_stale_json(
    monkeypatch, tmp_path, module, frame, attempt
):
    ep = tmp_path / "ep"
    if attempt is None:
        legacy = module._legacy_path(ep, frame)
    else:
        legacy = module._legacy_path(ep, frame, attempt)
    legacy.parent.mkdir(parents=True)
    module.story_json.write_json(legacy, {"frame": str(frame).zfill(2), "source": "stale-file"})
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_frame_review_repository as repo

    monkeypatch.setattr(repo.MySqlFrameReviewRepository, "get_current", lambda *_a, **_k: None)
    monkeypatch.setattr(repo.MySqlFrameReviewRepository, "list_episode", lambda *_a, **_k: [])
    if attempt is None:
        assert module.load(ep, frame) is None
    else:
        assert module.load(ep, frame, attempt) is None
    assert module.list_all(ep) == []


def test_host_request_mysql_missing_never_reads_workspace(monkeypatch, tmp_path):
    module = host_request_persistence
    ep = tmp_path / "ep"
    ep.mkdir()
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_host_request_repository as repo

    monkeypatch.setattr(repo.MySqlHostRequestRepository, "get_by_id", lambda *_a, **_k: None)
    monkeypatch.setattr(repo.MySqlHostRequestRepository, "list_by_episode", lambda *_a, **_k: [])
    monkeypatch.setattr(
        module.runtime_workspace,
        "read_candidates",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("legacy workspace fallback")),
    )
    assert module.load(ep, "stale-request") is None
    assert module.list_all(ep) == []


def test_prompt_package_mysql_missing_never_resolves_workspace(monkeypatch, tmp_path):
    module = prompt_package_persistence
    ep = tmp_path / "ep"
    ep.mkdir()
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_prompt_package_repository as repo

    monkeypatch.setattr(repo.MySqlPromptPackageRepository, "get_latest", lambda *_a, **_k: None)
    monkeypatch.setattr(
        module.runtime_workspace,
        "resolve_read_path",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("legacy workspace fallback")),
    )
    assert module.load_latest(ep, 3) is None


def test_provider_receipt_mysql_missing_ignores_stale_json(monkeypatch, tmp_path):
    module = provider_receipt_persistence
    ep = tmp_path / "ep"
    ep.mkdir()
    legacy = tmp_path / "stale-provider-receipt.json"
    legacy.write_text('{"provider":"stale-file"}', encoding="utf-8")
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_provider_receipt_repository as repo

    monkeypatch.setattr(repo.MySqlProviderReceiptRepository, "get_by_legacy_path", lambda *_a, **_k: None)
    assert module.load_by_path(ep, legacy) is None


def test_runtime_review_mysql_missing_ignores_stale_files(monkeypatch, tmp_path):
    module = runtime_review_persistence
    ep = tmp_path / "episode"
    path = ep / module.REL / "story-semantic-request.json"
    path.parent.mkdir(parents=True)
    module.story_json.write_json(path, {"review_kind": "story-semantic", "source": "stale-file"})

    class Repository:
        def get(self, *_a, **_k):
            return None

        def list_current(self, *_a, **_k):
            return []

        def list_attempts(self, *_a, **_k):
            return []

    monkeypatch.setattr(module, "_mode", lambda: "mysql")
    monkeypatch.setattr(module, "_repository", lambda _ep: (FakeConnection(), Repository()))
    monkeypatch.setattr(module.episode_identity, "storage_episode_id", lambda _ep: "EPU_authority_test")
    assert module.load_path(path) is None
    assert module.list_current(ep) == []
    assert module.list_attempts(ep, "story-semantic") == []


def test_validation_report_mysql_missing_ignores_stale_json(monkeypatch, tmp_path):
    module = validation_report_persistence
    ep = tmp_path / "ep"
    ep.mkdir()
    legacy = ep / "meta/preproduction-validation.json"
    legacy.parent.mkdir(parents=True)
    module.story_json.write_json(legacy, {"status": "stale-file"})

    class Repository:
        def get_by_id(self, *_a, **_k):
            return None

    _mysql_mode(module, monkeypatch)
    monkeypatch.setattr(module, "_repository", lambda _ep: (FakeConnection(), Repository()))
    assert module.load(ep, "preproduction", legacy_path=legacy) is None


def test_mysql_repository_failure_propagates_instead_of_falling_back(monkeypatch, tmp_path):
    module = frame_review_persistence
    ep = tmp_path / "ep"
    legacy = module._legacy_path(ep, 3)
    legacy.parent.mkdir(parents=True)
    module.story_json.write_json(legacy, {"frame": "03", "source": "stale-file"})
    _mysql_mode(module, monkeypatch)
    _patch_connection(monkeypatch)
    import platform.repository.mysql.mysql_frame_review_repository as repo

    def fail(*_args, **_kwargs):
        raise RuntimeError("mysql unavailable")

    monkeypatch.setattr(repo.MySqlFrameReviewRepository, "get_current", fail)
    with pytest.raises(RuntimeError, match="mysql unavailable"):
        module.load(ep, 3)
