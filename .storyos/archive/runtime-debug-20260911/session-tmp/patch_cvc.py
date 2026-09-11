# -*- coding: utf-8 -*-
import json, io

EP = "episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/character-visual-contract.json"
with io.open(EP, "r", encoding="utf-8") as f:
    data = json.load(f)

m = data["members"]["P01"]
m["hair"]["haircut_anchor"] = "普通黑发，齐肩，低马尾，红绳简单扎起，发尾自然微翘"
m["hair"]["hair_length_anchor"] = "齐肩到锁骨长度，普通直发，不染不烫"
m["face_identity"]["identity_spec_locked"] = True
data["status"] = "LOCKED"

with io.open(EP, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("CVC LOCKED")
