from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import authority_commit  # noqa: E402
import preimage_execution_persistence as execution  # noqa: E402
import runtime_atomic_store as atomic  # noqa: E402


def _setup(monkeypatch, tmp_path):
    monkeypatch.setattr(execution, "mode", lambda: "json")
    ep = tmp_path
    (ep / "meta").mkdir(parents=True, exist_ok=True)
    path = ep / "meta/story-gates.json"
    atomic.atomic_write_json(path, {"story": {"locked": True}, "visual": {}})
    return ep, path, authority_commit.sha(path)


def _ctx(ep, snapshot="snap-1", task="task-character", execution_id="exec-1", attempt=1):
    idem = f"idem-{task}-{attempt}"
    execution.begin_execution(
        ep,
        snapshot_id=snapshot,
        task_id=task,
        execution_id=execution_id,
        attempt=attempt,
        idempotency_key=idem,
    )
    execution.mark_candidate_ready(
        ep, snapshot_id=snapshot, task_id=task, execution_id=execution_id
    )
    return {
        "task_id": task,
        "execution_id": execution_id,
        "attempt": attempt,
        "idempotency_key": idem,
    }


def _commit(ep, expected, ctx, payload=None):
    return authority_commit.commit_transaction(
        ep,
        "meta/story-gates.json",
        expected_sha=expected,
        snapshot_id="snap-1",
        task_ids=[ctx["task_id"]],
        node_ids=["PREIMAGE_CHARACTER_FINALIZE"],
        patches=[("visual.character", payload or {"identity": "locked"})],
        candidate_paths=["meta/runtime/preimage-candidates/character.json"],
        execution_contexts=[ctx],
    )


def test_same_idempotency_after_candidate_ready_reuses_original_execution(monkeypatch, tmp_path):
    ep, _path, _expected = _setup(monkeypatch, tmp_path)
    first = _ctx(ep, execution_id="exec-1", attempt=1)
    resumed = execution.begin_execution(
        ep,
        snapshot_id="snap-1",
        task_id=first["task_id"],
        execution_id="exec-after-crash",
        attempt=1,
        idempotency_key=first["idempotency_key"],
    )
    assert resumed["execution_id"] == "exec-1"
    assert resumed["status"] == "CANDIDATE_READY"
    rows = [row for row in execution.load_records(ep, "snap-1") if row.get("task_id") == first["task_id"]]
    assert len(rows) == 1


def test_successful_commit_replays_without_second_mutation(monkeypatch, tmp_path):
    ep, path, expected = _setup(monkeypatch, tmp_path)
    ctx = _ctx(ep)
    first = _commit(ep, expected, ctx)
    first_bytes = path.read_bytes()
    second = _commit(ep, expected, ctx)
    assert first["status"] == "PASS"
    assert second["status"] == "REPLAYED"
    assert second["committed"] is False
    assert path.read_bytes() == first_bytes


def test_prepared_receipt_recovers_after_authority_write_before_finalize(monkeypatch, tmp_path):
    ep, path, expected = _setup(monkeypatch, tmp_path)
    ctx = _ctx(ep)
    preview = {"story": {"locked": True}, "visual": {"character": {"identity": "locked"}}}
    planned = authority_commit.sha_json_document(preview)
    execution.prepare_commit(
        ep,
        snapshot_id="snap-1",
        task_id=ctx["task_id"],
        execution_id=ctx["execution_id"],
        attempt=ctx["attempt"],
        idempotency_key=ctx["idempotency_key"],
        input_sha=expected,
        output_sha=planned,
    )
    atomic.atomic_write_json(path, preview)
    replay = _commit(ep, expected, ctx)
    assert replay["status"] == "REPLAYED"
    record = execution.find_execution(ep, "snap-1", ctx["task_id"], ctx["execution_id"])
    assert record["status"] == "COMMITTED"
    assert record["commit_receipt"]["status"] == "COMMITTED"


def test_prepared_commit_blocks_newer_attempt_until_resolved(monkeypatch, tmp_path):
    ep, _path, expected = _setup(monkeypatch, tmp_path)
    first = _ctx(ep, execution_id="exec-1", attempt=1)
    preview = {"story": {"locked": True}, "visual": {"character": {"identity": "locked"}}}
    execution.prepare_commit(
        ep,
        snapshot_id="snap-1",
        task_id=first["task_id"],
        execution_id=first["execution_id"],
        attempt=first["attempt"],
        idempotency_key=first["idempotency_key"],
        input_sha=expected,
        output_sha=authority_commit.sha_json_document(preview),
    )
    newer = execution.begin_execution(
        ep,
        snapshot_id="snap-1",
        task_id=first["task_id"],
        execution_id="exec-2",
        attempt=2,
        idempotency_key="idem-task-character-2",
    )
    assert newer["status"] == "COMMIT_IN_PROGRESS"
    record = execution.find_execution(ep, "snap-1", first["task_id"], first["execution_id"])
    assert record["status"] == "PREPARED"
    assert record["eligible"] is True


def test_new_attempt_supersedes_old_attempt(monkeypatch, tmp_path):
    ep, _path, expected = _setup(monkeypatch, tmp_path)
    old = _ctx(ep, execution_id="exec-1", attempt=1)
    new = _ctx(ep, execution_id="exec-2", attempt=2)
    old_result = _commit(ep, expected, old)
    assert old_result["status"] == "INELIGIBLE"
    new_result = _commit(ep, expected, new)
    assert new_result["status"] == "PASS"


def test_duplicate_dispatch_same_attempt_cannot_commit(monkeypatch, tmp_path):
    ep, _path, expected = _setup(monkeypatch, tmp_path)
    first = _ctx(ep, execution_id="exec-1", attempt=1)
    duplicate = execution.begin_execution(
        ep,
        snapshot_id="snap-1",
        task_id="task-character",
        execution_id="exec-duplicate",
        attempt=1,
        idempotency_key=first["idempotency_key"],
    )
    assert duplicate["execution_id"] == "exec-1"
    bad = dict(first)
    bad["execution_id"] = "exec-duplicate"
    result = _commit(ep, expected, bad)
    assert result["status"] == "INELIGIBLE"


def test_shadow_and_live_attempt_one_use_separate_execution_domains(monkeypatch, tmp_path):
    ep, _path, _expected = _setup(monkeypatch, tmp_path)
    live = execution.begin_execution(
        ep, snapshot_id="snap-1", task_id="task-character", execution_id="exec-live",
        attempt=1, idempotency_key="idem-live", shadow=False,
    )
    shadow = execution.begin_execution(
        ep, snapshot_id="snap-1", task_id="task-character", execution_id="exec-shadow-domain",
        attempt=1, idempotency_key="idem-shadow-domain", shadow=True,
    )
    assert live["status"] == "ACTIVE"
    assert shadow["status"] == "ACTIVE"
    assert live["execution_id"] != shadow["execution_id"]


def test_shadow_execution_is_never_commit_eligible(monkeypatch, tmp_path):
    ep, _path, expected = _setup(monkeypatch, tmp_path)
    execution.begin_execution(
        ep,
        snapshot_id="snap-1",
        task_id="task-shadow",
        execution_id="exec-shadow",
        attempt=1,
        idempotency_key="idem-shadow",
        shadow=True,
    )
    ctx = {
        "task_id": "task-shadow",
        "execution_id": "exec-shadow",
        "attempt": 1,
        "idempotency_key": "idem-shadow",
    }
    result = _commit(ep, expected, ctx)
    assert result["status"] == "INELIGIBLE"
