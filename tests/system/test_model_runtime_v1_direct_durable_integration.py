from __future__ import annotations

import base64
import hashlib
import sys
import subprocess
from pathlib import Path
from unittest import mock

import pytest

SYSTEM = Path(__file__).resolve().parents[2] / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))
import codex_user_runner as runner


def test_direct_durable_receipt_persisted_without_model_request(tmp_path):
    request_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    receipt_file = tmp_path / "results" / (request_id + ".json")
    output = "图文模型输出".encode("utf8")
    with mock.patch.object(runner, "bridge_required", return_value=False), \
         mock.patch.object(runner, "task_result_path", return_value=receipt_file), \
         mock.patch.object(runner.subprocess, "run", return_value=subprocess.CompletedProcess(
             ["codex"], 0, stdout=output, stderr=None)) as launch:
        done = runner.run_model_codex(["codex", "exec", "--json", "-"],
                                      input="test", stdout=subprocess.PIPE,
                                      request_id=request_id, task_type="critic")
        assert done.returncode == 0
        proof = runner.read_task_result(request_id)
        assert proof["request_id"] == request_id
        assert proof["output_sha256"] == hashlib.sha256(output).hexdigest()
        assert base64.b64decode(proof["output_base64"]) == output
        assert proof["evidence"]["request_id"] == request_id
        with pytest.raises(runner.CodexUserRunnerRejected, match="DUPLICATE_REQUEST_ID"):
            runner.run_model_codex(["codex", "exec", "-"],
                                   input="again", stdout=subprocess.PIPE,
                                   request_id=request_id)
        launch.assert_called_once()


def test_direct_request_id_never_dispatches_without_durable_stdout(tmp_path):
    request_id = "11111111-2222-3333-4444-555555555555"
    with mock.patch.object(runner, "bridge_required", return_value=False), \
         mock.patch.object(runner, "task_result_path",
                           return_value=tmp_path / "results" / (request_id + ".json")), \
         mock.patch.object(runner.subprocess, "run") as launch:
        with pytest.raises(runner.CodexUserRunnerRejected, match="DURABLE_OUTPUT_REQUIRED"):
            runner.run_model_codex(["codex", "exec", "-"], request_id=request_id,
                                   stdout=subprocess.DEVNULL)
        launch.assert_not_called()


def test_persist_is_non_overwriting_even_if_preflight_races(tmp_path):
    rid = "99999999-9999-9999-9999-999999999999"
    result_path = tmp_path / "receipts" / (rid + ".json")
    done = subprocess.CompletedProcess(["codex"], 0, stdout=b"first", stderr=None)
    with mock.patch.object(runner, "task_result_path", return_value=result_path):
        runner._persist_direct_result(rid, done, subprocess.PIPE, {"transport_route": "native_codex"})
        before = result_path.read_bytes()
        with pytest.raises(FileExistsError):
            runner._persist_direct_result(rid, done, subprocess.PIPE, {"transport_route": "native_codex"})
        assert result_path.read_bytes() == before
        assert not list(result_path.parent.glob("*.pending"))


def test_read_durable_receipt_rejects_identity_spoofing(tmp_path):
    rid = "01234567-89ab-cdef-0123-456789abcdef"
    path = tmp_path / (rid + ".json")
    path.write_text('{"request_id":"another-id","output_sha256":"fake"}', encoding="utf-8")
    with mock.patch.object(runner, "task_result_path", return_value=path):
        assert runner.read_task_result(rid) == {}


def test_unknown_direct_timeout_keeps_reservation_and_blocks_retry(tmp_path):
    rid = "abababab-abab-abab-abab-abababababab"
    result = tmp_path / "results" / (rid + ".json")
    def uncertain(command, **kwargs):
        raise subprocess.TimeoutExpired(command, 5)
    with mock.patch.object(runner, "bridge_required", return_value=False), \
         mock.patch.object(runner, "task_result_path", return_value=result), \
         mock.patch.object(runner.subprocess, "run", side_effect=uncertain) as launch:
        with pytest.raises(subprocess.TimeoutExpired):
            runner.run_model_codex(["codex", "exec", "-"], request_id=rid,
                                   input="first", timeout=5, stdout=subprocess.PIPE)
        assert result.with_name(result.name + ".dispatching").is_file()
        assert not result.exists()
        with pytest.raises(runner.CodexUserRunnerRejected, match="OUTCOME_UNKNOWN"):
            runner.run_model_codex(["codex", "exec", "-"], request_id=rid,
                                   input="retry", timeout=5, stdout=subprocess.PIPE)
        launch.assert_called_once()


def test_normal_direct_completion_clears_only_its_dispatch_guard(tmp_path):
    rid="abcdefab-cdef-abcd-efab-cdefabcdefab"
    result=tmp_path/"receipts"/(rid+".json")
    with mock.patch.object(runner,"bridge_required",return_value=False), \
         mock.patch.object(runner,"task_result_path",return_value=result), \
         mock.patch.object(runner.subprocess,"run",return_value=subprocess.CompletedProcess(
             ["codex"],0,stdout=b"ok",stderr=None)):
        runner.run_model_codex(["codex","exec","-"],input="hi",request_id=rid,
                               stdout=subprocess.PIPE)
    assert result.is_file()
    assert not result.with_name(result.name+".dispatching").exists()


