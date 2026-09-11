import json, os, sys, hashlib, glob
sys.stdout.reconfigure(encoding='utf-8')
ep = r"episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉"
TARGET_01D = "3745e670aa18dadbcb10588ef4b9369ebdd608accdd3f04ba5fac86594e7ab94"
CUR_01E  = "95c594c338d3a3d14fdea04271a4f502a2b2db04c5292c117300807bad8e1302"
def sh(t): return hashlib.sha256(t.encode("utf-8")).hexdigest()
def show(name, text):
    t = text.strip()
    tag = ""
    h = sh(t)
    if h == TARGET_01D: tag = "  <<< MATCH 01d (locked asset prompt)"
    elif h == CUR_01E: tag = "  <<< MATCH 01e (voided closeup)"
    print(f"[{name}] chars={len(t)} bytes={len(t.encode())} sha={h[:16]}{tag}")
# 1. current prompt file
p = os.path.join(ep, "docs", "prompts", "reveal-order-v2", "01.txt")
show("current 01.txt", open(p, encoding="utf-8-sig").read())
# 2. workbench candidates
for cand in ("workbench\\_new_prompt_01.txt",):
    if os.path.exists(cand):
        show(cand, open(cand, encoding="utf-8-sig").read())
        print("   content:", open(cand, encoding="utf-8-sig").read().strip()[:300].replace("\n","\\n"))
# 3. prompt package (derived cache)
pp = os.path.join(ep, "meta", "runtime", "prompt-packages", "01.json")
if os.path.exists(pp):
    d = json.load(open(pp, encoding="utf-8"))
    show("prompt-package 01.json", d.get("scene_prompt",""))
# 4. worker jsonl logs mentioning scene prompt
for f in sorted(glob.glob(os.path.join(ep, "meta", "image-workers", "01-*.jsonl"))):
    txt = open(f, encoding="utf-8", errors="replace").read()
    print(f"--- {os.path.basename(f)} len={len(txt)}")
    for line in txt.splitlines():
        if "scene" in line.lower() and len(line) > 200:
            try: obj = json.loads(line)
            except Exception: continue
            s = json.dumps(obj, ensure_ascii=False)
            idx = s.find("P01")
            if idx >= 0:
                print("    fragment:", s[idx:idx+320])
