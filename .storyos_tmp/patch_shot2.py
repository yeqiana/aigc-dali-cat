# -*- coding: utf-8 -*-
import json, io

EP = "episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/shot-progression-review.json"
with io.open(EP, "r", encoding="utf-8") as f:
    data = json.load(f)
frames = {row["frame"]: row for row in data["frames"]}

def frame(row, **kw):
    for k, v in kw.items():
        row[k] = v

def cin_ref(row, rid, tech):
    row["cinematic_reference"] = {"reference_id": rid, "technique_translation": tech, "exact_shot_recreation": False}

def light(row, src, contrast, suspense):
    row["lighting_design"] = {"practical_source": src, "contrast_mode": contrast, "suspense_function": suspense, "physically_motivated": True, "invented_cinematic_light": False}

def emotion(row, state, intensity, trigger, sync):
    row["emotion"] = {"state": state, "intensity": intensity, "trigger": trigger, "response_sync": sync}

# shot_scale distribution
for f_, s in [("01","medium"),("02","close"),("03","wide"),("04","close"),("05","detail"),
              ("06","wide"),("07","medium"),("08","detail"),("09","close"),("10","detail"),
              ("11","medium"),("12","wide"),("13","close"),("14","detail"),("15","medium"),
              ("16","extreme_wide"),("17","medium"),("18","close"),("19","wide"),("20","close")]:
    frame(frames[f_], shot_scale=s)

# response_sync + emotion frame 01
emotion(frames["01"], "ordinary", 0, "", "single_subject")
frames["01"]["interaction"] = {"type": "none", "actor": "", "target": "", "action": "", "meaningful": False}

# human_action_stage to avoid passive stall after confirmation (frame04)
frame(frames["04"], human_action_stage="verify")
frame(frames["05"], human_action_stage="verify")
frame(frames["06"], human_action_stage="move")
frame(frames["07"], human_action_stage="verify")
frame(frames["08"], human_action_stage="verify")

# cinematic reference genre_fit -> only FRAME_WITHIN_FRAME / NEGATIVE_SPACE_SUSPENSE for general_reality_crack
cin_ref(frames["08"], "FRAME_WITHIN_FRAME", "用真实镜框把陌生母亲脸框在第二层信息区，反射亮度略低于实景，仍是P01镜前可拍到的近贴画面")
cin_ref(frames["12"], "FRAME_WITHIN_FRAME", "用门缝与车灯把货车里的同款嫁衣女孩框在后景小区域，车灯扫过才透出信息")
cin_ref(frames["13"], "NEGATIVE_SPACE_SUSPENSE", "把拿药走近的他偏置到一侧，另一侧留作门缝阴影负空间，仍是门口对峙可拍到的画面")
cin_ref(frames["16"], "FRAME_WITHIN_FRAME", "用后门框和车灯把院门红字与田埂框住，她回头时在框内透出")

# lighting suspense_function for anomaly frames non-none
light(frames["17"], "fluorescent", "flat_natural", "reveal_partial_information")
light(frames["20"], "window_light", "flat_natural", "create_negative_space")
# frame 12 already vehicle_headlight/backlit/hide_information; frame 16 vehicle_headlight/backlit/separate (ok)
# frame 17/20 keep practical source but change suspense

with io.open(EP, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("PATCHED SHOT PROGRESSION 2")
