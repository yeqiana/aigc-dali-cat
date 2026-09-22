# -*- coding: utf-8 -*-
import yaml, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
EP = r"D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
old = yaml.safe_load(open(EP + "/meta/subtitles.v2.0-pre-optimization.yaml", encoding="utf-8"))["frames"]
new = yaml.safe_load(open(EP + "/meta/subtitles.yaml", encoding="utf-8"))["frames"]
print("old frames:", len(old), "| new frames:", len(new))
for f in sorted(set(old) | set(new), key=int):
    a, b = str(old.get(f, "")), str(new.get(f, ""))
    if a != b:
        print("==", f)
        print("  OLD:", a)
        print("  NEW:", b)
