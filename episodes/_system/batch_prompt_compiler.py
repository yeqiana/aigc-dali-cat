#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import batch_contract
import frame_contract
import prompt_package
from visual_profile_bridge_v224 import compile_prompt_contract

ROOT=Path(__file__).resolve().parents[2]

def compile_batch(ep:Path,contract:dict,items_by_id:dict,*,model:str,quality:str,size:str,reference_names:list[str])->dict:
    visual=compile_prompt_contract(ep)
    blocks=[]
    package_rows=[]
    for row in contract["frames"]:
        item=items_by_id[row["queue_item_id"]]
        frame=int(row["frame"])
        prompt_path=(ROOT/item["prompt_file"]).resolve()
        scene=prompt_path.read_text(encoding="utf-8").strip()
        if not scene: raise ValueError(f"frame {frame:02d} prompt empty")
        compiled=frame_contract.compile_frame(ep,frame,write_cache=True)
        package=prompt_package.compile_frame(ep,frame,prompt_path,write=True)
        package_rows.append({
            "frame":f"{frame:02d}",
            "package_sha256":package["package_sha256"],
            "frame_contract_sha256":package["frame_contract_sha256"],
        })
        blocks.append(
            f'<frame output_index="{int(row["output_index"])}" frame="{frame:02d}">\n'
            f'<frame_contract>\n{compiled["prompt_contract"]}\n</frame_contract>\n'
            f'<scene>\n{scene}\n</scene>\n'
            f'</frame>'
        )
    refs="\n".join(f"- {x}" for x in reference_names) or "- no shared references"
    count=int(contract["planned_count"])
    text=f"""You are Story OS V2.4 Batch Image Worker.
This is ONE batch request containing {count} independent Story OS frames.

HARD TOOL RULE:
- Call image_generation exactly ONCE total.
- In that single tool call request exactly {count} images (n={count} if the tool exposes n/count).
- NEVER call image_generation once per frame.
- If one tool call cannot return exactly {count} images, fail instead of silently issuing extra calls.

IMAGE MODEL CONTRACT:
model={model}
quality={quality}
canvas={size}
Do not silently substitute model, quality, or aspect ratio.

OUTPUT MAPPING CONTRACT:
- image 1 -> frame {contract["frames"][0]["frame"]}
- continue strictly by output_index.
- Save/copy the returned generated candidates as:
""" + "\n".join(f"  out-{int(r['output_index']):02d}.png -> frame {r['frame']}" for r in contract["frames"]) + f"""

All {count} out-XX.png files must exist before you reply.
Do not create images with Python.
Do not reuse cached images.
Do not make a contact sheet or collage.
Each output file is one full standalone Story OS frame.

Shared reference files:
{refs}

<visual_contract>
{visual["text"]}
</visual_contract>

""" + "\n\n".join(blocks)
    return {
        "text":text,
        "packages":package_rows,
        "visual_profile":{
            "profile_id":visual["profile_id"],
            "profile_path":visual["profile_path"],
            "profile_sha256":visual["profile_sha256"],
            "capture_profile":visual["capture_profile"],
        },
    }
