#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate C (P0-C): a step longer than the launcher's budget survives it, and the
process that ran it can be identified, read and asked how it ended.

Measured on 2026-09-15: CREATIVE_STORY takes ~16 min and PREIMAGE_COMPILE ~69 min,
while the host tool that launches Story OS allows 300 s. A Driver started in the
foreground is therefore killed while the step it is running is still going -- not
a Story OS timeout and not a Codex failure. `.storyos_cache/dag_detach.py` proved
the mechanism but is an operator's private script that starts `runtime_dag.py`
directly, bypassing the resident Driver; `runtime_driver.py` is that mechanism as
a product capability.

These tests exercise the real detach path -- real child processes, real
Toolhelp32 liveness, real log files -- rather than mocking the OS boundary, because
every historical failure here (a grandchild's stdout lost under DETACHED_PROCESS,
OpenProcess reporting ACCESS_DENIED for a live and a dead pid alike, a killed
Driver still reading as alive) was invisible to mocked tests.

Clipboard of what each test pins to the Gate C checklist is in the test bodies.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "episodes/_system"))

import persistent_runner_daemon
import episode_runner
import runtime_driver

# A controlled stand-in for a long scoped step: prints steadily so the log is
# observably being written by the process we are watching, for ~20 s.
PROBE = (
    "import time\n"
    "for i in range(200):\n"
    "    print('probe tick', i, flush=True)\n"
    "    time.sleep(0.1)\n"
)

# Opt-in only (STORY_OS_DRIVER_LONG_PROBE=1): the same probe, but past 300 s.
LONG_PROBE = (
    "import time\n"
    "for i in range(4200):\n"
    "    print('long probe tick', i, flush=True)\n"
    "    time.sleep(0.1)\n"
)

# Stands in for the host tool call: it starts a detached process and then does
# nothing but wait to be killed, exactly like a `driver start` whose launcher is
# on a 300 s budget. Written to a file so the test controls it byte for byte.
LAUNCHER = (
    "import json, sys, time\n"
    "from pathlib import Path\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "import runtime_driver\n"
    "proc = runtime_driver._detach([sys.executable, '-u', sys.argv[2]], Path(sys.argv[3]))\n"
    "Path(sys.argv[4]).write_text(json.dumps({'pid': proc.pid}), encoding='utf-8')\n"
    "time.sleep(300)\n"
)


def wait_for(predicate, timeout: float = 20.0, interval: float = 0.2) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(interval)
    return False


