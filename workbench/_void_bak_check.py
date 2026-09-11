import os, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
ep = r"episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉"
d = os.path.join(ep, "docs", "prompts", "reveal-order-v2")
for name in sorted(os.listdir(d)):
    p = os.path.join(d, name)
    if not os.path.isfile(p): continue
    raw = open(p, "rb").read()
    txt = open(p, encoding="utf-8-sig").read().strip()
    h = hashlib.sha256(txt.encode("utf-8")).hexdigest()
    print(f"{name}: bytes={len(raw)} chars={len(txt)} prompt_sha={h}")
    if name != "01.txt":
        print("   ---- content ----")
        print(txt)
        print("   -----------------")
