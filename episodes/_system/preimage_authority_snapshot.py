"""SHA-bound preimage authority snapshot; evidence only, never a stage or Gate."""
from __future__ import annotations
import datetime as dt, hashlib, json
from pathlib import Path
import runtime_request
import story_json

REL=Path("meta/runtime/preimage-authority-snapshot.json")
PATHS={"story_gates":"meta/story-gates.json","character_contract":"meta/character-contract.json",
       "world_identity":"meta/world-identity.json"}
def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
def _json_sha(value): return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def owned_scopes() -> tuple[str,...]:
    """The authority scopes the PREIMAGE tasks own; single-sourced from the task contract.

    ``preimage_task_contract.TASK_SPECS`` is the one declaration of ownership, so the
    staleness projection can never drift wider than what the tasks may rewrite.
    """
    import preimage_task_contract as tasks
    out=[]
    for spec in tasks.TASK_SPECS.values():
        for scope in spec.get("scope") or ():
            if scope not in out: out.append(scope)
    return tuple(out)
def _scope_value(gates: dict, scope: str):
    """Mirror ``authority_commit._merge_scope`` path semantics; missing -> None."""
    cursor=gates
    for key in [x for x in str(scope).split(".") if x]:
        if not isinstance(cursor,dict) or key not in cursor: return None
        cursor=cursor[key]
    return cursor
def _common(ep: Path, gates: dict | None = None) -> dict:
    ep=Path(ep)
    out={key:sha(ep/rel) for key,rel in PATHS.items() if key != "story_gates"}
    request_path=ep/"meta/runtime-request.json"
    request_data=story_json.read_json(request_path,default={}) if request_path.is_file() else {}
    out["runtime_request_preimage"]=runtime_request.preimage_authority_projection_sha256(request_data)
    if gates is None:
        gates=story_json.read_json(ep/"meta/story-gates.json",default={}) or {}
    out["story_lock"]=_json_sha(gates.get("story") or {})
    profile=(gates.get("visual_profile") or {})
    path=profile.get("profile_path") or profile.get("path")
    out["visual_profile"]=sha((Path(__file__).resolve().parents[2]/str(path))) if path else None
    return out
def hashes(ep: Path):
    """Whole-file projection. Kept broad on purpose: ``frame_contract`` binds per-frame
    contracts to scopes outside PREIMAGE ownership too, so narrowing this would let a
    mixed frame index ship."""
    ep=Path(ep); out={"story_gates":sha(ep/PATHS["story_gates"])}
    out.update(_common(ep)); return out
def owned_hashes(ep: Path):
    """Ownership projection. ``story_gates`` becomes one hash per owned scope, so a
    write to a non-owned scope (e.g. ``visual.calibration``) leaves this unchanged."""
    ep=Path(ep)
    gates=story_json.read_json(ep/"meta/story-gates.json",default={}) or {}
    out={"owned_scopes":{scope:_json_sha(_scope_value(gates,scope)) for scope in owned_scopes()}}
    out.update(_common(ep,gates)); return out
def build(ep: Path, *, write=True, kind="PREIMAGE_INPUT_SNAPSHOT"):
    ep=Path(ep)
    values=owned_hashes(ep); sid=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()
    row={"schema_version":1,"snapshot_id":sid,"snapshot_kind":kind,"created_at":now(),"authority_sha256":values,
         "whole_authority_sha256":hashes(ep),
         "derived_execution_evidence":True,"episode_state_mutated":False,"gate_pass":None}
    if write:
        story_json.write_json(ep/REL,row)
        if kind == "PREIMAGE_COMMITTED_SNAPSHOT":
            story_json.write_json(ep/"meta/runtime/preimage-committed-snapshot.json",row)
    return row
def _recorded(snapshot: dict) -> dict:
    """Whole-file projection recorded by this row; legacy rows stored it directly."""
    row=snapshot or {}
    recorded=row.get("whole_authority_sha256")
    if isinstance(recorded,dict) and recorded: return recorded
    return row.get("authority_sha256") or {}
def _migration_evidence_valid(ep: Path, projection_sha: str) -> bool:
    ep=Path(ep)
    evidence=story_json.read_json(ep/"meta/runtime/image-model-migration.json",default={}) or {}
    request_data=story_json.read_json(ep/"meta/runtime-request.json",default={}) or {}
    migration=(request_data.get("provenance") or {}).get("image_model_migration") or {}
    return bool(
        evidence.get("preimage_authority_preserved") is True
        and str(evidence.get("preimage_authority_projection_sha256") or "")==str(projection_sha or "")
        and str(evidence.get("request_id") or "")==str(request_data.get("request_id") or "")
        and str(evidence.get("from") or "")==str(migration.get("from") or "")
        and str(evidence.get("to") or "")==str(migration.get("to") or "")
        and str(evidence.get("source_request_id") or "")==str(migration.get("source_request_id") or "")
    )


def _equivalent_after_model_migration(ep: Path, current: dict, recorded: dict) -> bool:
    """Compatibility for snapshots created before Runtime Request projection hashes.

    Every non-Runtime-Request authority hash must still match. The old full-file
    runtime_request hash may differ only when a canonical image-model migration
    proves the PREIMAGE creative projection is unchanged.
    """
    cur=dict(current or {}); old=dict(recorded or {})
    projection=str(cur.pop("runtime_request_preimage", "") or "")
    legacy=old.pop("runtime_request", None)
    if not projection or not legacy:
        return False
    return cur==old and _migration_evidence_valid(ep,projection)


def stale(ep: Path, snapshot: dict):
    current=hashes(ep); recorded=_recorded(snapshot)
    return current!=recorded and not _equivalent_after_model_migration(ep,current,recorded)

def stale_owned(ep: Path, snapshot: dict):
    current=owned_hashes(ep); recorded=(snapshot or {}).get("authority_sha256") or {}
    return current!=recorded and not _equivalent_after_model_migration(ep,current,recorded)
