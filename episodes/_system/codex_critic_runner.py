#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS shared scoped Codex critic runner (B0).

Single implementation source for the critic process launch shared by
fast_frame_scout / visual_review_legacy / visual_lock_v21 /
frame_semantic_review / incremental_frame_review.  The Visual Lock V2.1
semantics are the reference model:

- prompt goes to stdin in a fresh isolated exec session;
- JSON output is persisted with -o when the consumer asks for a candidate
  file, otherwise it is read back from stdout;
- every launch writes a deterministic per-attempt log file;
- rc=0 plus valid JSON is content territory; anything else is a technical
  failure the consumer classifies with its own taxonomy.

This module never records ledger/health state: consumers keep their
attempt/technical-failure bookkeeping and their own prompts.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import codex_user_runner
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

SUCCESS_RC = 0
DEFAULT_LOG_NAME = "codex-critic-run.jsonl"


@dataclass
class LaunchResult:
    returncode: int
    log_path: Path
    log_text: str
    output: bytes = b""
    remote: dict | None = None
    execution_target: dict | None = None
    actual_dispatch_target: dict | None = None
    scheduler_authorized_target: dict | None = None
    router_proposed_target: dict | None = None
    model_execution_receipt: str | None = None


class ExecutionTargetRejected(RuntimeError):
    """The selected route cannot safely be consumed by this executor."""


def consume_scheduler_authorization(*, task_type, legacy_target, dispatch_authorization=None):
    """Validate and consume a Runtime Scheduler target; never resolve policy here."""
    target = dict(legacy_target or {})
    if not target:
        raise ExecutionTargetRejected("legacy execution target is required")
    allowed = {"story_semantic_critic", "preimage_semantic_critic", "final_semantic_critic"}
    if dispatch_authorization is None:
        import capability_router
        if (task_type in allowed
                and capability_router.effective_router_config()["production_enabled"] is True):
            raise ExecutionTargetRejected("production target requires Runtime Scheduler authorization")
        return target
    if not isinstance(dispatch_authorization, dict):
        raise ExecutionTargetRejected("invalid Runtime Scheduler authorization")
    if dispatch_authorization.get("task_type") != task_type:
        raise ExecutionTargetRejected("Scheduler authorization task binding mismatch")
    if dispatch_authorization.get("scheduler_authorized") is not True:
        raise ExecutionTargetRejected("Scheduler did not authorize Critic execution")
    selected = dispatch_authorization.get("execution_target")
    if not isinstance(selected, dict) or not selected:
        raise ExecutionTargetRejected("Scheduler authorization has no executable target")
    if (selected.get("provider") != "codex_user_runner"
            or selected.get("runtime") != "CODEX"
            or not isinstance(selected.get("model"), str)
            or not selected["model"].strip()):
        raise ExecutionTargetRejected("Scheduler target is not consumable by Codex Critic runner")
    return {"provider": selected["provider"], "model": selected["model"],
            "runtime": selected["runtime"]}


def resolve_codex(raw):
    import codex_cli_contract
    return codex_cli_contract.resolve_path(raw)


def prefix(codex):
    import codex_cli_contract
    return codex_cli_contract.command_prefix(codex)


def default_sandbox():
    return "danger-full-access" if os.name == "nt" else "workspace-write"


def resolve_sandbox(requested=None):
    """Resolve the nested-Codex sandbox flag for this platform.

    Windows cannot start the nested CLI under workspace-write
    (CreateProcessWithLogonW fails with 1385), so a workspace-write request
    degrades to the platform default there.  Other platforms keep the
    requested value, and non-workspace-write requests are never rewritten.
    """
    if os.name == "nt" and requested in (None, "workspace-write"):
        return default_sandbox()
    return requested or default_sandbox()


def default_log_path(root, tag="critic"):
    directory = Path(root).resolve() / "meta"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{tag}-run.jsonl"


