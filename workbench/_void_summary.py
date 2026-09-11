import json, sys, hashlib, os, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat")
EP = ROOT/"episodes"/"09_旧物怪谈"/"05_婚礼前夜_记忆麻醉"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1<<20), b""): h.update(b)
    return h.hexdigest()
def row(label, p, expect=None):
    s = sha(p) if Path(p).is_file() else "<missing>"
    mark = ""
    if expect: mark = "  [UNCHANGED]" if s == expect else "  [!! DIFFERS]"
    print(f"{label:38s} {s}{mark}")
    return s
print("--- publish assets (must be untouched) ---")
row("approved/01.png (locked candidate)", EP/"media"/"approved"/"01.png", "cef5b7b929e12b720b6becdbfcded43d3b0f34d0a2f82070741097af5fd812f6")
row("production/publish/01.png (body 01)", EP/"production"/"publish"/"01.png", "fb8f99e147fc427feadce4c4946aa2bcbf2a169262bcdf29c6dbbf8dd0efeee5")
row("production/cover/cover.png", EP/"production"/"cover"/"cover.png", "adeea84ec2aa4b1b4f4a7ee3a2e5bef9e5a9be0e0fbd2e5b7f1f0d25b3ec8ab0") if False else None
cov = EP/"production"/"cover"/"cover.png"
print(f"{'production/cover/cover.png':38s} {sha(cov)}")
print("--- derived evidence (rebuilt after the void) ---")
print(f"{'final-candidate-snapshot.json':38s} {sha(EP/'meta'/'final-candidate-snapshot.json')}")
snap = json.loads((EP/"meta"/"final-candidate-snapshot.json").read_text(encoding="utf-8"))
print("  snapshot_sha256:", snap["snapshot_sha256"], "| built_at:", snap["built_at"])
print(f"{'delegated-release.json':38s} {sha(EP/'meta'/'delegated-release.json')}")
rep = json.loads((EP/"meta"/"delegated-release.json").read_text(encoding="utf-8"))
pk = rep["package"]
zp = ROOT/pk["path"]
print("  package:", pk["path"])
print("  package sha256:", pk["sha256"])
print("  package bytes :", pk["bytes"], "| on-disk:", zp.stat().st_size, "| sha match:", sha(zp) == pk["sha256"])
print("--- ledger / queue ---")
led = json.loads((EP/"meta"/"production-ledger.json").read_text(encoding="utf-8"))
f1 = led["frames"]["01"]
print("  frame 01:", f1["status"], "| lock sha:", f1["lock"]["sha256"][:16], "| lock at:", f1["lock"]["at"])
print("  frames by status:", {s: sum(1 for f in led["frames"].values() if f.get("status")==s) for s in {f.get("status") for f in led["frames"].values()}})
q = json.loads((EP/"meta"/"production-queue.json").read_text(encoding="utf-8"))
from collections import Counter
print("  queue:", dict(Counter(i["status"] for i in q["items"])))
print("  frame-01 generated item:", [i["id"] for i in q["items"] if i["frame"]==1 and i["status"]=="generated"])
print("  stranded item:", [(i["id"], i["status"], (i.get("execution") or {}).get("phase")) for i in q["items"] if i["id"]=="87d54b6a927d"])
print("--- prompt ---")
p1 = EP/"docs"/"prompts"/"reveal-order-v2"/"01.txt"
print("  01.txt sha:", hashlib.sha256(p1.read_text(encoding='utf-8-sig').strip().encode()).hexdigest())
print("  first line:", p1.read_text(encoding="utf-8-sig").splitlines()[0][:90])
print("--- processes ---")
