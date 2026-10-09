"""Read-only Git integration gate: no production repo, branch or model calls."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

MODULE=Path(__file__).resolve().parents[2]/"scripts"/"storyos_model_runtime_merge_gate.py"
spec=importlib.util.spec_from_file_location("storyos_merge_gate",MODULE)
gate=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


def _git(root, *args):
    cp=subprocess.run(["git","-C",str(root),*args],check=True,
                      capture_output=True,text=True)
    return cp.stdout.strip()


def _commit(root, msg):
    _git(root,"add",".")
    _git(root,"commit","-m",msg)


def _fixture_repo(tmp_path):
    root=tmp_path/"repo"
    root.mkdir()
    _git(root,"init","-q")
    _git(root,"config","user.email","git-test@example.invalid")
    _git(root,"config","user.name","Test")
    _git(root,"checkout","-q","-b",gate.MAIN)
    (root/"runner.py").write_text("route = 'base'\n",encoding="utf8")
    _commit(root,"baseline")
    base=_git(root,"rev-parse","HEAD")
    _git(root,"checkout","-q","-b",gate.FEATURE)
    (root/"runner.py").write_text("route = 'native-only'\n",encoding="utf8")
    _commit(root,"feature")
    _git(root,"checkout","-q",gate.MAIN)
    _git(root,"checkout","-q","-b",gate.COMPANIONS[0])
    (root/"runner.py").write_text("route = 'native-plus-proof'\n",encoding="utf8")
    _commit(root,"native repair")
    _git(root,"checkout","-q",gate.MAIN)
    _git(root,"checkout","-q","-b",gate.COMPANIONS[1])
    (root/"runner.py").write_text("route = 'identity-verified'\n",encoding="utf8")
    _commit(root,"integration")
    _git(root,"checkout","-q",gate.MAIN)
    return root,base


def test_three_way_rehearsal_observes_real_conflicts_without_touching_worktree(tmp_path):
    root,base=_fixture_repo(tmp_path)
    before=(root/"runner.py").read_bytes()
    results=gate.diff_conflicts(root,base,gate.FEATURE,gate.COMPANIONS[0],{"runner.py"})
    assert len(results)==1
    assert results[0]["file"]=="runner.py"
    assert results[0]["kind"]=="content_conflict"
    assert results[0]["conflict_hunks"]>=1
    assert (root/"runner.py").read_bytes()==before
    assert _git(root,"status","--porcelain")==""


def test_merge_gate_blocks_dirty_main_and_overlapping_changes(tmp_path):
    root,_=_fixture_repo(tmp_path)
    (root/"runner.py").write_text("route = 'dirty-host'\n",encoding="utf8")
    state=gate.inspect(root)
    assert state["status"]=="NOT_READY_TO_MERGE_MAIN"
    assert state["main_worktree_dirty_entries"]>0
    assert state["main_dirty_overlapping_files"]==["runner.py"]
    assert "MAIN_UNCOMMITTED_FEATURE_OVERLAP" in state["blockers"]
    assert "COMPANION_SEMANTIC_MERGE_REQUIRED" in state["blockers"]
    assert state["production_cutover_verified"] is False
    assert state["model_capability_attested"] is False
    assert (root/"runner.py").read_text(encoding="utf8")=="route = 'dirty-host'\n"


def test_even_clean_main_cannot_skip_companion_conflicts(tmp_path):
    root,_=_fixture_repo(tmp_path)
    row=gate.inspect(root)
    assert "MAIN_WORKTREE_DIRTY" not in row["blockers"]
    assert "COMPANION_SEMANTIC_MERGE_REQUIRED" in row["blockers"]
    assert row["requires_integration_full_regression"] is True


def test_unsafe_refs_rejected_before_git_invocation(tmp_path,monkeypatch):
    monkeypatch.setattr(gate,"git",lambda *args,**kw:pytest.fail("must not run git"))
    with pytest.raises(ValueError,match="UNSAFE_GIT_REF"):
        gate.inspect(tmp_path,feature="--upload-pack=bad")


def test_conflict_free_clean_main_is_rehearsal_only_not_release(tmp_path):
    root,_=_fixture_repo(tmp_path)
    main_head=_git(root,"rev-parse",gate.MAIN)
    for companion in gate.COMPANIONS:
        _git(root,"branch","-f",companion,main_head)
    state=gate.inspect(root)
    assert state["status"]=="REHEARSAL_CANDIDATE_ONLY"
    assert state["blockers"]==[]
    assert state["requires_integration_full_regression"] is True
    assert state["production_cutover_verified"] is False
    assert state["model_capability_attested"] is False
    assert state["mysql_authority_e2e_verified"] is False
