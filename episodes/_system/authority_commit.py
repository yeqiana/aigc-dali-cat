"""Single-writer, SHA-checked commits for shared Story OS authority documents."""
from __future__ import annotations
import copy, datetime as dt
import hashlib, json
from pathlib import Path
import runtime_atomic_store as atomic
import story_json

GATES=Path("meta/story-gates.json")
def sha(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
def sha_json_document(data):
    raw=(json.dumps(data,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def _now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def _append(ep: Path, row: dict):
    p=Path(ep)/"meta/runtime/authority-commit.jsonl"; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8",newline="\n") as h: h.write(json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n")

def _merge_scope(target: dict, scope: str, payload: dict, *, replace_existing_scopes: set[str] | None = None) -> None:
    parts=[x for x in str(scope).split(".") if x]
    if not parts: raise ValueError("empty authority patch scope")
    cursor=target
    for key in parts[:-1]:
        child=cursor.get(key)
        if child is None: child={}; cursor[key]=child
        if not isinstance(child,dict): raise ValueError(f"authority scope parent is not object: {scope}")
        cursor=child
    leaf=parts[-1]
    allowed=set(replace_existing_scopes or ())
    if leaf in cursor and scope not in allowed:
        raise ValueError(f"authority scope already populated: {scope}")
    cursor[leaf]=copy.deepcopy(payload)

def commit_transaction(ep: Path, authority_path: str | Path, *, expected_sha: str, snapshot_id: str,
                       task_ids: list[str], node_ids: list[str], patches: list[tuple[str,dict]],
                       candidate_paths: list[str], preview_validator=None, preflight_validator=None,
                       replace_existing_scopes: set[str] | None = None, authority_guard=None,
                       execution_contexts: list[dict] | None = None) -> dict:
    """Atomically commit an entire PREIMAGE authority preview or write nothing.

    The read/SHA comparison/preview validation/merge/replace critical section is
    protected by the existing runtime lock.  There is deliberately no
    per-patch replace in this path.

    ``authority_guard`` is an optional zero-argument predicate evaluated *inside*
    the lock; returning a false value aborts with STALE.  Callers whose binding
    authority is narrower than the whole file pass their projection check here so
    the ownership comparison cannot race the merge.  It must not take another
    lock: the runtime lock is an exclusive lock file and is not reentrant.
    """
    path=Path(ep)/Path(authority_path); started=_now(); contexts=list(execution_contexts or [])
    result={"status":"FAILED","snapshot_id":snapshot_id,"committed":False,"atomic":True,"partial_commit":False}
    commit_id=uuid4_hex()
    try:
        with atomic.FileLock(path):
            actual=sha(path)
            persistence=None
            if contexts:
                import preimage_execution_persistence as persistence
                replay_states=[]
                for ctx in contexts:
                    replay_states.append(persistence.replay_state(
                        Path(ep),snapshot_id=snapshot_id,idempotency_key=str(ctx["idempotency_key"]),
                        actual_authority_sha=actual))
                replay_codes={row.get("status") for row in replay_states}
                if "DIVERGED" in replay_codes:
                    result={**result,"status":"INELIGIBLE","input_sha":actual,"reason":"execution receipt diverged from authority"}
                elif replay_codes and replay_codes.issubset({"REPLAYED","REPLAYED_RECOVERED"}):
                    result={**result,"status":"REPLAYED","committed":False,"replayed":True,"input_sha":actual,"output_sha":actual}
                elif replay_codes.intersection({"REPLAYED","REPLAYED_RECOVERED"}):
                    result={**result,"status":"INELIGIBLE","input_sha":actual,"reason":"partial execution receipt replay set"}
                else:
                    for ctx in contexts:
                        state=persistence.eligibility(
                            Path(ep),snapshot_id=snapshot_id,task_id=str(ctx["task_id"]),
                            execution_id=str(ctx["execution_id"]),attempt=int(ctx["attempt"]),
                            idempotency_key=str(ctx["idempotency_key"]))
                        if not state.get("eligible"):
                            result={**result,"status":"INELIGIBLE","input_sha":actual,
                                    "reason":f"execution not eligible: {ctx['task_id']}:{state.get('status')}"}
                            break
            if result["status"] not in {"FAILED"}:
                pass
            elif actual != expected_sha:
                result={**result,"status":"STALE","input_sha":actual}
            elif authority_guard is not None and not authority_guard():
                result={**result,"status":"STALE","input_sha":actual,"reason":"authority guard rejected"}
            else:
                current=atomic.read_json(path,{})
                if not isinstance(current,dict): raise ValueError("authority must be a JSON object")
                errors=list(preflight_validator() or []) if preflight_validator else []
                preview=copy.deepcopy(current)
                if not errors:
                    allowed_replacements=set(replace_existing_scopes or ())
                    declared_scopes={scope for scope,_ in patches}
                    unknown=allowed_replacements-declared_scopes
                    if unknown:
                        raise ValueError("replacement scope not present in transaction patches: " + ", ".join(sorted(unknown)))
                    for scope,payload in patches:
                        _merge_scope(preview,scope,payload,replace_existing_scopes=allowed_replacements)
                if not errors:
                    errors=list(preview_validator(preview) or []) if preview_validator else []
                if errors:
                    result={**result,"status":"FAILED","reason":"; ".join(errors),"input_sha":actual}
                else:
                    planned_output_sha=sha_json_document(preview)
                    if contexts and persistence is not None:
                        for ctx in contexts:
                            persistence.prepare_commit(
                                Path(ep),snapshot_id=snapshot_id,task_id=str(ctx["task_id"]),
                                execution_id=str(ctx["execution_id"]),attempt=int(ctx["attempt"]),
                                idempotency_key=str(ctx["idempotency_key"]),input_sha=actual,
                                output_sha=planned_output_sha)
                    atomic.atomic_write_json(path,preview)
                    written_sha=sha(path)
                    if written_sha != planned_output_sha:
                        raise RuntimeError("authority atomic write SHA does not match prepared commit receipt")
                    if contexts and persistence is not None:
                        for ctx in contexts:
                            persistence.mark_committed(
                                Path(ep),snapshot_id=snapshot_id,task_id=str(ctx["task_id"]),
                                execution_id=str(ctx["execution_id"]),commit_id=commit_id)
                    result={**result,"status":"PASS","committed":True,"input_sha":actual,"output_sha":written_sha}
    except Exception as exc:
        result={**result,"status":"FAILED","error":str(exc)}
    _append(ep,{"commit_id":commit_id,"transaction_type":"PREIMAGE_AUTHORITY_COMMIT","snapshot_id":snapshot_id,
        "task_ids":list(task_ids),"node_ids":list(node_ids),"expected_sha":expected_sha,"input_sha":result.get("input_sha"),
        "output_sha":result.get("output_sha"),"patch_scopes":[scope for scope,_ in patches],"candidate_paths":list(candidate_paths),
        "status":result["status"],"started_at":started,"finished_at":_now(),"atomic":True,"partial_commit":False,
        "replace_existing_scopes":sorted(replace_existing_scopes or ()),
        "execution_ids":[str(ctx.get("execution_id")) for ctx in contexts],
        "idempotency_keys":[str(ctx.get("idempotency_key")) for ctx in contexts],
        "replayed":bool(result.get("replayed"))})
    return result

def commit_patch(ep: Path, authority_path: str | Path, patch_scope: str, payload: dict, *, expected_sha: str, snapshot_id: str, node_id: str):
    """Compare/merge/replace under one lock.  ``patch_scope`` is a dotted path."""
    path=Path(ep)/Path(authority_path)
    started=_now(); result={"status":"FAILED","snapshot_id":snapshot_id,"committed":False}
    def mutate(current):
        nonlocal result
        if sha(path)!=expected_sha:
            result={"status":"STALE","snapshot_id":snapshot_id,"committed":False}; return result
        target=current
        parts=[x for x in str(patch_scope).split(".") if x]
        for key in parts[:-1]: target=target.setdefault(key,{})
        leaf=parts[-1] if parts else "payload"
        if leaf in target: raise ValueError(f"authority scope already populated: {patch_scope}")
        target[leaf]=dict(payload)
        result={"status":"PASS","snapshot_id":snapshot_id,"committed":True,"output_sha":None}
        return result
    try:
        atomic.update_json(path,lambda:{},mutate)
        if result["status"]=="PASS": result["output_sha"]=sha(path)
    except Exception as exc:
        result={"status":"FAILED","snapshot_id":snapshot_id,"committed":False,"error":str(exc)}
    _append(ep,{"commit_id":uuid4_hex(),"snapshot_id":snapshot_id,"node_ids":[node_id],"expected_sha":expected_sha,
                "input_sha":expected_sha,"output_sha":result.get("output_sha"),"patch_scopes":[patch_scope],"status":result["status"],"started_at":started,"finished_at":_now()})
    return result

def uuid4_hex():
    import uuid
    return uuid.uuid4().hex

def commit_visual_patch(ep: Path, patch: dict, *, expected_sha: str, snapshot_id: str):
    # Compatibility for the older "merge visual object" public helper.
    path=Path(ep)/GATES
    result={"status":"FAILED","snapshot_id":snapshot_id,"committed":False}
    def mutate(current):
        nonlocal result
        if sha(path)!=expected_sha:
            result={"status":"STALE","snapshot_id":snapshot_id,"committed":False}; return result
        current.setdefault("visual",{}).update(dict(patch))
        result={"status":"PASS","snapshot_id":snapshot_id,"committed":True}; return result
    atomic.update_json(path,lambda:{},mutate)
    if result["status"]=="PASS": result["output_sha"]=sha(path)
    return result
