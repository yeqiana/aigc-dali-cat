"""Phase9 Runtime Worker 存活观察者（P9.30）的离线回归测试。

真实 Redis 版由操作者手跑：

    python scripts/phase9_liveness_watchdog.py --register <worker_id> --rounds 3

这里用注入的假 Redis / 假时钟完整走判定与事件生命周期（不碰真实依赖），锁住五件事：
1. 心跳键命名空间往返（heartbeat_key / worker_id_from_key）；
2. evaluate_liveness 口径：全在线 -> ONLINE 无告警；expected 超出 observed -> 每个失联一条 CRITICAL；
   SCAN 到键但读不到心跳 -> 仍算失联；坏时间戳不猜；
3. 名册 read-modify-write 加锁不丢 Worker；
4. 事件生命周期：失联开 OPEN -> 恢复置 RESOLVED（跨运行持久化）；
5. 退出码契约（0/2/3）与证据绝不含凭据。
"""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from platform.core.clock import utc_now  # noqa: E402
from platform.operations.runtime_worker_liveness import (  # noqa: E402
    DEFAULT_PREFIX,
    LIVENESS_LEVEL,
    LIVENESS_LOST_REASON,
    STATUS_MISSING,
    STATUS_ONLINE,
    evaluate_liveness,
    heartbeat_key,
    seconds_since,
    worker_id_from_key,
)

from scripts import phase9_liveness_watchdog as liveness_module  # noqa: E402
from scripts.phase9_liveness_watchdog import (  # noqa: E402
    EXIT_ALERTING,
    EXIT_ENV_ERROR,
    EXIT_OK,
    _env_summary,
    exit_code,
    load_roster,
    main,
    register_workers,
    run_watchdog,
)


class FakeRedis:
    """内存 Redis：只实现观察者真正用到的 set / get / delete / scan_iter / ping。"""

    def __init__(self, *, fail_scan: bool = False) -> None:
        self.store: dict = {}
        self.fail_scan = fail_scan
        self.closed = False

    def set(self, key, value, ex=None, nx=False):
        self.store[key] = value
        return True

    def get(self, key):
        return self.store.get(key)

    def delete(self, key):
        self.store.pop(key, None)

    def scan_iter(self, match=None):
        if self.fail_scan:
            raise ConnectionError("scan unavailable")
        for key in list(self.store):
            if match is None or fnmatch.fnmatchcase(key, match):
                yield key

    def ping(self):
        return True

    def close(self):
        self.closed = True


class FakeAdapter:
    """替代 RedisConnection：直接返回给定的假客户端。"""

    def __init__(self, client):
        self.client = client

    def ping(self):
        return True


def _paths(tmp_path: Path) -> dict:
    return {
        "roster_path": tmp_path / "roster.json",
        "incident_path": tmp_path / "incidents.json",
        "alert_log": tmp_path / "alerts.jsonl",
        "metrics_file": tmp_path / "metrics.prom",
    }


def _beat(client: FakeRedis, worker_id: str, *, heartbeat_time: str | None = None) -> None:
    payload = {
        "worker_id": worker_id,
        "status": "ONLINE",
        "heartbeat_time": heartbeat_time or utc_now().isoformat(),
    }
    client.store[heartbeat_key(worker_id)] = json.dumps(payload)


def _run(tmp_path: Path, client: FakeRedis, **overrides) -> dict:
    kwargs = dict(_paths(tmp_path))
    kwargs.setdefault("rounds", 1)
    kwargs.setdefault("interval", 0.0)
    kwargs["watchdog_id"] = "wd-unit"
    kwargs.update(overrides)
    return run_watchdog(client=client, **kwargs)


# ---- 判定口径 ----

def test_heartbeat_key_roundtrip_and_namespace():
    key = heartbeat_key("worker-1")
    assert key == "storyos:worker:worker-1:heartbeat"
    assert key.startswith(DEFAULT_PREFIX)
    assert worker_id_from_key(key) == "worker-1"


def test_worker_id_from_key_rejects_non_heartbeat_and_empty():
    assert worker_id_from_key("storyos:worker:") is None
    assert worker_id_from_key("storyos:worker::heartbeat") is None
    assert worker_id_from_key("other:key") is None
    assert worker_id_from_key("storyos:worker:worker-1:lock") is None
    assert worker_id_from_key("storyos:worker:worker-1:heartbeat", "custom:") is None


def test_seconds_since_handles_bad_and_missing():
    now = utc_now()
    assert seconds_since(None, now) is None
    assert seconds_since("", now) is None
    assert seconds_since("not-a-timestamp", now) is None
    assert seconds_since(now.isoformat(), now) == 0.0