def test_direct_file_sink_persists_exact_output(tmp_path):
    rid="fedcba98-7654-3210-fedc-ba9876543210"
    result=tmp_path/"receipts"/(rid+".json")
    log=tmp_path/"output.jsonl"
    output='{"type":"turn.completed"}\n'.encode("utf8")
    def simulated_run(cmd,**kwargs):
        kwargs["stdout"].write(output.decode("utf8"))
        return subprocess.CompletedProcess(cmd,0,None,None)
    with mock.patch.object(runner,"bridge_required",return_value=False), \
         mock.patch.object(runner,"task_result_path",return_value=result), \
         mock.patch.object(runner.subprocess,"run",side_effect=simulated_run):
        with log.open("w",encoding="utf8",newline="\n") as handle:
            runner.run_model_codex(["codex","exec","-"],request_id=rid,
                                   stdout=handle,input="abc")
    with mock.patch.object(runner,"task_result_path",return_value=result), \
         mock.patch.object(runner,"bridge_required",return_value=False):
        record=runner.read_task_result(rid)
    assert base64.b64decode(record["output_base64"])==output


def test_atomic_publish_failure_never_leaves_partial_json(tmp_path):
    rid="f"*32
    path=tmp_path/"results"/(rid+".json")
    done=subprocess.CompletedProcess(["codex"],0,stdout=b"ok",stderr=None)
    with mock.patch.object(runner,"task_result_path",return_value=path), \
         mock.patch.object(runner.os,"link",side_effect=OSError("atomic link disabled")):
        with pytest.raises(OSError):
            runner._persist_direct_result(rid,done,subprocess.PIPE,{})
    assert not path.exists()
    assert not list(path.parent.glob("*.pending"))


def test_nonzero_direct_exit_is_recovered_as_failure_not_success(tmp_path):
    rid="f0"*16
    path=tmp_path/"result"/(rid+".json")
    with mock.patch.object(runner,"bridge_required",return_value=False), \
         mock.patch.object(runner,"task_result_path",return_value=path), \
         mock.patch.object(runner.subprocess,"run",return_value=subprocess.CompletedProcess(
             ["codex"],13,stdout=b'{"type":"turn.failed"}\n',stderr=None)):
        cp=runner.run_model_codex(["codex","exec","-"],request_id=rid,
                                  input="x",stdout=subprocess.PIPE)
    assert cp.returncode==13
    with mock.patch.object(runner,"task_result_path",return_value=path), \
         mock.patch.object(runner,"bridge_required",return_value=False):
        row=runner.read_task_result(rid)
    assert row["returncode"]==13
    assert b"turn.failed" in base64.b64decode(row["output_base64"])


def test_critic_forwards_preallocated_durable_request_id(tmp_path):
    import codex_critic_runner as critic
    rid="a1"*16
    fake=subprocess.CompletedProcess(["codex"],0,stdout=b"",stderr=None)
    fake.remote={"request_id":rid}
    # Deliberately incomplete semantic model binding causes validation to stop
    # after dispatch and before any database/model receipt writes.
    with mock.patch.object(critic.codex_user_runner,"run_model_codex",
                           return_value=fake) as dispatch:
        with pytest.raises(ValueError,match="model execution context requires"):
            critic.launch("text",codex=Path("codex.exe"),root=tmp_path,timeout=2,
                model_execution_context={"episode":tmp_path,"runner_request_id":rid})
    assert dispatch.call_args.kwargs["request_id"]==rid


def test_critic_invalid_request_id_rejected_before_dispatch(tmp_path):
    import codex_critic_runner as critic
    with mock.patch.object(critic.codex_user_runner,"run_model_codex") as dispatch:
        with pytest.raises(ValueError,match="invalid runner request_id"):
            critic.launch("text",codex=Path("codex.exe"),root=tmp_path,timeout=2,
                model_execution_context={"episode":tmp_path,"runner_request_id":"invalid/../id"})
        dispatch.assert_not_called()


def test_critic_does_not_truncate_review_log_when_request_already_has_result(tmp_path):
    import codex_critic_runner as critic
    rid="99"*16
    log=tmp_path/"review.jsonl"
    log.write_text("preserved-final-semantic-result",encoding="utf8")
    prior=tmp_path/"results"/(rid+".json")
    prior.parent.mkdir(parents=True)
    prior.write_text('{"request_id":"'+rid+'"}',encoding="utf8")
    with mock.patch.object(critic.codex_user_runner,"task_result_path",return_value=prior), \
         mock.patch.object(critic.codex_user_runner,"run_model_codex") as dispatch:
        with pytest.raises(runner.CodexUserRunnerRejected,match="DUPLICATE_REQUEST_ID"):
            critic.launch("text",codex=Path("codex.exe"),root=tmp_path,timeout=2,
                          log_path=log,
                          model_execution_context={"episode":tmp_path,"runner_request_id":rid})
        dispatch.assert_not_called()
    assert log.read_text(encoding="utf8")=="preserved-final-semantic-result"
