#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

import frame_contract
import prompt_package
from visual_profile_bridge_v224 import compile_prompt_contract

ROOT=Path(__file__).resolve().parents[2]
MAX_PROMPT_CHARS=32000

def compile_batch(ep:Path,contract:dict,items_by_id:dict,*,model:str,quality:str,size:str,reference_names:list[str])->dict:
    visual=compile_prompt_contract(ep)
    slots=[]
    packages=[]
    for row in contract["frames"]:
        item=items_by_id[row["queue_item_id"]]
        frame=int(row["frame"])
        prompt_path=(ROOT/item["prompt_file"]).resolve()
        scene=prompt_path.read_text(encoding="utf-8").strip()
        if not scene:
            raise ValueError(f"frame {frame:02d} prompt empty")
        resolved=frame_contract.compile_frame(ep,frame,write_cache=True)
        package=prompt_package.compile_frame(ep,frame,prompt_path,write=True)
        packages.append({
            "frame":f"{frame:02d}",
            "package_sha256":package["package_sha256"],
            "frame_contract_sha256":package["frame_contract_sha256"],
        })
        slots.append(
            f"<image_slot index=\"{int(row['output_index'])}\" frame=\"{frame:02d}\">\n"
            f"<frame_contract>\n{resolved['prompt_contract']}\n</frame_contract>\n"
            f"<scene>\n{scene}\n</scene>\n"
            f"</image_slot>"
        )
    refs="\n".join(f"- {x}" for x in reference_names) or "- no reference images"
    count=int(contract["planned_count"])
    text=f"""Create exactly {count} separate standalone images as one ordered generation set.

OUTPUT SLOT CONTRACT:
- Return exactly {count} images.
- Output image 1 must depict only image_slot 1.
- Output image 2 must depict only image_slot 2, and so on in order.
- Do not combine slots into one image.
- Do not create contact sheets, grids, collages, split screens, storyboards, captions, labels, or visible slot numbers.
- Each returned image is a full standalone photograph.
- Keep shared character/location/capture identity consistent across the set where the contracts require continuity.
- The visual and frame contracts are mandatory; do not turn them into visible text.

MODEL/OUTPUT INTENT:
model={model}
quality={quality}
requested_story_canvas={size}

Shared reference images:
{refs}

<shared_visual_contract>
{visual["text"]}
</shared_visual_contract>

""" + "\n\n".join(slots)
    if len(text)>MAX_PROMPT_CHARS:
        raise ValueError(
            f"OPENAI_BATCH_PROMPT_TOO_LONG: {len(text)} chars > {MAX_PROMPT_CHARS}; "
            "fall back to per-frame generation instead of truncating Frame Contract authority."
        )
    return {
        "text":text,
        "packages":packages,
        "visual_profile":{
            "profile_id":visual["profile_id"],
            "profile_path":visual["profile_path"],
            "profile_sha256":visual["profile_sha256"],
            "capture_profile":visual["capture_profile"],
        },
        "prompt_chars":len(text),
        "mapping_contract":"output_index_to_frame_requires_review",
    }
