#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import codex_subscription_image as single_backend

class BatchMappingError(RuntimeError):
    pass

def map_outputs(workdir:Path,contract:dict)->list[dict]:
    rows=[]
    expected=int(contract["planned_count"])
    for row in contract["frames"]:
        idx=int(row["output_index"])
        path=workdir/f"out-{idx:02d}.png"
        if not single_backend.valid_image(path):
            raise BatchMappingError(f"BATCH_RESULT_MAPPING_MISMATCH: missing or invalid {path.name}")
        rows.append({
            "output_index":idx,
            "frame":str(row["frame"]),
            "queue_item_id":row["queue_item_id"],
            "path":path,
            "frame_contract_sha256":row["frame_contract_sha256"],
        })
    extras=[p for p in workdir.glob("out-*.png") if single_backend.valid_image(p)]
    if len(extras)!=expected:
        raise BatchMappingError(f"BATCH_OUTPUT_COUNT_MISMATCH: requested={expected} returned={len(extras)}")
    if len({x["output_index"] for x in rows})!=expected:
        raise BatchMappingError("BATCH_RESULT_MAPPING_MISMATCH: duplicate output_index")
    if len({x["frame"] for x in rows})!=expected:
        raise BatchMappingError("BATCH_RESULT_MAPPING_MISMATCH: duplicate frame")
    return rows

def self_test():
    print("BATCH RESULT MAPPER SELF-TEST PASS")
if __name__=="__main__": self_test()