def _records_index(result):
    return {record["worker_id"]: record for record in result["records"]}


def test_evaluate_liveness_all_online_is_quiet():
    now = utc_now()
    seen = {"status": "ONLINE", "heartbeat_time": now.isoformat()}
    result = evaluate_liveness(
        expected=["worker-1", "worker-2"],
        observed=["worker-1", "worker-2"],
        read_heartbeat=lambda worker_id: dict(seen),
        now=now,
    )
    assert result["status"] == STATUS_ONLINE
    assert result["missing"] == []
    assert result["alerts"] == []
    records = _records_index(result)
    assert records["worker-1"]["status"] == STATUS_ONLINE
    assert records["worker-1"]["seconds_since_heartbeat"] == 0.0


def test_evaluate_liveness_missing_produces_one_critical_each():
    now = utc_now()
    online = {"status": "ONLINE", "heartbeat_time": now.isoformat()}
    result = evaluate_liveness(
        expected=["worker-1", "worker-2", "worker-3"],
        observed=["worker-1"],
        read_heartbeat=lambda worker_id: dict(online) if worker_id == "worker-1" else None,
        now=now,
    )
    assert result["status"] == STATUS_MISSING
    assert result["missing"] == ["worker-2", "worker-3"]
    assert len(result["alerts"]) == 2
    for alert in result["alerts"]:
        assert alert["level"] == LIVENESS_LEVEL == "CRITICAL"
        assert alert["reason"] == LIVENESS_LOST_REASON
        assert alert["source"] == "liveness_watchdog"
    assert {alert["worker_id"] for alert in result["alerts"]} == {"worker-2", "worker-3"}
    assert _records_index(result)["worker-2"]["status"] == STATUS_MISSING


def test_evaluate_liveness_scan_seen_but_unreadable_is_missing():
    """SCAN 到键但心跳读不到，同样算失联（以真实读取为准）。"""
    now = utc_now()
    result = evaluate_liveness(
        expected=["ghost"],
        observed=["ghost"],
        read_heartbeat=lambda worker_id: None,
        now=now,
    )
    assert result["observed"] == ["ghost"]
    assert result["missing"] == ["ghost"]
    assert result["status"] == STATUS_MISSING


# ---- 名册 ----

def test_register_workers_merges_and_releases_lock(tmp_path):
    roster = tmp_path / "roster.json"
    register_workers(roster, ["worker-1"])
    register_workers(roster, ["worker-2"])
    assert load_roster(roster) == ["worker-1", "worker-2"]
    assert not (tmp_path / "roster.json.lock").exists()
    document = json.loads(roster.read_text(encoding="utf-8"))
    assert {item["worker_id"] for item in document["workers"]} == {"worker-1", "worker-2"}
    assert all(item.get("registered_at") for item in document["workers"])


# ---- 观察者 ----

def test_watchdog_online_round_is_quiet(tmp_path):
    client = FakeRedis()
    register_workers(tmp_path / "roster.json", ["worker-1"])
    _beat(client, "worker-1")
    result = _run(tmp_path, client)
    summary = result["summary"]
    assert summary["status"] == STATUS_ONLINE
    assert summary["missing"] == []
    assert summary["open_incidents"] == []
    assert exit_code(summary) == EXIT_OK
    assert not (tmp_path / "alerts.jsonl").exists()


