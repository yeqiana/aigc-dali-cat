"""The signed-in interactive runner belongs to the shared repository, not a Git worktree."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

SYSTEM=Path(__file__).resolve().parents[2]/"episodes"/"_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0,str(SYSTEM))
import codex_user_runner as runner


def _fake_worktree(tmp_path):
    main=tmp_path/"storyOS"
    gitdir=main/".git"/"worktrees"/"feature-slot"
    gitdir.mkdir(parents=True)
    feature=main/".worktrees"/"feature-slot"
    feature.mkdir(parents=True)
    (feature/".git").write_text("gitdir: "+str(gitdir)+"\n",encoding="utf-8")
    return main, feature


def test_git_worktrees_use_one_shared_runner_endpoint_directory(tmp_path):
    main, feature = _fake_worktree(tmp_path)
    assert runner._shared_worktree_root(feature)==main
    with mock.patch.object(runner,"ROOT",feature):
        assert runner.runtime_dir()==main/runner.RUNTIME_REL
        assert runner.endpoint_path()==main/runner.RUNTIME_REL/runner.ENDPOINT_NAME
        assert runner.token_path()==main/runner.RUNTIME_REL/runner.TOKEN_NAME
        assert runner.task_result_path("a"*32)==feature/runner.RUNTIME_REL/runner.RESULT_DIR_NAME/("a"*32+".json")
    with mock.patch.object(runner,"ROOT",main):
        assert runner.runtime_dir()==main/runner.RUNTIME_REL


def test_untrusted_or_invalid_worktree_marker_falls_back_to_current_root(tmp_path):
    main, feature=_fake_worktree(tmp_path)
    for marker in ("not-a-gitdir\n","gitdir: /some/unrelated/.git/worktrees/missing\n","gitdir: "+str(main/".git")+"\n"):
        (feature/".git").write_text(marker,encoding="utf-8")
        assert runner._shared_worktree_root(feature)==feature


def test_runtime_root_does_not_depend_on_worker_identity_or_cli_login(tmp_path):
    main,feature=_fake_worktree(tmp_path)
    with mock.patch.dict(runner.os.environ, {"CODEX_HOME":"D:/other-profile/.codex"}), \
         mock.patch.object(runner,"ROOT",feature):
        assert runner.runtime_dir()==main/runner.RUNTIME_REL
    # The login credential remains in the runner process' user profile.


def test_git_marker_cannot_redirect_runner_to_unrelated_repo(tmp_path):
    original,feature=_fake_worktree(tmp_path)
    unrelated=tmp_path/"other_repo"
    pointer=unrelated/".git"/"worktrees"/"evil-slot"
    pointer.mkdir(parents=True)
    (feature/".git").write_text("gitdir: "+str(pointer),encoding="utf-8")
    assert runner._shared_worktree_root(feature)==feature
