from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes/_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

import runtime_command


CORE_INTERNAL_WRAPPERS = (
    "runtime_dag.py",
    "runtime_mode_router.py",
    "workflow_runner.py",
    "incremental_closure.py",
    "codex_auto_orchestrator.py",
    "final_checklist.py",
    "post_publish_review.py",
    "visual_lock_baseline_gate.py",
    "regression_matrix_v21.py",
)


def _direct_subprocess_runs(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id == "subprocess" and node.func.attr == "run":
            lines.append(node.lineno)
    return lines


def test_internal_python_wrappers_use_single_runtime_command_transport():
    for name in CORE_INTERNAL_WRAPPERS:
        path = SYSTEM / name
        source = path.read_text(encoding="utf-8")
        assert "runtime_command.run_argv" in source, name
        assert _direct_subprocess_runs(path) == [], (
            f"{name} bypasses runtime_command at lines {_direct_subprocess_runs(path)}"
        )


def test_utf8_child_round_trip_has_no_replacement_character():
    with tempfile.TemporaryDirectory(prefix="StoryOS-中文-UTF8-") as raw:
        root = Path(raw)
        script = root / "中文输出.py"
        expected = "中文路径正常｜夏夜返乡｜✓"
        script.write_text(
            "print(" + repr(expected) + ")\n",
            encoding="utf-8",
            newline="\n",
        )
        result = runtime_command.run_python(script, cwd=root, timeout=15)
        assert result.returncode == 0
        assert result.stdout.strip() == expected
        assert "�" not in result.stdout
