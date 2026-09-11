# -*- coding: utf-8 -*-
"""Audit: has current files been modified vs preimage-revisions frame01_frontface/before?"""
import hashlib, os, sys, json, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
BEFORE = os.path.join(EP, "meta/preimage-revisions/20260909_frame01_frontface/before")

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()[:16]

mapping = [
    ("docs/03_婚礼前夜_20张正式分镜_V2.0.md", "docs/03_婚礼前夜_20张正式分镜_V2.0.md"),
    ("docs/04_婚礼前夜_视觉规范_V2.0.md", "docs/04_婚礼前夜_视觉规范_V2.0.md"),
    ("meta/shot-progression-review.json", "meta/shot-progression-review.json"),
    ("meta/story-gates.json", "meta/story-gates.json"),
    ("prompts/01.txt", "docs/prompts/reveal-order-v2/01.txt"),
]

for before_rel, cur_rel in mapping:
    b = os.path.join(BEFORE, before_rel)
    c = os.path.join(EP, cur_rel)
    if not os.path.exists(b):
        print("BEFORE-MISSING:", before_rel)
        continue
    if not os.path.exists(c):
        print("CURRENT-MISSING:", cur_rel)
        continue
    hb, hc = sha(b), sha(c)
    print(("DIFF" if hb != hc else "SAME"), cur_rel, hb[:12], hc[:12])
