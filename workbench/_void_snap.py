import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
ep = r"episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉"
meta = os.path.join(ep, "meta")
for name in sorted(os.listdir(meta)):
    if "snapshot" in name or "final" in name:
        print("META FILE:", name)
snap = os.path.join(meta, "final-candidate-snapshot.json")
if os.path.exists(snap):
    d = json.load(open(snap, encoding="utf-8"))
    print("keys:", list(d.keys()))
    txt = json.dumps(d, ensure_ascii=False)
    print("mentions prompts/reveal-order-v2:", "reveal-order-v2" in txt)
    print("mentions contracts/frames:", "contracts/frames" in txt)
    print("mentions prompt-packages:", "prompt-packages" in txt)
    for k in ("created_at","verified_at","status","snapshot_sha256"):
        if k in d: print(k, "=", d[k])
    items = d.get("items") or d.get("files") or []
    print("item count:", len(items) if isinstance(items, list) else type(items))
    if isinstance(items, list):
        for it in items[:6]:
            print("  ", json.dumps(it, ensure_ascii=False)[:200])
