"""Static graph records direct imports without claiming dynamic call ownership."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "slim_runtime_graph", ROOT / "scripts/storyos_runtime_callgraph.py")
assert spec and spec.loader
graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph)


def test_ast_import_extraction_ignores_strings_and_calls():
    source = """import alpha, beta as b
from gamma.sub import X
def f():
    import delta
    text = 'import fake'
"""
    assert graph.direct_imports(source) == {"alpha", "beta", "gamma", "delta"}
    assert graph.eager_imports(source) == {"alpha", "beta", "gamma"}


def test_static_edges_are_labeled_and_stable(tmp_path):
    (tmp_path / "one.py").write_text("import two\nfrom three import x\n", encoding="utf-8")
    (tmp_path / "two.py").write_text("from one import y\n", encoding="utf-8")
    (tmp_path / "three.py").write_text("def x(): pass\n", encoding="utf-8")
    result = graph.collect(tmp_path, ("three", "two", "one", "absent"))
    assert result["edges"] == [
        {"from": "one", "to": "three"}, {"from": "one", "to": "two"},
        {"from": "two", "to": "one"}]
    assert result["missing_modules"] == ["absent"]
    assert result["runtime_invocations_measured"] is False
    assert result["fan_out"]["one"] == 2
    assert result["deferred_edges"] == []


def test_real_graph_parses_without_implementation_side_effects():
    data = graph.collect(graph.SYSTEM)
    assert data["parse_errors"] == {}
    assert "runtime_dag" in data["modules"]
    assert data["analysis_kind"] == "static_import_graph_only"
    assert {"from": "runtime_scheduler", "to": "runtime_dag"} in data["deferred_edges"]
    assert {"from": "runtime_scheduler", "to": "runtime_dag"} not in data["eager_edges"]
