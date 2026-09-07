#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B8 anti-regression sweep: runtime timeout literals must come from timeout_policy.

config/storyos.yaml:timeout_policy plus episodes/_system/runtime_timeout_policy.py is
the single default authority for every runtime timeout role. Production modules
expose CLI --timeout with default=None, function defaults as None resolved inside
the body, and pass library timeouts only as explicit overrides.

Remaining numeric literals are documented infrastructure exceptions:
- async_task_runtime.py: asyncio.wait_for(..., timeout=0.2) event-pump polls;
- persistent_runner_daemon.py: thread.join(timeout=5) daemon shutdown;
- runtime_dag.py: provisional_future.result(timeout=120) is the non-blocking
  pre-warm poll budget (provisional_release.build owns its own role default);
- runtime_atomic_store.py: FileLock/update_json timeout=15.0 is a file-lock
  acquisition bound, not a Codex/user role;
- runner_health_monitor.py: check(heartbeat_timeout=120) is a heartbeat
  freshness threshold, not a role default;
- self_test() bodies may probe subprocess transport timeouts
  (runtime_command.py run_python timeout=15);
- episodes/_system/test_*.py fixtures pass an explicit 30s budget to keep the
  mock pipeline fast (test isolation, never a default authority);
- episode_fingerprint.py delegates its --timeout to release_preflight's
  build_recent5(), whose internal None resolution owns the default, so it does
  not need to import the policy module itself.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"

# Modules whose scoped-codex step timeout and supervisor default must come from
# the policy module (story_os.py facade is the entry that forwards to them).
EXPECTED_POLICY_CONSUMERS = {
    "batch_scheduler.py",
    "caption_image_audit.py",
    "codex_auto_orchestrator.py",
    "codex_subscription_image.py",
    "concept_ambition.py",
    "episode_runner.py",
    "fast_frame_scout.py",
    "fingerprint_semantics.py",
    "frame_semantic_review.py",
    "image_provider_smoke.py",
    "image_scheduler.py",
    "image_worker_pool.py",
    "incremental_frame_review.py",
    "provisional_release.py",
    "release_preflight.py",
    "release_preflight_recent5.py",
    "rolling_frame_review.py",
    "runtime_dag.py",
    "runtime_mode_router.py",
    "scoped_codex_worker.py",
    "speculative_production.py",
    "story_os.py",
    "story_review.py",
    "storyos_config.py",
    "test_stage_v224.py",
    "test_stage_v225.py",
    "test_stage_v227.py",
    "visual_lock_baseline_gate.py",
    "visual_lock_v21.py",
    "visual_review.py",
    "visual_review_legacy.py",
    "workflow_runner.py",
}

ALLOWED_ANNOTATED_DEFAULTS = {
    # (file, qualified function/class name, param) -> numeric default
    ("runtime_atomic_store.py", "FileLock.__init__", "timeout"): 15.0,
    ("runtime_atomic_store.py", "update_json", "timeout"): 15.0,
    ("runner_health_monitor.py", "check", "heartbeat_timeout"): 120,
}

ALLOWED_CALL_LITERALS = {
    ("async_task_runtime.py", "wait_for"): 0.2,
    ("persistent_runner_daemon.py", "join"): 5,
    ("runtime_dag.py", "result"): 120,
}


def _func_ctx(ctx: list[ast.FunctionDef]) -> ast.FunctionDef | None:
    return ctx[-1] if ctx else None


