"""SHA-bound preimage authority snapshot; evidence only, never a stage or Gate."""
from __future__ import annotations
import datetime as dt, hashlib, json
from pathlib import Path
import story_json

REL=Path("meta/runtime/preimage-authority-snapshot.json")
PATHS={"story_gates":"meta/story-gates.json","character_contract":"meta/character-contract.json",
       "world_identity":"meta/world-identity.json","runtime_request":"meta/runtime-request.json"}
def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
def hashes(ep: Path):
    ep=Path(ep); out={key:sha(ep/rel) for key,rel in PATHS.items()}
    gates=story_json.read_json(ep/"meta/story-gates.json",default={}) or {}
    out["story_lock"]=hashlib.sha256(json.dumps(gates.get("story") or {},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    profile=(gates.get("visual_profile") or {})
    path=profile.get("profile_path") or profile.get("path")
    out["visual_profile"]=sha((Path(__file__).resolve().parents[2]/str(path))) if path else None
    return out
def build(ep: Path, *, write=True, kind="PREIMAGE_INPUT_SNAPSHOT"):
    values=hashes(ep); sid=hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()
    row={"schema_version":1,"snapshot_id":sid,"snapshot_kind":kind,"created_at":now(),"authority_sha256":values,
         "derived_execution_evidence":True,"episode_state_mutated":False,"gate_pass":None}
    if write:
        story_json.write_json(Path(ep)/REL,row)
        if kind == "PREIMAGE_COMMITTED_SNAPSHOT":
            story_json.write_json(Path(ep)/"meta/runtime/preimage-committed-snapshot.json",row)
    return row
def stale(ep: Path, snapshot: dict): return hashes(ep)!=(snapshot.get("authority_sha256") or {})