def read_log(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


class DetachedDriverContractTests(unittest.TestCase):

    def setUp(self) -> None:
        base = ROOT / "episodes" / "_tests"
        base.mkdir(parents=True, exist_ok=True)
        self._td = tempfile.TemporaryDirectory(prefix="driver-", dir=base)
        self.ep = Path(self._td.name)
        (self.ep / "meta").mkdir(parents=True, exist_ok=True)
        self._probes = []
        self._beats = []

    def tearDown(self) -> None:
        for stop in self._beats:
            stop.set()
        if os.name == "nt":
            task = runtime_driver.carrier_task_name(self.ep)
            script = f"Unregister-ScheduledTask -TaskName '{task}' -Confirm:$false -ErrorAction SilentlyContinue"
            try:
                subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                               capture_output=True, check=False, timeout=30)
            except Exception:
                pass
        # These are the test's own probes; the product deliberately has no kill
        # path (see test_the_driver_has_no_kill_path), so cleanup is the test's job.
        for proc in self._probes:
            try:
                if proc.poll() is None:
                    proc.kill()
                # Wait for it to really be gone: until then it still owns the
                # handle on its stdout log, and Windows refuses to unlink it.
                proc.wait(timeout=30)
            except Exception:
                pass
        for _ in range(20):
            try:
                self._td.cleanup()
                return
            except PermissionError:
                time.sleep(0.25)

    def _kill_probe_pid(self, pid_file: Path) -> None:
        """Stop a probe this test started. The product has no kill path by design."""
        try:
            pid = int(json.loads(pid_file.read_text(encoding="utf-8"))["pid"])
        except Exception:
            return
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, check=False)
        except Exception:
            pass
        wait_for(lambda: runtime_driver.liveness(pid) == "DEAD", 20)

    def spawn_probe(self, source: str, name: str = "probe"):
        log = self.ep / "meta/driver-logs" / f"{name}.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        proc = runtime_driver._detach([sys.executable, "-u", "-c", source], log)
        self._probes.append(proc)
        runtime_driver._write_record(
            self.ep, {"pid": proc.pid, "log": str(log), "rc": runtime_driver.RUNNING})
        # Beat from here for as long as the probe lives, the way the real Driver's
        # own daemon thread does. Without this a probe that outlives the 90 s
        # tolerance would read ALIVE_NOT_BEATING -- correct for a stale beacon, and
        # a false alarm for a process that is plainly still working.
        self._beat(proc)
        return proc, log

    def _beat(self, proc) -> None:
        stop = threading.Event()
        self._beats.append(stop)
        # Beat once now: the caller reads status() within the second, and a Driver
        # that has only just been launched is exactly as alive as one beating for
        # an hour.
        runtime_driver.write_beacon(self.ep, proc.pid, beat=1)

        def loop() -> None:
            beat = 2
            while not stop.wait(5.0):
                if proc.poll() is not None:
                    return
                try:
                    runtime_driver.write_beacon(self.ep, proc.pid, beat=beat)
                except Exception:
                    return
                beat += 1

        threading.Thread(target=loop, name="probe-beacon", daemon=True).start()

    # --- 真正执行进程 PID 可识别 / stdout 可查 -------------------------------

    def test_detached_process_outlives_the_call_that_started_it(self):
        proc, log = self.spawn_probe(PROBE)
        self.assertNotEqual(proc.pid, os.getpid())

        self.assertTrue(wait_for(lambda: "probe tick" in read_log(log)),
                        "分离进程没有把 stdout 写进日志文件")

        # The recorded pid is a row in the OS process table, i.e. it names the
        # process that is actually doing the work, and the log the record points
        # at is the file that process is writing.
        self.assertEqual(runtime_driver.liveness(proc.pid), "ALIVE")
        self.assertIn(proc.pid, [row[0] for row in runtime_driver.process_table()])

        data = runtime_driver.status(self.ep)
        self.assertEqual(data["driver_state"], "RUNNING")
        self.assertIsNone(data["exit_code"] or None)
        self.assertIn("probe tick", "\n".join(runtime_driver.log_tail(self.ep, 5)))
        self.assertGreater(data["log_bytes"], 0)

    def test_the_launch_call_does_not_wait_for_the_task(self):
        """The host budget applies to the launching call, not to the Driver."""
        started = time.monotonic()
        _, log = self.spawn_probe(PROBE)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 10.0, "启动调用被长任务阻塞，宿主超时会连带杀死它")
        self.assertEqual(runtime_driver.liveness(runtime_driver._read_record(self.ep)["pid"]), "ALIVE")
        self.assertTrue(wait_for(lambda: "probe tick" in read_log(log)))

    def test_the_work_outlives_the_call_that_launched_it(self):
        """宿主 tool 调用被杀：这是 300s 墙的实际形态，Driver 不得跟着死。

        The launcher here is a separate process that does nothing but start the
        work and wait to be killed -- the same shape as a `driver start` whose
        host call is on a 300 s budget.
        """
        probe = self.ep / "probe.py"
        probe.write_text(PROBE, encoding="utf-8")
        launcher = self.ep / "launcher.py"
        launcher.write_text(LAUNCHER, encoding="utf-8")
        log = self.ep / "meta/driver-logs/outlives.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        pid_file = self.ep / "launcher-pid.json"

        host = subprocess.Popen(
            [sys.executable, "-u", str(launcher), str(ROOT / "episodes/_system"),
             str(probe), str(log), str(pid_file)],
            cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._probes.append(host)
        try:
            self.assertTrue(wait_for(pid_file.is_file, 30), "启动进程没有报出被分离的 pid")
            worker_pid = int(json.loads(pid_file.read_text(encoding="utf-8"))["pid"])
            self.assertEqual(runtime_driver.liveness(worker_pid), "ALIVE")

            host.kill()
            host.wait(timeout=30)

            self.assertTrue(wait_for(lambda: read_log(log).count("probe tick") > 5, 20),
                            "宿主调用死亡后，被分离的进程不再产出")
            self.assertEqual(runtime_driver.liveness(worker_pid), "ALIVE",
                             "宿主调用一死，长任务就跟着死了")
        finally:
            self._kill_probe_pid(pid_file)

    def test_detach_requests_its_own_console_and_process_group(self):
        """The flags are the whole mechanism, and on this host they are not
        otherwise observable: the test process has no console of its own, so an
        inherited-console probe reports 0 whether or not the flag is set."""
        captured = {}

        def fake_popen(cmd, **kwargs):
            captured.update(kwargs)
            raise RuntimeError("stop here")

        with mock.patch.object(runtime_driver.subprocess, "Popen", side_effect=fake_popen):
            with self.assertRaises(RuntimeError):
                runtime_driver._detach([sys.executable, "-c", "pass"], self.ep / "x.log")

        flags = captured.get("creationflags", 0)
        self.assertTrue(flags & subprocess.DETACHED_PROCESS, "没有脱离控制台，控制台关闭会连带杀死 Driver")
        self.assertTrue(flags & subprocess.CREATE_NEW_PROCESS_GROUP, "没有独立进程组")
        self.assertTrue(flags & subprocess.CREATE_BREAKAWAY_FROM_JOB, "没有脱离宿主 Job 对象")
        self.assertIsNotNone(captured.get("stdout"), "stdout 不是文件，宿主一死日志就断")

    def test_new_driver_epoch_does_not_inherit_old_carrier_or_terminal_fields(self):
        runtime_driver._write_record(self.ep, {
            "pid": 0, "rc": "900 old", "carrier": "WINDOWS_TASK_SCHEDULER",
            "carrier_task": "StoryOSDriver-old", "direct_detach_error": "old-breakaway",
            "carrier_error": "old-carrier", "exited_at": "old-time",
        })
        runtime_driver._begin_record(self.ep, {
            "pid": 123, "rc": runtime_driver.RUNNING, "carrier": "DIRECT_BREAKAWAY",
            "episode": str(self.ep), "started_at": "new-time",
        })
        row = runtime_driver._read_record(self.ep)
        self.assertEqual(row["carrier"], "DIRECT_BREAKAWAY")
        self.assertEqual(row["rc"], runtime_driver.RUNNING)
        for stale in ("carrier_task", "direct_detach_error", "carrier_error", "exited_at"):
            self.assertNotIn(stale, row)

    def test_product_detach_does_not_silently_fall_back_when_breakaway_is_denied(self):
        calls = []

        def denied(cmd, **kwargs):
            calls.append(kwargs.get("creationflags", 0))
            raise OSError("job forbids breakaway")

        with mock.patch.object(runtime_driver.subprocess, "Popen", side_effect=denied):
            with self.assertRaises(runtime_driver.DetachedLaunchError):
                runtime_driver._detach([sys.executable, "-c", "pass"], self.ep / "strict.log",
                                       require_breakaway=True)
        self.assertEqual(len(calls), 1, "产品启动不应再尝试一个仍属于宿主 Job 的假 detached child")
        self.assertTrue(calls[0] & subprocess.CREATE_BREAKAWAY_FROM_JOB)

    def test_task_scheduler_carrier_is_same_driver_and_has_logon_recovery_trigger(self):
        cmd = [sys.executable, "-u", str(ROOT / "episodes/_system/runtime_driver.py"),
               "_serve_task", str(self.ep), "--interval", "10", "--log", str(self.ep / "driver.log")]
        task, script = runtime_driver.task_carrier_script(self.ep, cmd, carrier_user="RENRP\\yeqian")
        self.assertTrue(task.startswith("StoryOSDriver-"))
        self.assertIn("Register-ScheduledTask", script)
        self.assertIn("Start-ScheduledTask", script)
        self.assertIn("New-ScheduledTaskTrigger -AtLogOn", script)
        self.assertIn("_serve_task", script)
        self.assertIn("runtime_driver.py", script)
        self.assertIn("RENRP\\yeqian", script)
        self.assertNotIn("WindowsIdentity]::GetCurrent", script, "service identity must not leak into the durable carrier")
        self.assertNotIn("runtime_dag.py", script, "OS carrier must not become a second DAG entrypoint")

    def test_task_carrier_prefers_current_interactive_identity(self):
        with mock.patch.object(runtime_driver.codex_user_runner, "current_identity", return_value="RENRP\\yeqian"), \
                mock.patch.object(runtime_driver.codex_user_runner, "is_non_interactive", return_value=False), \
                mock.patch.object(runtime_driver.codex_user_runner, "read_endpoint") as endpoint:
            user, source = runtime_driver.resolve_task_carrier_user()
        self.assertEqual((user, source), ("RENRP\\yeqian", "current_interactive_identity"))
        endpoint.assert_not_called()

    def test_system_launcher_uses_live_interactive_runner_identity(self):
        with mock.patch.object(runtime_driver.codex_user_runner, "current_identity", return_value="DIGITALCHINA\\SYSTEM"), \
                mock.patch.object(runtime_driver.codex_user_runner, "is_non_interactive", side_effect=lambda value=None: str(value).upper().endswith("SYSTEM")), \
                mock.patch.object(runtime_driver.codex_user_runner, "read_endpoint", return_value={"user":"RENRP\\yeqian","pid":123}), \
                mock.patch.object(runtime_driver.codex_user_runner, "_pid_alive", return_value=True), \
                mock.patch.object(runtime_driver.codex_user_runner, "expected_user", return_value=None):
            user, source = runtime_driver.resolve_task_carrier_user()
        self.assertEqual((user, source), ("RENRP\\yeqian", "live_codex_user_runner_endpoint"))

    def test_system_launcher_never_registers_system_without_interactive_proof(self):
        with mock.patch.object(runtime_driver.codex_user_runner, "current_identity", return_value="DIGITALCHINA\\SYSTEM"), \
                mock.patch.object(runtime_driver.codex_user_runner, "is_non_interactive", return_value=True), \
                mock.patch.object(runtime_driver.codex_user_runner, "read_endpoint", return_value={}):
            with self.assertRaisesRegex(runtime_driver.DetachedLaunchError, "INTERACTIVE_USER_UNAVAILABLE"):
                runtime_driver.resolve_task_carrier_user()

    # --- 被强杀的 Driver 不得被报成还在跑 ------------------------------------

    def test_a_vanished_driver_is_not_reported_as_running(self):
        proc, _ = self.spawn_probe(PROBE, "killed")
        proc.kill()
        proc.wait(timeout=20)

        self.assertTrue(wait_for(lambda: runtime_driver.liveness(proc.pid) == "DEAD"),
                        "已被杀死的进程仍被判为存活——这正是 2026-09-15 隐藏了 12 分钟的那个误判")
        data = runtime_driver.status(self.ep)
        self.assertEqual(data["driver_state"], "ABNORMAL_DISAPPEARANCE")
        self.assertEqual(data["exit_code"], "")

        report = runtime_driver.recover(self.ep)
        self.assertEqual(report["recovery"], "START")
        self.assertIn("in-flight", report["note"])

    # --- Driver exit code 可查（真实分离进程，端到端） -----------------------

    def test_launch_records_a_queryable_exit_code(self):
        (self.ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": "PUBLISHED"}), encoding="utf-8")
        result = runtime_driver.launch(self.ep, interval=0, settle_seconds=0)
        self.assertTrue(result.get("started"), result)
        self.assertEqual(runtime_driver.liveness(result["pid"]), "ALIVE")

        self.assertTrue(
            wait_for(lambda: runtime_driver.exit_code_of(runtime_driver._read_record(self.ep)) != "",
                     timeout=90),
            "分离的 Driver 结束后没有留下退出码")

        # EXITED must hold the moment the exit code lands, not two seconds later
        # once the interpreter has finished tearing down and left the pid table.
        data = runtime_driver.status(self.ep)
        self.assertEqual(data["driver_state"], "EXITED")
        self.assertNotEqual(data["exit_code"], "")
        self.assertGreater(data["log_bytes"], 0, "Driver 的 stdout 不可查")
        self.assertEqual(data["pid"], 0, "收尾时没有交还 pid，状态仍要靠猜")
        # It ran as the resident Driver (owner lock + heartbeat), not as a private
        # second entrypoint straight into runtime_dag.
        self.assertTrue(data["heartbeat_status"], "分离进程没有作为常驻 Driver 运行")

    def test_finishing_inside_the_start_window_is_a_successful_start(self):
        """An episode already at its terminal state ends the Driver in ~2 s.

        That is a completed start whose work is done, not a launch failure; calling
        it EXITED_DURING_STARTUP would send an operator hunting for a bug that is
        not there.
        """
        (self.ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": "PUBLISHED"}), encoding="utf-8")
        result = runtime_driver.launch(self.ep, interval=0, settle_seconds=3.0)
        self.assertTrue(result.get("started"), result)
        self.assertEqual(result["reason"] if "reason" in result else "", "")
        self.assertTrue(result.get("exit_code"), result)
        self.assertTrue(runtime_driver.interpret_rc(result["exit_code"]) is not None)

    def test_the_official_entrypoint_reports_driver_state(self):
        """Gate C is met through `story_os.py driver`, not a private script."""
        runtime_driver._write_record(
            self.ep, {"pid": os.getpid(), "log": "", "rc": runtime_driver.RUNNING})
        runtime_driver.write_beacon(self.ep, os.getpid(), beat=1)
        cp = subprocess.run(
            [sys.executable, str(ROOT / "episodes/_system/story_os.py"),
             "driver", "status", str(self.ep), "--json"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        data = json.loads(cp.stdout)
        self.assertEqual(data["driver_state"], "RUNNING")
        self.assertEqual(data["pid"], os.getpid())

    def test_the_resident_driver_can_run_a_scoped_codex_step(self):
        """P0-B/P0-D 的接缝：常驻 Driver 必须能把 codex 透传到步骤引擎。

        `execute_cycle` 曾经整个丢掉 codex 参数，于是唯一能跑 scoped 步骤的通道
        只剩被归类为「步骤引擎」的 `dag run` —— 这正是"文档定的唯一驱动跑不动
        生产"的根因。此测试盯住这条透传链的每一段。
        """
        seen = {}
        with mock.patch.object(persistent_runner_daemon.episode_runner, "run_episode",
                               side_effect=lambda ep, **kw: seen.update(kw) or 0):
            self.assertEqual(persistent_runner_daemon.run(self.ep, interval=0,
                                                          codex="C:/codex.exe"), 0)
        self.assertEqual(seen.get("codex"), "C:/codex.exe")

        calls = []
        with mock.patch.object(episode_runner, "local_host_action", return_value=None), \
                mock.patch.object(episode_runner.next_action, "write", return_value={}), \
                mock.patch.object(episode_runner.runtime_dag, "execute",
                                  side_effect=lambda ep, **kw: calls.append(kw) or 0):
            episode_runner.execute_cycle(self.ep, codex="C:/codex.exe", timeout=1800)
        self.assertEqual(calls, [{"codex": "C:/codex.exe", "timeout": 1800}])

    def test_a_stale_beacon_is_not_reported_as_running(self):
        """A live pid that stopped beating is not evidence the Driver is fine."""
        runtime_driver._write_record(
            self.ep, {"pid": os.getpid(), "log": "", "rc": runtime_driver.RUNNING})
        runtime_driver.write_beacon(self.ep, os.getpid())
        beacon_file = self.ep / runtime_driver.BEACON_REL
        stale = json.loads(beacon_file.read_text(encoding="utf-8"))
        stale["at"] = "2020-01-01T00:00:00+08:00"
        beacon_file.write_text(json.dumps(stale), encoding="utf-8")

        data = runtime_driver.status(self.ep)
        self.assertEqual(data["driver_state"], "ALIVE_NOT_BEATING")
        self.assertGreater(data["beacon_age_seconds"], runtime_driver.BEACON_TOLERANCE_SECONDS)

    def test_a_beacon_for_another_pid_is_not_evidence(self):
        runtime_driver._write_record(
            self.ep, {"pid": os.getpid(), "log": "", "rc": runtime_driver.RUNNING})
        runtime_driver.write_beacon(self.ep, os.getpid() + 1)
        self.assertEqual(runtime_driver.status(self.ep)["driver_state"], "ALIVE_NOT_BEATING")

    def test_serve_records_the_exit_code_it_returns(self):
        for rc in (0, 20, 23):
            with mock.patch.object(persistent_runner_daemon, "run", return_value=rc):
                self.assertEqual(runtime_driver.serve(self.ep, interval=0), rc)
            record = runtime_driver._read_record(self.ep)
            self.assertEqual(runtime_driver.exit_code_of(record), str(rc))
        self.assertEqual(runtime_driver.interpret_rc("0"), "正常结束")
        self.assertNotEqual(runtime_driver.interpret_rc("20"), "")
        self.assertNotEqual(runtime_driver.interpret_rc("25"), "")

    def test_a_crashing_driver_still_leaves_an_exit_code(self):
        with mock.patch.object(persistent_runner_daemon, "run", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                runtime_driver.serve(self.ep, interval=0)
        self.assertEqual(runtime_driver.exit_code_of(runtime_driver._read_record(self.ep)), "900")

    # --- 不重复启动、不擅自杀进程 -------------------------------------------

    def test_a_second_driver_is_refused_while_one_is_provably_alive(self):
        # This test process is, by definition, an alive pid, and the beacon is what
        # makes it provably *our* Driver rather than a recycled pid.
        runtime_driver._write_record(
            self.ep, {"pid": os.getpid(), "log": "", "rc": runtime_driver.RUNNING})
        runtime_driver.write_beacon(self.ep, os.getpid(), beat=1)
        result = runtime_driver.launch(self.ep)
        self.assertFalse(result.get("started"))
        self.assertEqual(result["reason"], "DRIVER_ALREADY_RUNNING")
        self.assertEqual(result["pid"], os.getpid())

    def test_a_recycled_pid_does_not_wedge_the_episode(self):
        """A live pid with no beacon is not our Driver, and must not block a restart.

        Otherwise a killed Driver whose pid Windows handed to an unrelated process
        would make the episode permanently unstartable.
        """
        runtime_driver._write_record(
            self.ep, {"pid": os.getpid(), "log": "", "rc": runtime_driver.RUNNING})
        data = runtime_driver.status(self.ep)
        self.assertEqual(data["driver_state"], "ALIVE_NOT_BEATING")
        self.assertEqual(runtime_driver.recover(self.ep)["recovery"], "VERIFY_BEFORE_START")

        (self.ep / "meta/episode-state.json").write_text(
            json.dumps({"current_state": "PUBLISHED"}), encoding="utf-8")
        self.assertTrue(runtime_driver.launch(self.ep, interval=0, settle_seconds=0)["started"],
                        "被复用的 pid 让这个 Episode 再也起不来了")
        self.assertTrue(wait_for(lambda: runtime_driver.status(self.ep)["driver_state"] == "EXITED",
                                 timeout=90), "新启动的 Driver 没有收尾")

    def test_launch_refuses_a_directory_that_is_not_an_episode(self):
        other = self.ep / "not-an-episode"
        other.mkdir()
        self.assertEqual(runtime_driver.launch(other)["reason"], "NOT_AN_EPISODE")

    def test_recover_never_starts_or_kills_anything(self):
        report = runtime_driver.recover(self.ep)
        self.assertEqual(report["driver_state"], "NEVER_STARTED")
        self.assertEqual(report["recovery"], "START")
        self.assertFalse(runtime_driver._read_record(self.ep).get("pid"),
                         "recover 只报告，不得顺手启动")

    def test_the_driver_has_no_kill_path(self):
        """Recovery is "start it again"; the in-flight result is claimed, not destroyed.

        Checked against the module's AST rather than its text so the docstring can
        keep explaining why `.storyos_cache/dag_detach.py` was not adopted.
        """
        tree = ast.parse((ROOT / "episodes/_system/runtime_driver.py").read_text(encoding="utf-8"))
        named = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                named.add(node.id)
            elif isinstance(node, ast.Attribute):
                named.add(node.attr)
            elif isinstance(node, ast.Import):
                named.update(alias.name.split(".")[-1] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                named.add((node.module or "").split(".")[-1])
        for forbidden in ("taskkill", "TerminateProcess", "kill", "terminate", "dag_detach"):
            self.assertNotIn(forbidden, named, f"runtime_driver 暴露了终止/私有依赖能力：{forbidden}")

    # --- >300s：宿主调用已返回，任务仍在跑 -----------------------------------

    @unittest.skipUnless(os.environ.get("STORY_OS_DRIVER_LONG_PROBE"),
                         "长任务实测需显式开启：STORY_OS_DRIVER_LONG_PROBE=1")
    def test_a_task_longer_than_the_host_budget_survives(self):
        """330 s > 宿主 300 s 预算：启动调用早已返回，进程与心跳仍在。"""
        proc, log = self.spawn_probe(LONG_PROBE, "long")
        time.sleep(330)
        self.assertEqual(runtime_driver.liveness(proc.pid), "ALIVE")
        self.assertEqual(runtime_driver.status(self.ep)["driver_state"], "RUNNING")
        self.assertIn("long probe tick 3200", read_log(log))


if __name__ == "__main__":
    unittest.main()
