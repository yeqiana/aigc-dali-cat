"""Phase9 真实 Canary 演练（scripts/phase9_canary_drill.py）的离线回归测试。

真实 Redis / MySQL 版由操作者手跑：

    python scripts/phase9_canary_drill.py

这里只走注入路径，但仍调用真实灰度控制面（gateway / metrics / soak /
promotion gate / progressive rollout / rollback / switch decision），锁住六件事：
1. 健康探针下全量演练（baseline / 晋级 / 回滚 / 二次晋级 / 切换决策）必须全绿；
2. 分流比例来自真实 sha256 bucket，且粘性 key 在更高阶段是超集；
3. 观察窗样本不足时 Promotion Gate 必须 HOLD，不能假装通过；
4. 探针真实失败必须触发 ROLLBACK 并把网关拉回 production_default；
5. 刻意错误的网关必须让断言失败（退出码 2），证明断言不是摆设；
6. 证据 JSON 契约（0/2/3、不含凭据）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import phase9_canary_drill as drill_module  # noqa: E402
from scripts.phase9_canary_drill import (  # noqa: E402
    EXIT_ENV_ERROR,
    EXIT_FINDING,
    EXIT_OK,
    CanaryDrill,
    CanaryProbe,
    exit_code,
    main,
    request_keys,
)


class FakeProbe:
    """可控探针：全成功或全失败，用来驱动健康 / 回滚分支。"""

    def __init__(self, *, ok: bool = True, latency_ms: float = 5.0) -> None:
        self.ok = ok
        self.latency_ms = latency_ms
        self.calls = 0

    def sample(self) -> dict:
        self.calls += 1
        return {
            "ok": self.ok,
            "latency_ms": self.latency_ms,
            "error": None if self.ok else "injected: dependency refused",
        }


class _Route:
    def __init__(self, target: str, reason: str) -> None:
        self.target = target
        self.reason = reason


class AlwaysV3Gateway:
    """故意错误的网关：任何 percent 都把所有 key 路由到 V3。"""

    def __init__(self) -> None:
        self.canary_enabled = False
        self.canary_percent = 0

    def configure(self, *, enabled: bool, percent: int) -> None:
        self.canary_enabled = enabled
        self.canary_percent = percent

    def route(self, episode_id: str, request_key: str | None = None) -> _Route:
        return _Route("V3_RUNTIME", "canary_bucket_match")


class FakeRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def ping(self):
        if self.fail:
            raise ConnectionError("redis unavailable")
        return True


class FakeMySql:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def query_one(self, sql, params=None):
        if self.fail:
            raise RuntimeError("mysql unavailable")
        return {"alive": 1}


class TickClock:
    """每次调用前进固定量的假时钟，用来验证真实测得的延迟。"""

    def __init__(self, step: float = 0.5) -> None:
        self.t = 0.0
        self.step = step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


def make_drill(**kwargs) -> CanaryDrill:
    settings = dict(
        probe=FakeProbe(),
        broken_probe=FakeProbe(ok=False),
        requests_per_stage=1000,
        samples_per_stage=120,
    )
    settings.update(kwargs)
    return CanaryDrill(**settings)


def test_healthy_run_passes_every_step():
    evidence = make_drill().run()
    summary = evidence["summary"]
    assert summary["ok"] is True
    assert summary["failed_steps"] == []
    assert exit_code(evidence) == EXIT_OK
    steps = {item["step"] for item in evidence["steps"]}
    assert "disabled_gateway_routes_all_to_v2" in steps
    assert "rollout_started_from_zero" in steps
    assert "switch_decision_switches_to_v3" in steps
    assert "switch_decision_guard_keeps_canary_before_100" in steps


def test_routing_distribution_tracks_gateway_percent():
    evidence = make_drill().run()
    rows = [
        item for item in evidence["steps"]
        if item["step"].endswith("_routing_distribution")
    ]
    assert len(rows) == 8  # 4 个阶段 x 2 轮晋级
    observed = {}
    for item in rows:
        detail = item["detail"]
        assert item["ok"] is True
        assert abs(detail["observed_percent"] - detail["target_percent"]) <= 2.0
        observed[detail["target_percent"]] = detail["observed_percent"]
    assert observed[100] == 100.0


def test_baseline_routes_all_traffic_to_v2_when_disabled():
    drill = make_drill()
    drill.scenario_baseline()
    step = drill.steps[0]
    assert step["step"] == "disabled_gateway_routes_all_to_v2"
    assert step["ok"] is True
    assert step["detail"]["v2"] == step["detail"]["total"]
    assert set(step["detail"]["reasons"]) == {"production_default"}


def test_sticky_bucket_keys_are_supersets_across_stages():
    drill = make_drill()
    drill.run()
    stages = list(drill.plan.stages)
    for previous, current in zip(stages, stages[1:]):
        assert drill._v3_keys[previous].issubset(drill._v3_keys[current])
    supersets = [
        item for item in drill.steps if item["step"].endswith("_sticky_bucket_superset")
    ]
    assert supersets and all(item["ok"] for item in supersets)


def test_broken_probe_triggers_rollback_and_restores_v2_default():
    evidence = make_drill().run()
    rollback = {
        item["step"]: item for item in evidence["steps"]
        if item["scenario"] == "rollback_drill"
    }
    assert rollback["real_failure_injection_measured"]["ok"] is True
    assert rollback["real_failure_injection_measured"]["detail"]["error_rate"] == 1.0
    assert rollback["rollback_policy_triggers_on_error_rate"]["detail"]["action"] == "ROLLBACK"
    assert rollback["p85_rollback_controller_returns_v2_route"]["detail"]["route"] == "V2_RUNTIME"
    assert rollback["gateway_back_to_production_default"]["ok"] is True
    assert rollback["gateway_back_to_production_default"]["detail"]["applied_percent"] == 0


def test_rollback_requires_broken_probe():
    drill = make_drill(broken_probe=None)
    with pytest.raises(ValueError):
        drill.scenario_rollback()


def test_production_switch_decision_and_pre_100_guard():
    evidence = make_drill().run()
    rows = {
        item["step"]: item for item in evidence["steps"]
        if item["scenario"] == "production_switch"
    }
    switch = rows["switch_decision_switches_to_v3"]["detail"]
    assert switch["action"] == "SWITCH_TO_V3"
    assert switch["target_runtime"] == "V3_RUNTIME"
    guard = rows["switch_decision_guard_keeps_canary_before_100"]["detail"]
    assert guard["action"] == "KEEP_CANARY"
    assert guard["checked_stage_percent"] == 50


def test_insufficient_soak_sample_holds_promotion():
    evidence = make_drill(samples_per_stage=50).run()
    summary = evidence["summary"]
    assert summary["ok"] is False
    assert any(step.endswith("_promotion_gate") for step in summary["failed_steps"])
    assert exit_code(evidence) == EXIT_FINDING


def test_wrong_gateway_is_caught_by_assertions():
    evidence = make_drill(gateway=AlwaysV3Gateway()).run()
    summary = evidence["summary"]
    assert summary["ok"] is False
    assert "disabled_gateway_routes_all_to_v2" in summary["failed_steps"]
    assert exit_code(evidence) == EXIT_FINDING


def test_exit_code_contract():
    assert exit_code({"summary": {"ok": True}}) == EXIT_OK
    assert exit_code({"summary": {"ok": False}}) == EXIT_FINDING
    assert exit_code({}) == EXIT_FINDING


def test_evidence_never_contains_credentials(monkeypatch):
    secret = "super-secret-canary-password"
    monkeypatch.setenv("STORYOS_MYSQL_PWD", secret)
    monkeypatch.setenv("STORYOS_MYSQL_USER", "root")
    monkeypatch.setenv("STORYOS_REDIS_PASSWORD", secret)
    evidence = make_drill().run()
    blob = json.dumps(evidence, ensure_ascii=False)
    assert secret not in blob
    assert evidence["environment"]["mysql"]["password_present"] is True
    assert evidence["environment"]["redis"]["password_present"] is True


def test_main_returns_env_error_when_environment_unavailable(monkeypatch, tmp_path):
    def boom(_args):
        raise RuntimeError("no redis / mysql")

    monkeypatch.setattr(drill_module, "build_drill", boom)
    evidence_file = tmp_path / "canary-evidence.json"
    code = main(["--quiet", "--evidence-file", str(evidence_file)])
    assert code == EXIT_ENV_ERROR
    assert not evidence_file.exists()


def test_stage_parser_rejects_non_increasing_stages():
    assert drill_module._stages_from_text("1,10,50,100") == (1, 10, 50, 100)
    with pytest.raises(ValueError):
        drill_module._stages_from_text("10,5,100")
    with pytest.raises(ValueError):
        drill_module._stages_from_text("1,10,50")


def test_request_keys_are_deterministic_and_unique():
    first = request_keys(50)
    assert first == request_keys(50)
    assert len(set(first)) == 50


def test_canary_probe_measures_latency_and_reports_real_failure():
    good = CanaryProbe(
        redis_client=FakeRedis(), mysql_connection=FakeMySql(), clock=TickClock()
    ).sample()
    assert good["ok"] is True
    assert good["error"] is None
    assert good["latency_ms"] >= 0

    bad_redis = CanaryProbe(
        redis_client=FakeRedis(fail=True), mysql_connection=FakeMySql(), clock=TickClock()
    ).sample()
    assert bad_redis["ok"] is False
    assert "redis" in bad_redis["error"]

    bad_mysql = CanaryProbe(
        redis_client=FakeRedis(), mysql_connection=FakeMySql(fail=True), clock=TickClock()
    ).sample()
    assert bad_mysql["ok"] is False
    assert "mysql" in bad_mysql["error"]
