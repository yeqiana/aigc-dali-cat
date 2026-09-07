#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import codex_critic_runner as runner


class FakeCompleted:
    def __init__(self, returncode):
        self.returncode = returncode


class CodexCriticRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="critic-runner-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_prefix_python_and_plain(self):
        py = self.root / "codex.py"
        py.write_text("", encoding="utf-8")
        self.assertEqual(runner.prefix(py)[0], sys.executable)
        plain = self.root / "codex"
        plain.write_text("", encoding="utf-8")
        self.assertEqual(runner.prefix(plain), [str(plain)])

    @unittest.skipUnless(os.name == "nt", "cmd wrapper is Windows-only")
    def test_prefix_cmd_wrapper(self):
        cmd = self.root / "codex.cmd"
        cmd.write_text("@echo off", encoding="utf-8")
        self.assertEqual(runner.prefix(cmd)[:3],
                         ["cmd.exe", "/d", "/c"])

    def test_build_command_shape(self):
        cmd = runner.build_command(
            codex=Path("codex.exe"),
            root=self.root,
            sandbox="workspace-write",
            model="gpt-5.6-luna",
            reasoning_effort="medium",
            attachments=[Path("a.png")],
            output_path=Path("out.json"),
        )
        self.assertIn("--skip-git-repo-check", cmd)
        self.assertIn("--ephemeral", cmd)
        self.assertIn("--json", cmd)
        self.assertIn("-m", cmd)
        self.assertEqual(cmd[cmd.index("-m") + 1], "gpt-5.6-luna")
        self.assertIn("-i", cmd)
        self.assertIn("-o", cmd)
        self.assertEqual(cmd[-1], "-")
        effort_flag = cmd[cmd.index("-c") + 1]
        self.assertEqual(effort_flag, 'model_reasoning_effort="medium"')

    def test_launch_writes_log_and_returns_rc(self):
        target = self.root / "out.json"
        log = self.root / "meta" / "attempt-1.jsonl"
        with mock.patch.object(runner.subprocess, "run",
                               return_value=FakeCompleted(0)) as run:
            result = runner.launch(
                "prompt",
                codex=Path("codex.exe"),
                root=self.root,
                timeout=120,
                output_path=target,
                log_path=log,
            )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(log.is_file())
        self.assertEqual(run.call_args.kwargs["timeout"], 120)
        self.assertEqual(run.call_args.kwargs["stderr"],
                         runner.subprocess.STDOUT)
        self.assertTrue(hasattr(run.call_args.kwargs["stdout"], "write"))

    def test_timeout_propagates(self):
        log = self.root / "meta" / "attempt-1.jsonl"
        with mock.patch.object(runner.subprocess, "run",
                               side_effect=TimeoutError("boom")):
            with self.assertRaises(TimeoutError):
                runner.launch("prompt", codex=Path("codex.exe"),
                              root=self.root, timeout=1, log_path=log)

    def test_parse_json_helpers(self):
        payload = {"summary": {"passed": True}}
        self.assertEqual(runner.parse_json_text(json.dumps(payload)), payload)
        with self.assertRaises(ValueError):
            runner.parse_json_text("[1,2]")
        out = self.root / "out.json"
        out.write_text(json.dumps(payload), encoding="utf-8")
        self.assertEqual(runner.parse_json_file(out), payload)


if __name__ == "__main__":
    unittest.main()
