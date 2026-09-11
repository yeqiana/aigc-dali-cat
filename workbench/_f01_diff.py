# -*- coding: utf-8 -*-
import os, sys, io, difflib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
BEFORE = os.path.join(EP, "meta/preimage-revisions/20260909_frame01_frontface/before")

mapping = [
    ("docs/03_婚礼前夜_20张正式分镜_V2.0.md", "docs/03_婚礼前夜_20张正式分镜_V2.0.md"),
    ("docs/04_婚礼前夜_视觉规范_V2.0.md", "docs/04_婚礼前夜_视觉规范_V2.0.md"),
    ("meta/story-gates.json", "meta/story-gates.json"),
    ("meta/shot-progression-review.json", "meta/shot-progression-review.json"),
    ("prompts/01.txt", "docs/prompts/reveal-order-v2/01.txt"),
]

def read(p):
    with open(p, 'rb') as f:
        return f.read().decode('utf-8', errors='replace')

for before_rel, cur_rel in mapping:
    a = read(os.path.join(BEFORE, before_rel)).splitlines()
    b = read(os.path.join(EP, cur_rel)).splitlines()
    print("=" * 20, cur_rel, "=" * 20)
    diff = list(difflib.unified_diff(a, b, 'BEFORE', 'CURRENT', lineterm='', n=2))
    if not diff:
        print("  (identical)")
    for line in diff:
        print(line)
