"""Phase9 常驻 Runtime 编排入口（P9.34）的离线回归测试。

不碰真实 Redis / MySQL / 子进程，锁住编排语义：
1. build_children 构造 Worker 与 Metrics 端点两个子进程，并共享同一 metrics 文件；
2. start / stop 通过注入 spawn 完成启动与统一优雅退出；
3. run 在子进程提前退出时 fail-fast（exited_early 非空）；
4. run 在正常 max-seconds 到期时优雅返回（exited_early 为空）。
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase9_runtime_launcher import (  # noqa: E402
    ChildSpec,
    RuntimeLauncher,
    build_children,
    load_runtime_env_file,
)


class FakeProc:
    def __init__(self, pid, exited=False):
        self.pid = pid
        self._exited = exited
        self._terminated = False
        self._killed = False
        self.returncode = None

    def poll(self):
        if self._exited:
            if self.returncode is None:
                self.returncode = 1
            return self.returncode
        return None

    def terminate(self):
        self._terminated = True
        self._exited = True
        if self.returncode is None:
            self.returncode = 0

    def kill(self):
        self._killed = True
        self._exited = True
        if self.returncode is None:
            self.returncode = -9

    def wait(self, timeout=None):
        if not self._exited:
            self._exited = True
            if self.returncode is None:
                self.returncode = 0
        return self.returncode


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        value = self.t
        self.t += 1.0
        return value


def _spawn_from(registry, early=None):
    def spawn(spec, env):
        pid = len(registry) + 1
        proc = FakeProc(pid, exited=(early is not None and spec.name == early))
        registry[spec.name] = proc
        return proc

    return spawn


def test_runtime_env_file_loads_only_allowed_storyos_keys(tmp_path):
    path = tmp_path / "runtime.env"
    path.write_text(
        "STORYOS_MYSQL_HOST=db.internal\n"
        "STORYOS_MYSQL_PORT=9000\n"
        "STORYOS_MYSQL_PWD=secret\n",
        encoding="utf-8",
    )
    env, keys = load_runtime_env_file(path, {"KEEP": "1"})

    assert env["KEEP"] == "1"
    assert env["STORYOS_MYSQL_HOST"] == "db.internal"
    assert env["STORYOS_MYSQL_PWD"] == "secret"
    assert keys == ("STORYOS_MYSQL_HOST", "STORYOS_MYSQL_PORT", "STORYOS_MYSQL_PWD")


def test_runtime_env_file_rejects_unknown_keys(tmp_path):
    path = tmp_path / "runtime.env"
    path.write_text("NOT_ALLOWED=value\n", encoding="utf-8")

    try:
        load_runtime_env_file(path, {})
    except ValueError as exc:
        assert "unsupported runtime env key" in str(exc)
    else:
        raise AssertionError("unknown key must be rejected")


def test_build_children_shares_metrics_file(tmp_path):
    children = build_children(
        run_root=tmp_path,
        worker_id="w1",
        interval=5,
        consistency_every=3,
        stuck_minutes=10,
        jsonl_root=str(tmp_path / "data"),
    )
    assert [c.name for c in children] == ["worker", "metrics-exporter"]
    worker_cmd = children[0].cmd
    exporter_cmd = children[1].cmd
    assert "--worker-id" in worker_cmd and "w1" in worker_cmd
    assert "--interval" in worker_cmd and "5" in worker_cmd
    assert "--consistency-every" in worker_cmd and "3" in worker_cmd
    metrics_file = str(tmp_path / "worker-metrics.prom")
    assert metrics_file in worker_cmd
    assert metrics_file in exporter_cmd
    assert "--port" in exporter_cmd


def test_build_children_alert_webhook_optional(tmp_path):
    base = dict(
        run_root=tmp_path,
        worker_id="w",
        interval=1,
        consistency_every=1,
        stuck_minutes=1,
        jsonl_root="d",
    )
    with_hook = build_children(alert_webhook="http://x/hook", alert_webhook_format="dingtalk", **base)
    assert "--alert-webhook" in with_hook[0].cmd
    assert "http://x/hook" in with_hook[0].cmd
    assert "--alert-webhook-format" in with_hook[0].cmd
    assert "dingtalk" in with_hook[0].cmd

    without_hook = build_children(**base)
    assert "--alert-webhook" not in without_hook[0].cmd


def test_launcher_start_and_stop():
    registry = {}
    launcher = RuntimeLauncher(spawn=_spawn_from(registry), clock=FakeClock(), sleep=lambda s: None)
    children = [
        ChildSpec("worker", ["py", "worker"]),
        ChildSpec("metrics-exporter", ["py", "exporter"]),
    ]
    started = launcher.start(children, env={})
    assert set(started) == {"worker", "metrics-exporter"}
    assert launcher._procs["worker"] is registry["worker"]

    stopped = launcher.stop()
    assert stopped["worker"]["exit_code"] == 0
    assert registry["worker"]._terminated
    assert registry["metrics-exporter"]._terminated
    assert launcher._procs == {}


def test_run_normal_returns_no_early_exit():
    registry = {}
    launcher = RuntimeLauncher(spawn=_spawn_from(registry), clock=FakeClock(), sleep=lambda s: None)
    children = [
        ChildSpec("worker", ["x"]),
        ChildSpec("metrics-exporter", ["y"]),
    ]
    result = launcher.run(children, env={}, max_seconds=2)
    assert result["exited_early"] is None
    assert set(result["children"]) == {"worker", "metrics-exporter"}


def test_run_fail_fast_detects_early_exit():
    registry = {}
    launcher = RuntimeLauncher(spawn=_spawn_from(registry, early="worker"), clock=FakeClock(), sleep=lambda s: None)
    children = [
        ChildSpec("worker", ["x"]),
        ChildSpec("metrics-exporter", ["y"]),
    ]
    result = launcher.run(children, env={}, max_seconds=2)
    assert result["exited_early"] == "worker"
