
import json, os, shutil, datetime
ep = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
src = os.path.join(ep, "docs/prompts/reveal-order-v2/01.txt")
bak = src + ".bak_pre_face_closeup"
if not os.path.exists(bak):
    shutil.copy2(src, bak)
    print("backup ->", bak)
p = os.path.join(ep, "docs/prompts/reveal-order-v2/01.txt")
new = open(r"workbench/_new_prompt_01.txt", encoding="utf-8").read()
open(p, "w", encoding="utf-8", newline="\n").write(new)
txt = open(p, encoding="utf-8").read()
body = [l for l in txt.splitlines() if l.strip()]
first = body[0] if body else ""
print("chars_total", len(txt), "bytes_total", len(txt.encode("utf-8")))
print("chars_firstline", len(first), "bytes_firstline", len(first.encode("utf-8")))

