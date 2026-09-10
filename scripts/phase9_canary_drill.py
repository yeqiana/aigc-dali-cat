"""Story OS V3 Phase9 真实 Canary 演练（P9.29）。

阶段定位：
    reports/phase9_runtime_canary_simulation_report.md 此前停在「真实 Canary Traffic: Pending」，
    阻塞原因是「需要 Runtime Staging 环境、真实 Worker 与流量入口」。P9.28 交付常驻 Runtime
    Worker 载体后，本文件把灰度切换链路真正驱动一遍，并产出生产切换决策证据。

链路（全部调用既有公开 API，不复制判定逻辑）：
    CanaryRuntimeGateway 路由
        -> CanaryObservabilityMetrics 采集
        -> CanarySoakWindow 观察窗
        -> CanaryPromotionGate 晋级门禁 / CanaryProgressiveRollout 渐进推进
        -> CanaryRollbackController(P8.5) 与 CanaryProgressiveRolloutController(P8.6) 回滚
        -> CanaryProductionSwitchDecision 生产切换决策

真与不真的边界（报告里同样写明）：
    - 真实：分流走真实 sha256 bucket 代码；每个阶段用真实只读探针（Redis ping + MySQL
      SELECT 1）测量真实延迟与真实成败；故障注入用一个被拒绝的本地端口，产生真实驱动异常。
    - 仿真：请求流是确定性生成的粘性 key，不是真实用户流量；平台当前没有生产流量入口。
    - 只读：探针不写业务数据，不产生 event / trace / artifact 行。
    - 不切换生产：本文件只产出决策证据，不做 V2 -> V3 的归属切换。

退出码：
    0 = 全部断言通过
    2 = 有断言失败（观察到与预期不符的真实行为）
    3 = 参数或环境错误
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_STAGES = (1, 10, 50, 100)
DEFAULT_REQUESTS_PER_STAGE = 1000
DEFAULT_SAMPLES_PER_STAGE = 120
DEFAULT_EPISODE_ID = "drill_canary_episode"
DEFAULT_RUNTIME = "V3_RUNTIME"
DEFAULT_EVIDENCE_FILE = PROJECT_ROOT / ".storyos" / "drill" / "canary-drill-evidence.json"

REQUEST_KEY_PREFIX = "drill-req"
DISTRIBUTION_TOLERANCE_PERCENT = 2.0

# 被拒绝的本地端口：连接立即失败，用来做真实且快速的依赖故障注入。
REFUSED_MYSQL_HOST = "127.0.0.1"
REFUSED_MYSQL_PORT = 1

EXIT_OK = 0
EXIT_FINDING = 2
EXIT_ENV_ERROR = 3


def _bootstrap_story_platform() -> None:
    """把 import platform 指向仓库内 platform 包，而不是 stdlib platform。"""
    target = (PROJECT_ROOT / "platform" / "__init__.py").resolve()
    existing = sys.modules.get("platform")
    existing_file = getattr(existing, "__file__", None)
    if existing_file:
        try:
            if Path(existing_file).resolve() == target:
                return
        except OSError:
            pass

    root = str(PROJECT_ROOT)
    while root in sys.path:
        sys.path.remove(root)
    sys.path.insert(0, root)

    spec = importlib.util.spec_from_file_location(
        "platform",
        target,
        submodule_search_locations=[str(target.parent)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Story OS platform package from " + str(target))
    module = importlib.util.module_from_spec(spec)
    sys.modules["platform"] = module
    spec.loader.exec_module(module)


_bootstrap_story_platform()

from platform.core.clock import utc_now  # noqa: E402
from platform.gateway.canary_auto_rollback import (  # noqa: E402
    CanaryAutoRollbackPolicy,
    CanaryRollbackController,
    CanaryRollbackPolicy,
)
from platform.gateway.canary_observability_metrics import (  # noqa: E402
    CanaryObservabilityMetrics,
)
from platform.gateway.canary_production_switch_decision import (  # noqa: E402
    CanaryProductionSwitchDecision,
)
from platform.gateway.canary_progressive_rollout import (  # noqa: E402
    CanaryProgressiveRollout,
    CanaryProgressiveRolloutController,
    CanaryRolloutPlan,
)
from platform.gateway.canary_promotion_evidence import build_promotion_evidence  # noqa: E402
from platform.gateway.canary_promotion_gate import CanaryPromotionGate  # noqa: E402
from platform.gateway.canary_runtime_gateway import CanaryRuntimeGateway  # noqa: E402
from platform.gateway.canary_soak_window import CanarySoakWindow  # noqa: E402
from platform.repository.mysql.mysql_connection import MySqlConnection  # noqa: E402
from platform.state.redis_connection import RedisConnection  # noqa: E402


def now_iso() -> str:
    return utc_now().isoformat()


def request_keys(count: int, *, prefix: str = REQUEST_KEY_PREFIX) -> list:
    """确定性粘性 key：同一批 key 在每个阶段都落同一侧，便于验证 bucket 稳定性。"""
    return [prefix + "-" + str(index).zfill(5) for index in range(count)]


class CanaryProbe:
    """一次「canary 请求」的真实只读执行：Redis ping + MySQL SELECT 1。

    只读、不写业务数据；延迟是真实测量值，失败是真实驱动异常。
    """

    def __init__(self, *, redis_client, mysql_connection, clock=time.perf_counter) -> None:
        self.redis_client = redis_client
        self.mysql_connection = mysql_connection
        self.clock = clock

    def sample(self) -> dict:
        start = self.clock()
        try:
            self.redis_client.ping()
        except Exception as exc:  # noqa: BLE001 - 真实失败按失败记录
            return self._failure(start, "redis: " + type(exc).__name__ + ": " + str(exc))
        try:
            row = self.mysql_connection.query_one("SELECT 1 AS alive")
            if not row or row.get("alive") != 1:
                raise RuntimeError("mysql probe returned " + repr(row))
        except Exception as exc:  # noqa: BLE001 - 真实失败按失败记录
            return self._failure(start, "mysql: " + type(exc).__name__ + ": " + str(exc))
        return {"ok": True, "latency_ms": round((self.clock() - start) * 1000.0, 3), "error": None}

    def _failure(self, start, message: str) -> dict:
        return {
            "ok": False,
            "latency_ms": round((self.clock() - start) * 1000.0, 3),
            "error": message,
        }


def _env_summary() -> dict:
    def _int(name, default):
        try:
            return int(os.environ.get(name, str(default)))
        except ValueError:
            return default

    return {
        "mysql": {
            "host": os.environ.get("STORYOS_MYSQL_HOST", "127.0.0.1"),
            "port": _int("STORYOS_MYSQL_PORT", 3306),
            "database": os.environ.get("STORYOS_MYSQL_DB", "story_os_runtime"),
            "user_present": bool(os.environ.get("STORYOS_MYSQL_USER", "")),
            "password_present": bool(os.environ.get("STORYOS_MYSQL_PWD", "")),
        },
        "redis": {
            "host": os.environ.get("STORYOS_REDIS_HOST", "127.0.0.1"),
            "port": _int("STORYOS_REDIS_PORT", 6379),
            "db": _int("STORYOS_REDIS_DB", 0),
            "password_present": bool(os.environ.get("STORYOS_REDIS_PASSWORD", "")),
        },
        "failure_injection": {"mysql_host": REFUSED_MYSQL_HOST, "mysql_port": REFUSED_MYSQL_PORT},
    }


class CanaryDrill:
    """驱动真实灰度控制面，记录每个阶段的真实分流与真实探针结果。

    探针与故障探针可注入，方便离线测试；控制面对象默认用生产实现。
    """

    def __init__(
        self,
        *,
        probe,
        broken_probe=None,
        gateway=None,
        plan=None,
        gate=None,
        rollout=None,
        metrics_collector=None,
        episode_id: str = DEFAULT_EPISODE_ID,
        runtime: str = DEFAULT_RUNTIME,
        requests_per_stage: int = DEFAULT_REQUESTS_PER_STAGE,
        samples_per_stage: int = DEFAULT_SAMPLES_PER_STAGE,
        now=utc_now,
    ) -> None:
        self.probe = probe
        self.broken_probe = broken_probe
        self.gateway = gateway or CanaryRuntimeGateway(canary_enabled=False, canary_percent=0)
        self.plan = plan or CanaryRolloutPlan(
            stages=tuple(DEFAULT_STAGES), min_requests_per_stage=20
        )
        self.plan.validate()
        self.gate = gate or CanaryPromotionGate(
            min_requests=100, max_error_rate=0.05, max_latency_ms=30000
        )
        self.rollout = rollout or CanaryProgressiveRollout(
            self.plan,
            CanaryRollbackPolicy(
                max_error_rate=0.05, max_avg_latency_ms=30000, min_sample_size=5
            ),
        )
        self.rollout_controller = CanaryProgressiveRolloutController()
        self.rollback_controller = CanaryRollbackController()
        self.rollback_policy = CanaryAutoRollbackPolicy()
        self.metrics_collector = metrics_collector or CanaryObservabilityMetrics()
        self.switch_decider = CanaryProductionSwitchDecision()
        self.episode_id = episode_id
        self.runtime = runtime
        self.requests_per_stage = requests_per_stage
        self.samples_per_stage = samples_per_stage
        self.now = now
        self.current_percent = 0
        self.steps: list = []
        self.notes: list = []
        self.stage_rows: list = []
        self._v3_keys: dict = {}

    # ---- 记录 ----

    def _record(self, scenario: str, step: str, ok: bool, detail=None) -> dict:
        entry = {
            "scenario": scenario,
            "step": step,
            "ok": bool(ok),
            "at": now_iso(),
            "detail": detail if detail is not None else {},
        }
        self.steps.append(entry)
        return entry

    def _note(self, note_id: str, detail) -> dict:
        entry = {"id": note_id, "detail": detail}
        if not any(item["id"] == note_id for item in self.notes):
            self.notes.append(entry)
        return entry

    # ---- 步骤 ----

    def route_stage(self, percent: int) -> dict:
        keys = request_keys(self.requests_per_stage)
        v3_keys = []
        reasons: dict = {}
        for key in keys:
            result = self.gateway.route(self.episode_id, request_key=key)
            reasons[result.reason] = reasons.get(result.reason, 0) + 1
            if result.target == "V3_RUNTIME":
                v3_keys.append(key)
        total = len(keys)
        v3 = len(v3_keys)
        self._v3_keys[percent] = set(v3_keys)
        return {
            "percent": percent,
            "total": total,
            "v3": v3,
            "v2": total - v3,
            "v3_percent": round(100.0 * v3 / total, 2) if total else 0.0,
            "reasons": reasons,
            "v3_keys": v3_keys,
        }

    def sample_stage(self) -> tuple:
        samples = [self.probe.sample() for _ in range(self.samples_per_stage)]
        failed = [item for item in samples if not item["ok"]]
        latencies = [item["latency_ms"] for item in samples]
        payload = {
            "total_requests": len(samples),
            "success_count": len(samples) - len(failed),
            "failed_count": len(failed),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 3) if latencies else 0.0,
        }
        detail = dict(payload)
        detail["max_latency_ms"] = round(max(latencies), 3) if latencies else 0.0
        detail["sample_errors"] = [item["error"] for item in failed[:3]]
        return payload, detail

    def describe_gateway(self) -> dict:
        return {"enabled": self.gateway.canary_enabled, "percent": self.gateway.canary_percent}

    def start_rollout(self) -> dict:
        """current_percent = 0 的真实起步决策（rollout_started）。"""
        snapshot = self.metrics_collector.collect(
            self.episode_id, self.runtime, {"total_requests": 0}
        )
        decision = self.rollout.evaluate(snapshot, current_percent=0)
        applied = self.rollout_controller.apply(decision, self.gateway)
        self.current_percent = applied.percent
        return {
            "action": decision.action,
            "reasons": list(decision.reasons),
            "next_percent": decision.next_percent,
            "gateway": self.describe_gateway(),
        }

    def run_stage(self, percent: int, scenario: str) -> dict:
        distribution = self.route_stage(percent)
        payload, sample_detail = self.sample_stage()
        metrics = self.metrics_collector.collect(self.episode_id, self.runtime, payload)
        soak = CanarySoakWindow(percent).snapshot(metrics, trace_healthy=True)
        gate_index = list(self.plan.stages).index(percent)
        next_percent = (
            self.plan.stages[gate_index + 1]
            if gate_index + 1 < len(self.plan.stages)
            else self.plan.stages[-1]
        )
        gate_result = self.gate.evaluate(soak, next_percent)
        rollout_decision = self.rollout.evaluate(metrics, current_percent=percent)
        before_percent = self.gateway.canary_percent
        applied = self.rollout_controller.apply(rollout_decision, self.gateway)
        self.current_percent = applied.percent

        self._record(
            scenario,
            "stage_" + str(percent) + "_routing_distribution",
            abs(distribution["v3_percent"] - percent) <= DISTRIBUTION_TOLERANCE_PERCENT,
            {"target_percent": percent, "observed_percent": distribution["v3_percent"],
             "v3": distribution["v3"], "v2": distribution["v2"],
             "total": distribution["total"], "tolerance_percent": DISTRIBUTION_TOLERANCE_PERCENT,
             "reasons": distribution["reasons"]},
        )
        self._record(
            scenario,
            "stage_" + str(percent) + "_canary_probe_health",
            metrics.failed_count == 0 and metrics.avg_latency_ms <= 30000,
            {"metrics": sample_detail, "error_rate": metrics.error_rate,
             "avg_latency_ms": metrics.avg_latency_ms},
        )
        self._record(
            scenario,
            "stage_" + str(percent) + "_promotion_gate",
            gate_result.action == "PROMOTE",
            {"action": gate_result.action, "reasons": list(gate_result.reasons),
             "next_percent": gate_result.next_percent,
             "request_count": soak.request_count, "error_rate": soak.error_rate,
             "avg_latency_ms": soak.avg_latency_ms},
        )
        expected_rollout = "COMPLETE" if percent == self.plan.stages[-1] else "PROMOTE"
        self._record(
            scenario,
            "stage_" + str(percent) + "_progressive_rollout",
            rollout_decision.action == expected_rollout
            and before_percent == percent
            and applied.percent == rollout_decision.next_percent,
            {"action": rollout_decision.action, "reasons": list(rollout_decision.reasons),
             "expected_action": expected_rollout, "gateway_percent_before_apply": before_percent,
             "gateway_percent_after_apply": applied.percent,
             "next_percent": rollout_decision.next_percent},
        )

        row = {
            "percent": percent,
            "distribution": distribution,
            "metrics": metrics,
            "sample_detail": sample_detail,
            "soak": soak,
            "gate": gate_result,
            "rollout": rollout_decision,
        }
        self.stage_rows.append(row)
        return row

    # ---- 场景 ----

    def scenario_baseline(self) -> None:
        name = "baseline"
        distribution = self.route_stage(0)
        self._record(
            name,
            "disabled_gateway_routes_all_to_v2",
            distribution["v3"] == 0 and distribution["v2"] == distribution["total"]
            and set(distribution["reasons"]) == {"production_default"},
            {"gateway": self.describe_gateway(), "v2": distribution["v2"],
             "total": distribution["total"], "reasons": distribution["reasons"]},
        )

    def scenario_progressive_promotion(self, stages=None) -> None:
        name = "progressive_promotion"
        stages = tuple(stages or self.plan.stages)
        started = self.start_rollout()
        self._record(
            name,
            "rollout_started_from_zero",
            started["action"] == "PROMOTE" and started["gateway"]["percent"] == stages[0],
            started,
        )
        previous_keys = None
        for percent in stages:
            self.run_stage(percent, name)
            current_keys = self._v3_keys[percent]
            if previous_keys is not None:
                self._record(
                    name,
                    "stage_" + str(percent) + "_sticky_bucket_superset",
                    previous_keys.issubset(current_keys),
                    {"previous_v3": len(previous_keys), "current_v3": len(current_keys),
                     "note": "同一粘性 key 在更高百分比阶段必然仍落 V3（真实 sha256 bucket 性质）"},
                )
            previous_keys = current_keys

    def scenario_rollback(self) -> None:
        name = "rollback_drill"
        if self.broken_probe is None:
            raise ValueError("rollback drill requires a broken_probe")
        healthy = self.probe
        self.probe = self.broken_probe
        try:
            payload, sample_detail = self.sample_stage()
            metrics = self.metrics_collector.collect(self.episode_id, self.runtime, payload)
            decision = self.rollout.evaluate(metrics, current_percent=self.current_percent)
            rollback_decision = decision.rollback_decision
            p85_route = self.rollback_controller.apply(rollback_decision, self.gateway)
            applied = self.rollout_controller.apply(decision, self.gateway)
            after = self.gateway.route(self.episode_id, request_key=REQUEST_KEY_PREFIX + "-00000")
        finally:
            self.probe = healthy

        self._record(
            name,
            "real_failure_injection_measured",
            metrics.error_rate == 1.0 and metrics.failed_count == metrics.total_requests,
            {"metrics": sample_detail, "error_rate": metrics.error_rate,
             "injected": _env_summary()["failure_injection"],
             "stage_percent_at_injection": self.current_percent},
        )
        self._record(
            name,
            "rollback_policy_triggers_on_error_rate",
            decision.action == "ROLLBACK" and rollback_decision is not None
            and "error_rate_exceeded" in rollback_decision.reasons,
            {"action": decision.action, "reasons": list(decision.reasons),
             "rollback_reasons": list(rollback_decision.reasons) if rollback_decision else None,
             "next_percent": decision.next_percent},
        )
        self._record(
            name,
            "p85_rollback_controller_returns_v2_route",
            p85_route is not None and p85_route.target == "V2_RUNTIME",
            {"route": getattr(p85_route, "target", None),
             "reason": getattr(p85_route, "reason", None)},
        )
        self._record(
            name,
            "gateway_back_to_production_default",
            self.gateway.canary_enabled is False and self.gateway.canary_percent == 0
            and applied.percent == 0 and after.target == "V2_RUNTIME"
            and after.reason == "production_default",
            {"gateway": self.describe_gateway(), "applied_percent": applied.percent,
             "post_rollback_route": {"target": after.target, "reason": after.reason}},
        )
        self.current_percent = 0

    def scenario_production_switch(self) -> None:
        name = "production_switch"
        final = self.stage_rows[-1]
        if final["percent"] != self.plan.stages[-1]:
            raise ValueError("production switch requires the final stage to be completed")
        evidence = build_promotion_evidence(final["soak"], final["gate"], generated_at=self.now())
        decision = self.switch_decider.evaluate(evidence)

        mid = None
        for row in self.stage_rows:
            if row["percent"] != self.plan.stages[-1]:
                mid = row
        mid_decision = None
        if mid is not None:
            mid_evidence = build_promotion_evidence(
                mid["soak"], mid["gate"], generated_at=self.now()
            )
            mid_decision = self.switch_decider.evaluate(mid_evidence)

        self._record(
            name,
            "switch_decision_switches_to_v3",
            decision.action == "SWITCH_TO_V3" and decision.target_runtime == "V3_RUNTIME",
            {"action": decision.action, "reasons": list(decision.reasons),
             "target_runtime": decision.target_runtime,
             "stage_percent": evidence.stage_percent,
             "request_count": evidence.request_count, "error_rate": evidence.error_rate},
        )
        self._record(
            name,
            "switch_decision_guard_keeps_canary_before_100",
            mid_decision is not None and mid_decision.action == "KEEP_CANARY",
            {"checked_stage_percent": mid["percent"] if mid else None,
             "action": mid_decision.action if mid_decision else None,
             "reasons": list(mid_decision.reasons) if mid_decision else None},
        )
        self._note(
            "decision_only_no_ownership_switch",
            {"note": "CanaryProductionSwitchDecision 只给决策；V2 退役与归属切换不在本次演练范围",
             "switch_action": decision.action},
        )

    # ---- 编排 ----

    def run(self) -> dict:
        started = now_iso()
        self.scenario_baseline()
        self.scenario_progressive_promotion()
        self.scenario_rollback()
        self.stage_rows = [row for row in self.stage_rows]
        self.scenario_progressive_promotion()
        self.scenario_production_switch()
        failed = [item["step"] for item in self.steps if not item["ok"]]
        return {
            "summary": {
                "episode_id": self.episode_id,
                "runtime": self.runtime,
                "stages": list(self.plan.stages),
                "requests_per_stage": self.requests_per_stage,
                "samples_per_stage": self.samples_per_stage,
                "distribution_tolerance_percent": DISTRIBUTION_TOLERANCE_PERCENT,
                "started_at": started,
                "finished_at": now_iso(),
                "steps": len(self.steps),
                "failed_steps": failed,
                "notes": self.notes,
                "ok": not failed,
            },
            "steps": self.steps,
            "environment": _env_summary(),
        }


def exit_code(evidence: dict) -> int:
    return EXIT_OK if (evidence.get("summary") or {}).get("ok") else EXIT_FINDING


def _write_json(path, payload: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Story OS V3 Phase9 真实 Canary 演练（分流 / 晋级 / 回滚 / 切换决策）"
    )
    parser.add_argument("--episode-id", default=DEFAULT_EPISODE_ID)
    parser.add_argument("--stages", default=",".join(str(item) for item in DEFAULT_STAGES),
                        help="逗号分隔，必须严格递增且以 100 结尾")
    parser.add_argument("--requests-per-stage", type=int, default=DEFAULT_REQUESTS_PER_STAGE)
    parser.add_argument("--samples-per-stage", type=int, default=DEFAULT_SAMPLES_PER_STAGE)
    parser.add_argument("--evidence-file", default=str(DEFAULT_EVIDENCE_FILE))
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args(argv)


def _stages_from_text(text: str) -> tuple:
    stages = tuple(int(item.strip()) for item in text.split(",") if item.strip())
    CanaryRolloutPlan(stages=stages).validate()
    return stages


def build_drill(args) -> CanaryDrill:
    redis_client = RedisConnection().client
    redis_client.ping()
    mysql = MySqlConnection()
    mysql.health_check()
    broken = CanaryProbe(
        redis_client=redis_client,
        mysql_connection=MySqlConnection(
            host=REFUSED_MYSQL_HOST, port=REFUSED_MYSQL_PORT
        ),
    )
    return CanaryDrill(
        probe=CanaryProbe(redis_client=redis_client, mysql_connection=mysql),
        broken_probe=broken,
        plan=CanaryRolloutPlan(
            stages=_stages_from_text(args.stages), min_requests_per_stage=20
        ),
        episode_id=args.episode_id,
        requests_per_stage=args.requests_per_stage,
        samples_per_stage=args.samples_per_stage,
    )


def main(argv=None) -> int:
    args = _parse_args(argv)
    try:
        drill = build_drill(args)
    except Exception as exc:  # noqa: BLE001 - 环境不可用必须显式退出
        print("启动失败：" + type(exc).__name__ + ": " + str(exc))
        return EXIT_ENV_ERROR

    if not args.quiet:
        print("Story OS V3 Phase9 真实 Canary 演练")
        print("  episode_id=" + drill.episode_id + " stages="
              + ",".join(str(item) for item in drill.plan.stages))
        print("  requests_per_stage=" + str(drill.requests_per_stage)
              + " samples_per_stage=" + str(drill.samples_per_stage))

    evidence = drill.run()
    _write_json(args.evidence_file, evidence)

    summary = evidence["summary"]
    print("== 按阶段的真实分流 ==")
    for item in evidence["steps"]:
        if item["step"].endswith("_routing_distribution"):
            detail = item["detail"]
            print("  target=" + str(detail["target_percent"]) + "% -> observed="
                  + str(detail["observed_percent"]) + "% (v3=" + str(detail["v3"])
                  + " v2=" + str(detail["v2"]) + ")")
    print("== 汇总 ==")
    print("  steps=" + str(summary["steps"]) + " failed=" + str(len(summary["failed_steps"])))
    if summary["failed_steps"]:
        print("  失败步骤=" + ",".join(summary["failed_steps"]))
    for note in summary["notes"]:
        print("  note " + note["id"])
    print("  evidence=" + str(args.evidence_file))
    code = exit_code(evidence)
    print("  退出码=" + str(code) + "（0=全部通过 2=有断言失败 3=环境错误）")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