def _persist_final_semantic_durable_result(
    episode, remote, expected_returncode, *, output_path=None,
):
    """Persist the exact User Runner output bytes referenced by a final receipt.

    A local Critic log is useful diagnostics, but it is not the durable result
    object written by the User Runner. Keep the durable bytes in the Episode
    runtime evidence area so result_ref and result_sha256 identify one object.
    Missing or incomplete durable evidence is deliberately reported as absent;
    the Final Semantic receipt remains provisional and cannot become success.
    """
    request_id = str((remote or {}).get("request_id") or "").strip()
    if not request_id:
        return {}
    try:
        # Reuse the User Runner's request-id contract before using it in a
        # runtime evidence filename.
        durable_path = codex_user_runner.task_result_path(request_id)
        durable = codex_user_runner.read_task_result(request_id)
        if (not isinstance(durable, dict)
                or str(durable.get("request_id") or "") != request_id
                or int(durable.get("returncode", -1)) != int(expected_returncode)):
            return {"durable_result_status": "MISSING_OR_MISMATCHED"}
        raw = base64.b64decode(str(durable.get("output_base64") or ""), validate=True)
        text = raw.decode("utf-8-sig", errors="replace")
        events = []
        for line in text.splitlines():
            try:
                event = json.loads(line)
            except Exception:
                continue
            if isinstance(event, dict):
                events.append(event)
        if not any(event.get("type") == "turn.completed" for event in events):
            return {"durable_result_status": "TURN_NOT_COMPLETED"}
        structured_result = recover_completed_agent_json(text)
        structured_result_source = "USER_RUNNER_AGENT_MESSAGE"
        if structured_result is None and output_path is not None:
            # Newer Codex CLI builds may keep the schema-bound answer in `-o`
            # while the final agent_message is a human-readable summary. The
            # output file is acceptable only when it is inside the same Episode
            # and the durable runner record proves rc=0 + turn.completed for
            # this exact request.
            candidate = Path(output_path).resolve()
            episode_root = Path(episode).resolve()
            try:
                candidate.relative_to(episode_root)
            except ValueError:
                return {"durable_result_status": "OUTPUT_PATH_OUTSIDE_EPISODE"}
            if candidate.is_file():
                try:
                    parsed = json.loads(candidate.read_bytes().decode("utf-8-sig"))
                except Exception:
                    parsed = None
                if isinstance(parsed, dict):
                    structured_result = parsed
                    structured_result_source = "CODEX_OUTPUT_FILE"
        if structured_result is None:
            return {"durable_result_status": "STRUCTURED_RESULT_MISSING"}
        # Keep the full task-result JSON in place in the User Runner. Copy only
        # a minimal, secret-safe projection into the Episode evidence area.
        durable_json = durable_path.read_bytes()
        if json.loads(durable_json.decode("utf-8-sig")) != durable:
            return {"durable_result_status": "DURABLE_JSON_MISMATCH"}
    except Exception:
        return {"durable_result_status": "DURABLE_RESULT_UNAVAILABLE"}

    target_dir = Path(episode).resolve() / "meta" / "runtime" / "model-execution-results"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{request_id}.projection.json"
    temporary = target.with_suffix(target.suffix + ".tmp")
    projection = {
        "schema": "storyos.user_runner_result_projection.v1",
        "request_id": request_id,
        "returncode": int(expected_returncode),
        "turn_completed": True,
        "structured_result": structured_result,
        "structured_result_source": structured_result_source,
        "output_sha256": hashlib.sha256(raw).hexdigest(),
        "copied_at": dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds"),
    }
    projection_bytes = (json.dumps(
        projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n").encode("utf-8")
    temporary.write_bytes(projection_bytes)
    temporary.replace(target)
    return {
        "result_ref": target.relative_to(Path(episode).resolve()).as_posix(),
        "result_sha256": hashlib.sha256(projection_bytes).hexdigest(),
        "result_sha256_source": "USER_RUNNER_DURABLE_RESULT_PROJECTION",
        "result_output_sha256": projection["output_sha256"],
        "execution_completion_source": "USER_RUNNER_DURABLE_RESULT",
        "durable_result_status": "VALIDATED",
    }


def build_command(
    *,
    codex,
    root,
    sandbox=None,
    attachments=None,
    model=None,
    reasoning_effort=None,
    reasoning_effort_literal=None,
    output_path=None,
    output_schema=None,
    extra=None,
):
    """Assemble one isolated Codex exec invocation.

    Flags follow visual_lock_v21 ordering.  reasoning_effort_literal passes an
    exact -c value (legacy fast scout uses model_reasoning_effort="low");
    otherwise -c model_reasoning_effort="<effort>" is generated.
    """
    cmd = prefix(codex) + [
        "exec", "--skip-git-repo-check", "--ephemeral",
        *(extra or []),
    ]
    if model:
        cmd += ["-m", model]
    if reasoning_effort_literal is not None:
        cmd += ["-c", reasoning_effort_literal]
    elif reasoning_effort:
        cmd += ["-c", f'model_reasoning_effort="{reasoning_effort}"']
    cmd += ["-s", resolve_sandbox(sandbox), "-C", str(root), "--json"]
    if output_schema is not None:
        cmd += ["--output-schema", str(output_schema)]
    if output_path is not None:
        cmd += ["-o", str(output_path)]
    for attachment in attachments or []:
        cmd += ["-i", str(attachment)]
    cmd += ["-"]
    return cmd


def launch(
    prompt,
    *,
    codex,
    root,
    timeout,
    output_path=None,
    output_schema=None,
    attachments=None,
    model=None,
    reasoning_effort=None,
    reasoning_effort_literal=None,
    sandbox=None,
    log_path=None,
    extra=None,
    execution_target=None,
    dispatch_authorization=None,
    router_proposed_target=None,
    model_execution_context=None,
):
    """Run one critic; returns rc plus the full attempt log text.

    subprocess.TimeoutExpired / OSError propagate to the consumer so each lane
    keeps its own technical-failure bookkeeping semantics.
    """
    resolved_log = log_path or default_log_path(root)
    resolved_log.parent.mkdir(parents=True, exist_ok=True)
    if execution_target is not None:
        if (not isinstance(execution_target, dict)
                or execution_target.get("provider") != "codex_user_runner"
                or execution_target.get("runtime") != "CODEX"
                or not isinstance(execution_target.get("model"), str)
                or not execution_target["model"].strip()):
            raise ExecutionTargetRejected("invalid execution target for Codex Critic runner")
        authorized = consume_scheduler_authorization(
            task_type=(dispatch_authorization or {}).get("task_type"),
            legacy_target=execution_target,
            dispatch_authorization=dispatch_authorization,
        ) if dispatch_authorization is not None else dict(execution_target)
        if authorized != execution_target:
            raise ExecutionTargetRejected("runner target differs from Scheduler authorization")
        model = execution_target["model"]
    cmd = build_command(
        codex=codex,
        root=root,
        sandbox=sandbox,
        attachments=attachments,
        model=model,
        reasoning_effort=reasoning_effort,
        reasoning_effort_literal=reasoning_effort_literal,
        output_path=output_path,
        output_schema=output_schema,
        extra=extra,
    )
    planned_request_id = (
        str(model_execution_context.get("runner_request_id") or "").strip()
        if isinstance(model_execution_context, dict) else ""
    )
    if planned_request_id:
        # Fail before truncating review logs; the existing result belongs to
        # the previous dispatch and must be reconciled, never overwritten.
        prior = codex_user_runner.task_result_path(planned_request_id)
        if prior.is_file():
            raise codex_user_runner.CodexUserRunnerRejected(
                "CODEX_USER_RUNNER_DUPLICATE_REQUEST_ID",
                "existing Final Semantic result requires authoritative reconciliation",
            )
    started_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds")
    started_clock = time.perf_counter()
    with resolved_log.open("w", encoding="utf-8", newline="\n") as handle:
        # STORY_OS_V2_7_CODEX_USER_MODE_BRIDGE: one execution contract for every
        # critic lane. Direct when Story OS already runs as the interactive user,
        # otherwise the same declarative task is forwarded to the user-mode runner.
        done = codex_user_runner.run_model_codex(
            cmd,
            input=prompt.encode("utf-8"),
            stdout=handle,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
            task_type="critic",
            request_id=planned_request_id or None,
        )
    finished_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="milliseconds")
    duration_ms = max(0, int((time.perf_counter() - started_clock) * 1000))
    log_text = resolved_log.read_text(encoding="utf-8-sig", errors="replace")
    remote = dict(getattr(done, "remote", {}) or {})
    receipt_path = None
    if isinstance(model_execution_context, dict):
        context = dict(model_execution_context)
        context.pop("runner_request_id", None)
        episode = Path(context.pop("episode")).resolve()
        import logical_asset_identity
        import runtime_observability
        import runtime_trace

        call_id = planned_request_id or uuid.uuid4().hex
        trace_context = runtime_trace.current(episode) or {}
        selected_model = str(model or "").strip()
        effort = str(reasoning_effort or "").strip()
        policy_sha = str(context.pop("model_policy_sha256", "") or "").strip()
        policy_version = str(context.pop("model_policy_version", "") or "").strip()
        profile = str(context.pop("profile", "") or "").strip()
        role = str(context.pop("model_role", "") or "").strip()
        # This is an internal compatibility flag only. Final Semantic
        # authority is always provisional until the review lane validates its
        # durable result and candidate bindings.
        context.pop("defer_final_semantic_success", None)
        if not all((selected_model, effort, policy_sha, policy_version, profile, role)):
            raise ValueError("model execution context requires bound role/profile/model/effort/policy")
        durable_result_evidence = (
            _persist_final_semantic_durable_result(
                episode, remote, done.returncode, output_path=output_path,
            )
            if role == "vision.final" else {}
        )
        receipt = {
            "receipt_schema_version": 1,
            "episode_id": logical_asset_identity.episode_id(episode),
            "run_id": str(context.pop("run_id", "") or trace_context.get("run_id") or call_id),
            "trace_id": str(context.pop("trace_id", "") or trace_context.get("trace_id") or call_id),
            "step": role,
            "call_id": call_id,
            "model_role": role,
            "profile": profile,
            "requested_model": selected_model,
            "effective_model": selected_model,
            "reasoning_effort": effort,
            "model_policy_version": policy_version,
            "model_policy_sha256": policy_sha,
            "provider": "codex",
            "runner": "codex_user_runner",
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_ms": duration_ms,
            # Final Semantic success is not authoritative until the caller has
            # validated turn completion, durable output and the candidate's
            # review-item/generation bindings. Its receipt is finalized later.
            # A nonzero runner exit is a terminal *execution-call* failure;
            # it cannot remain pending independent semantic validation.
            # This does NOT attest Provider image Attempt failure or authorize
            # a retry. Successful Final Semantic calls still need full Review
            # Authority validation before recording SUCCESS.
            "status": ("FAILED" if int(done.returncode) != 0
                       else "PENDING_VALIDATION" if role == "vision.final"
                       else "SUCCESS"),
            "returncode": int(done.returncode),
            "runner_request_id": str(remote.get("request_id") or ""),
            "thread_id": str(remote.get("thread_id") or ""),
            "model_binding_source": "EPISODE_BOUND_POLICY",
            "effective_model_source": "EXPLICIT_RUNTIME_BINDING",
            **durable_result_evidence,
            **context,
        }
        receipt_file = runtime_observability.write_model_execution_receipt(episode, receipt=receipt)
        receipt_path = receipt_file.relative_to(Path(root).resolve()).as_posix()
        runtime_observability.safe_record_runtime_event(
            episode, "MODEL_EXECUTION", episode_id=receipt["episode_id"],
            run_id=receipt["run_id"], trace_id=receipt["trace_id"],
            step=role, call_id=call_id, model_role=role, profile=profile,
            requested_model=selected_model, effective_model=selected_model,
            reasoning_effort=effort, model_policy_version=policy_version,
            model_policy_sha256=policy_sha, provider="codex", runner="codex_user_runner",
            started_at=started_at, finished_at=finished_at, duration_ms=duration_ms,
            status=receipt["status"], effective_model_source="EXPLICIT_RUNTIME_BINDING",
            logical_asset_key=receipt.get("logical_asset_key"),
            attempt_index=receipt.get("attempt_index"), generation_key=receipt.get("generation_key"),
            source="codex_critic_runner", evidence_ref=receipt_path,
        )
    authorized_target = ((dispatch_authorization or {}).get("execution_target")
                         if dispatch_authorization else None)
    return LaunchResult(returncode=done.returncode, log_path=resolved_log,
                        log_text=log_text, output=log_text.encode("utf-8"),
                        remote=remote or None,
                        execution_target=dict(execution_target) if execution_target else None,
                        actual_dispatch_target=dict(execution_target) if execution_target else None,
                        scheduler_authorized_target=dict(authorized_target) if authorized_target else None,
                        router_proposed_target=dict(router_proposed_target) if router_proposed_target else None,
                        model_execution_receipt=receipt_path)


def parse_json_text(text):
    """Parse a critic JSON answer (stdout mode)."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("critic JSON root must be an object")
    return data


def parse_json_file(path):
    """Parse a critic JSON answer persisted with -o."""
    import story_json

    return story_json.read_json(path)


def recover_completed_agent_json(log_text: str) -> dict | None:
    """Recover a completed critic answer when Codex crashes after the answer.

    Fail closed: accept only a JSONL ``item.completed`` agent_message whose
    inner text is a JSON object and which is followed by ``turn.completed``.
    This deliberately rejects partial streaming output and pre-completion
    messages. The caller must still validate source hashes and the review schema.
    """
    last_agent: tuple[int, dict] | None = None
    completed_indexes: list[int] = []
    for index, raw in enumerate(str(log_text or "").splitlines()):
        try:
            event = json.loads(raw)
        except Exception:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "turn.completed":
            completed_indexes.append(index)
            continue
        item = event.get("item") if event.get("type") == "item.completed" else None
        if not isinstance(item, dict) or item.get("type") != "agent_message":
            continue
        text = item.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        try:
            payload = parse_json_text(text)
        except Exception:
            continue
        last_agent = (index, payload)
    if not last_agent:
        return None
    index, payload = last_agent
    if not any(done_index > index for done_index in completed_indexes):
        return None
    return payload


def self_test():
    import tempfile

    assert prefix(Path("codex.py")) == [sys.executable, "codex.py"]
    with tempfile.TemporaryDirectory(prefix="critic runner self test ") as td:
        root = Path(td)
        cmd = build_command(codex=Path("codex.exe"), root=root,
                            model="m", reasoning_effort="low",
                            attachments=[Path("a.png")],
                            output_path=Path("out.json"))
        assert "--skip-git-repo-check" in cmd and "--json" in cmd
        assert cmd[-1] == "-" and "-i" in cmd
        payload = {"summary": {"passed": True}}
        out = root / "out.json"
        out.write_text(json.dumps(payload), encoding="utf-8")
        assert parse_json_file(out) == payload
        assert parse_json_text(json.dumps(payload)) == payload
        recovered_log = "\n".join([
            json.dumps({"type":"item.completed","item":{"type":"agent_message","text":json.dumps(payload)}}),
            json.dumps({"type":"turn.completed","usage":{}}),
            "memory allocation failed",
        ])
        assert recover_completed_agent_json(recovered_log) == payload
        partial_log = json.dumps({"type":"item.completed","item":{"type":"agent_message","text":json.dumps(payload)}})
        assert recover_completed_agent_json(partial_log) is None
        try:
            parse_json_text("[1]")
            raise AssertionError("non-object JSON must be rejected")
        except ValueError:
            pass
    print("CODEX CRITIC RUNNER SELF-TEST PASS")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", default="self-test")
    args = ap.parse_args()
    if args.command == "self-test":
        self_test()
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
