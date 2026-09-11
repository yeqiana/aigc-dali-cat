# -*- coding: utf-8 -*-
import json, io

EP = "episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/shot-progression-review.json"
with io.open(EP, "r", encoding="utf-8") as f:
    data = json.load(f)
frames = {row["frame"]: row for row in data["frames"]}

def setf(frame, **kw):
    r = frames[frame]
    for k, v in kw.items():
        r[k] = v

# Repair shot_scale distribution (no >2 consecutive, >=3 distinct, large+small present)
setf("01", shot_scale="medium")
setf("02", shot_scale="close")
setf("03", shot_scale="wide")
setf("04", shot_scale="close")
setf("05", shot_scale="detail")
setf("06", shot_scale="wide")
setf("07", shot_scale="medium")
setf("08", shot_scale="detail")
setf("09", shot_scale="close")
setf("10", shot_scale="detail")
setf("11", shot_scale="medium")
setf("12", shot_scale="wide")
setf("13", shot_scale="close")
setf("14", shot_scale="detail")
setf("15", shot_scale="medium")
setf("16", shot_scale="extreme_wide")
setf("17", shot_scale="medium")
setf("18", shot_scale="close")
setf("19", shot_scale="wide")
setf("20", shot_scale="close")

# response_sync for human_present frames must not be not_applicable
setf("01", response_sync="single_subject")
# keep others already asynchronous; frame 01 was not_applicable

# human_action_stage after first confirmation (frame 04) to avoid passive stall
setf("04", hstage="verify")
setf("05", hstage="verify")
setf("06", hstage="move")
setf("07", hstage="verify")
setf("08", hstage="verify")

# cinematic reference genre_fit: only NEGATIVE_SPACE_SUSPENSE / FRAME_WITHIN_FRAME for general_reality_crack
setf("08", ref_id="FRAME_WITHIN_FRAME",
     ref_tech="用真实镜框把陌生母亲脸框在第二层信息区，反射亮度略低于实景，仍是P01镜前可拍到的近贴画面")
setf("12", ref_id="FRAME_WITHIN_FRAME",
     ref_tech="用门缝与车灯把货车里的同款嫁衣女孩框在后景小区域，车灯扫过才透出信息")
setf("13", ref_id="NEGATIVE_SPACE_SUSPENSE",
     ref_tech="把拿药走近的他偏置到一侧，另一侧留作门缝阴影负空间，仍是门口对峙可拍到的画面")
setf("16", ref_id="FRAME_WITHIN_FRAME",
     ref_tech="用后门框和车灯把院门红字与田埂框住，她回头时在框内透出")

# lighting suspense_function must be non-none for anomaly frames
setf("17", suspense="reveal_partial_information")
setf("20", suspense="create_negative_space")

# interaction: frame 01 human_present true + single_subject, keep type none meaningful false
frames["01"]["interaction"] = {"type": "none", "actor": "", "target": "", "action": "", "meaningful": False}
frames["01"]["emotion"] = {"state": "ordinary", "intensity": 0, "trigger": "", "response_sync": "single_subject"}

for row in data["frames"]:
    # apply frame key fields
    pass

with io.open(EP, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("PATCHED SHOT PROGRESSION")
