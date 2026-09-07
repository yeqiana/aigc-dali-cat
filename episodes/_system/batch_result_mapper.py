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
    import tempfile
    from PIL import Image
    with tempfile.TemporaryDirectory(prefix="storyos-mapping-") as td:
        root=Path(td)
        contract={"planned_count":2,"frames":[{"output_index":i,"frame":str(i),"queue_item_id":str(i),"frame_contract_sha256":"test"} for i in (1,2)]}
        for i in (1,2): Image.new("RGB",(8,8)).save(root/f"out-{i:02d}.png")
        assert len(map_outputs(root,contract))==2
        (root/"out-02.png").unlink()
        try: map_outputs(root,contract)
        except BatchMappingError: pass
        else: raise AssertionError("missing output accepted")
        Image.new("RGB",(8,8)).save(root/"out-02.png")
        Image.new("RGB",(8,8)).save(root/"out-03.png")
        try: map_outputs(root,contract)
        except BatchMappingError: pass
        else: raise AssertionError("extra output accepted")
    print("BATCH RESULT MAPPER SELF-TEST PASS")
if __name__=="__main__": self_test()