class _SweepWalker(ast.NodeVisitor):
    """Collect timeout numeric literals that bypass runtime_timeout_policy."""

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        self.violations: list[str] = []
        self._ctx: list[ast.FunctionDef] = []
        self._classes: list[ast.ClassDef] = []

    def _qualified_name(self, node: ast.FunctionDef) -> str:
        if self._classes:
            return f"{self._classes[-1].name}.{node.name}"
        return node.name

    def _allow_annotated(self, func: ast.FunctionDef, param: str, value: object) -> bool:
        key = (self.file_name, self._qualified_name(func), param)
        if key in ALLOWED_ANNOTATED_DEFAULTS:
            return ALLOWED_ANNOTATED_DEFAULTS[key] == value
        return False

    def _allow_call(self, label: str, value: object) -> bool:
        key = (self.file_name, label)
        if key in ALLOWED_CALL_LITERALS:
            return ALLOWED_CALL_LITERALS[key] == value
        if self.file_name.startswith("test_") and value == 30:
            return True  # mock-pipeline fixture budget
        fn = _func_ctx(self._ctx)
        if fn is not None and fn.name == "self_test" and value == 15:
            return True  # cross-shell transport probe
        return False

    def _check_defaults(self, node: ast.FunctionDef) -> None:
        plain = node.args.posonlyargs + node.args.args
        for idx, arg in enumerate(plain):
            defaults = node.args.defaults
            off = len(plain) - len(defaults)
            if idx - off < 0:
                continue
            default = defaults[idx - off]
            if arg.arg.endswith("timeout") and _is_number(default):
                if not self._allow_annotated(node, arg.arg, default.value):
                    self.violations.append(
                        f"{node.lineno}: def {node.name} param {arg.arg} numeric default {default.value!r}")
        for idx, arg in enumerate(node.args.kwonlyargs):
            if idx >= len(node.args.kw_defaults):
                continue
            default = node.args.kw_defaults[idx]
            if default is not None and arg.arg.endswith("timeout") and _is_number(default):
                if not self._allow_annotated(node, arg.arg, default.value):
                    self.violations.append(
                        f"{node.lineno}: def {node.name} kwarg {arg.arg} numeric default {default.value!r}")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_defaults(node)
        self._ctx.append(node)
        self.generic_visit(node)
        self._ctx.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_defaults(node)
        self._ctx.append(node)
        self.generic_visit(node)
        self._ctx.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._classes.append(node)
        self.generic_visit(node)
        self._classes.pop()

    def _call_label(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return "<complex>"

    def visit_Call(self, node: ast.Call) -> None:
        label = self._call_label(node)
        if label == "add_argument":
            self._visit_add_argument(node)
            return
        for kw in node.keywords:
            if kw.arg != "timeout" or not _is_number(kw.value):
                continue
            if not self._allow_call(label, kw.value.value):
                self.violations.append(
                    f"{node.lineno}: call {label}(... timeout={kw.value.value!r}) numeric literal")
        self.generic_visit(node)

    def _visit_add_argument(self, node: ast.Call) -> None:
        flag = any(
            isinstance(a, ast.Constant) and isinstance(a.value, str) and "--timeout" in a.value
            for a in node.args)
        default = next((kw.value for kw in node.keywords if kw.arg == "default"), None)
        if flag and default is not None and _is_number(default):
            self.violations.append(
                f"{node.lineno}: --timeout argparse default={default.value!r} (must be None)")

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if (isinstance(target, ast.Name) and target.id.endswith("timeout")
                    and _is_number(node.value)):
                self.violations.append(
                    f"{node.lineno}: assign {target.id}={node.value.value!r} numeric literal")
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if (isinstance(node.target, ast.Name) and node.target.id.endswith("timeout")
                and node.value is not None and _is_number(node.value)):
            self.violations.append(
                f"{node.lineno}: annotate {node.target.id}={node.value.value!r} numeric literal")
        self.generic_visit(node)


def _is_number(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float))


def _scan() -> list[str]:
    violations: list[str] = []
    for py in sorted(SYSTEM.glob("*.py")):
        src = py.read_text(encoding="utf-8-sig")
        walker = _SweepWalker(py.name)
        try:
            tree = ast.parse(src, filename=str(py))
        except SyntaxError as exc:
            violations.append(f"{py.name}: unparsable {exc}")
            continue
        walker.visit(tree)
        for item in walker.violations:
            violations.append(f"{py.name}:{item}")
    return violations


class TimeoutPolicySweepTests(unittest.TestCase):
    def test_no_numeric_timeout_literals_outside_whitelist(self):
        self.assertEqual(_scan(), [])

    def test_policy_consumers_reference_the_policy_module(self):
        missing = []
        for py in sorted(SYSTEM.glob("*.py")):
            if py.name not in EXPECTED_POLICY_CONSUMERS:
                continue
            src = py.read_text(encoding="utf-8-sig")
            if "import runtime_timeout_policy" not in src and \
                    "from runtime_timeout_policy import" not in src:
                missing.append(f"{py.name} does not reference runtime_timeout_policy")
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
