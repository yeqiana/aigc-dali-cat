import json, sys, os, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat")
sys.path.insert(0, str(ROOT/"episodes"/"_system"))
import final_candidate_snapshot as fcs
ep = ROOT/"episodes"/"09_旧物怪谈"/"05_婚礼前夜_记忆麻醉"
saved = json.loads((ep/"meta"/"final-candidate-snapshot.json").read_text(encoding="utf-8"))
rows = saved["lock"]["evidence"]
for i, row in enumerate(rows):
    print(i, row.get("role"), "|", row.get("path"), "|", row.get("bytes"), row.get("sha256","")[:12])
print("--- delivery_files ---")
for i, row in enumerate(saved["lock"]["delivery_files"]):
    if i in (25,): print(i, row.get("role"), "|", row.get("path"), "|", row.get("bytes"))
cur = fcs.build_lock(ep, write_evidence=False)
print("--- current evidence[0] ---")
print(json.dumps(cur["evidence"][0], ensure_ascii=False))
p = ROOT/cur["evidence"][0]["path"]
print("mtime:", datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat())