def test_watchdog_missing_round_alerts_and_opens_incident(tmp_path):
    client = FakeRedis()
    register_workers(tmp_path / "roster.json", ["worker-1"])
    result = _run(tmp_path, client, rounds=2)
    summary = result["summary"]
    assert summary["status"] == STATUS_MISSING
    assert summary["missing"] == ["worker-1"]
    assert summary["alert_counts"]["CRITICAL"] == 2
    assert len(summary["open_incidents"]) == 1
    incident = summary["open_incidents"][0]
    assert incident["status"] == "OPEN"
    assert incident["alert_level"] == "CRITICAL"
    assert incident["reason"] == LIVENESS_LOST_REASON
    assert incident["occurrences"] == 2
    assert exit_code(summary) == EXIT_ALERTING

    lines = [
        json.loads(line)
        for line in (tmp_path / "alerts.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 2
    assert lines[0]["level"] == "CRITICAL"
    assert lines[0]["worker_id"] == "worker-1"
    assert lines[0]["source"] == "liveness_watchdog"
    assert lines[0]["incident_id"]

    metrics = (tmp_path / "metrics.prom").read_text(encoding="utf-8")
    assert 'storyos_runtime_worker_liveness_missing{watchdog_id="wd-unit"} 1' in metrics
    assert 'storyos_runtime_worker_liveness_state{watchdog_id="wd-unit",status="MISSING"} 1' in metrics
    assert 'storyos_runtime_worker_liveness_rounds_total{watchdog_id="wd-unit"} 2' in metrics


def test_watchdog_recovery_resolves_incident_across_runs(tmp_path):
    client = FakeRedis()
    paths = _paths(tmp_path)
    register_workers(paths["roster_path"], ["worker-1"])

    first = _run(tmp_path, client)
    assert first["summary"]["missing"] == ["worker-1"]
    assert len(first["summary"]["open_incidents"]) == 1

    _beat(client, "worker-1")
    second = run_watchdog(
        client=client, watchdog_id="wd-unit", rounds=1, interval=0.0, **paths
    )
    summary = second["summary"]
    assert summary["missing"] == []
    assert summary["open_incidents"] == []
    assert len(summary["resolved_incidents"]) == 1
    assert summary["resolved_incidents"][0]["status"] == "RESOLVED"
    assert summary["resolved_incidents"][0]["worker_id"] == "worker-1"
    assert exit_code(summary) == EXIT_OK


def test_watchdog_scanned_but_unreadable_heartbeat_is_reported_missing(tmp_path):
    client = FakeRedis()
    register_workers(tmp_path / "roster.json", ["ghost"])
    client.store[heartbeat_key("ghost")] = None
    result = _run(tmp_path, client)
    summary = result["summary"]
    assert summary["observed"] == ["ghost"]
    assert summary["missing"] == ["ghost"]
    assert exit_code(summary) == EXIT_ALERTING


def test_rounds_advance_and_sleep_between_rounds(tmp_path):
    client = FakeRedis()
    register_workers(tmp_path / "roster.json", ["worker-1"])
    _beat(client, "worker-1")
    slept = []
    result = _run(tmp_path, client, rounds=3, interval=5.0, sleep=lambda seconds: slept.append(seconds))
    assert result["summary"]["rounds"] == 3
    assert slept == [5.0, 5.0]


def test_empty_roster_is_online_not_alerting(tmp_path):
    client = FakeRedis()
    result = _run(tmp_path, client)
    summary = result["summary"]
    assert summary["status"] == STATUS_ONLINE
    assert summary["missing"] == []
    assert exit_code(summary) == EXIT_OK


def test_exit_code_contract():
    assert exit_code({"missing": []}) == EXIT_OK
    assert exit_code({"missing": ["worker-1"]}) == EXIT_ALERTING
    assert exit_code({"missing": [], "open_incidents": [{"status": "OPEN"}]}) == EXIT_ALERTING
    assert exit_code({}) == EXIT_OK


def test_env_summary_hides_password_but_reports_presence(monkeypatch):
    secret = "super-secret-watchdog-password"
    monkeypatch.setenv("STORYOS_REDIS_PASSWORD", secret)
    monkeypatch.setenv("STORYOS_REDIS_HOST", "10.0.0.9")
    summary = _env_summary()
    assert summary["redis"]["host"] == "10.0.0.9"
    assert summary["redis"]["password_present"] is True
    assert secret not in json.dumps(summary, ensure_ascii=False)


def test_main_writes_evidence_without_credentials(tmp_path, monkeypatch):
    secret = "super-secret-watchdog-password"
    monkeypatch.setenv("STORYOS_REDIS_PASSWORD", secret)
    client = FakeRedis()
    monkeypatch.setattr(liveness_module, "RedisConnection", lambda: FakeAdapter(client))
    paths = _paths(tmp_path)
    evidence_file = tmp_path / "evidence.json"
    code = main([
        "--roster", str(paths["roster_path"]),
        "--incident-state", str(paths["incident_path"]),
        "--alert-log", str(paths["alert_log"]),
        "--metrics-file", str(paths["metrics_file"]),
        "--evidence-file", str(evidence_file),
        "--register", "worker-1",
        "--quiet",
    ])
    assert code == EXIT_ALERTING
    evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    blob = json.dumps(evidence, ensure_ascii=False)
    assert secret not in blob
    assert evidence["environment"]["redis"]["password_present"] is True
    assert evidence["summary"]["missing"] == ["worker-1"]
    assert load_roster(paths["roster_path"]) == ["worker-1"]


def test_main_returns_env_error_when_redis_unavailable(monkeypatch):
    def boom():
        raise ConnectionError("redis down")

    monkeypatch.setattr(liveness_module, "RedisConnection", boom)
    assert main(["--quiet"]) == EXIT_ENV_ERROR


def test_scan_failure_is_environment_error(tmp_path):
    client = FakeRedis(fail_scan=True)
    register_workers(tmp_path / "roster.json", ["worker-1"])
    with pytest.raises(liveness_module.LivenessEnvironmentError):
        _run(tmp_path, client)
