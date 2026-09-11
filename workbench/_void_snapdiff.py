import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat")
sys.path.insert(0, str(ROOT/"episodes"/"_system"))
import final_candidate_snapshot as fcs
ep = ROOT/"episodes"/"09_旧物怪谈"/"05_婚礼前夜_记忆麻醉"
saved = json.loads((ep/"meta"/"final-candidate-snapshot.json").read_text(encoding="utf-8"))
print("saved built_at:", saved.get("built_at"))
current = fcs.build_lock(ep, write_evidence=False)
def walk(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a: yield (f"{path}.{k}", "<missing-in-saved>", str(b[k])[:80])
            elif k not in b: yield (f"{path}.{k}", str(a[k])[:80], "<missing-in-current>")
            else: yield from walk(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): yield (f"{path}[]", f"len={len(a)}", f"len={len(b)}")
        for i, (x, y) in enumerate(zip(a, b)): yield from walk(x, y, f"{path}[{i}]")
    else:
        if a != b: yield (path, str(a)[:100], str(b)[:100])
diffs = list(walk(saved.get("lock") or {}, current))
print("diff count:", len(diffs))
for p, a, b in diffs[:40]:
    print(f"  {p}\n     saved  : {a}\n     current: {b}")
