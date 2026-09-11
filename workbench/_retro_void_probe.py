import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
EP = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉")
tr = EP/"meta"/"runtime"/"trace-events.jsonl"
rows = [json.loads(l) for l in tr.read_text(encoding="utf-8").splitlines() if l.strip()]
print("trace rows:", len(rows))
for r in rows[-8:]:
    print("  ", r.get("at"), r.get("event") or r.get("kind"), json.dumps({k: v for k, v in r.items() if k not in ("at","event","kind")}, ensure_ascii=False)[:150])
starts = [r for r in rows if str(r.get("event","")).startswith("SPAN_START")]
ends = [r for r in rows if str(r.get("event","")).startswith("SPAN_END")]
print("SPAN_START:", len(starts), "SPAN_END:", len(ends))
for s in starts:
    key = s.get("span") or s.get("name")
    if not any((e.get("span") or e.get("name")) == key for e in ends):
        print("  UNCLOSED SPAN:", json.dumps(s, ensure_ascii=False)[:260])
j = EP/"meta"/"runtime"/"queue-journal.jsonl"
if j.is_file():
    jr = [json.loads(l) for l in j.read_text(encoding="utf-8").splitlines() if l.strip()]
    print("queue journal tail:")
    for r in jr[-4:]:
        print("  ", json.dumps(r, ensure_ascii=False)[:220])
perf = EP/"meta"/"episode-performance-ledger.json"
if perf.is_file():
    d = json.loads(perf.read_text(encoding="utf-8"))
    print("perf top keys:", list(d.keys())[:14])
    print("  active_wall_seconds:", (d.get("performance_slo") or {}).get("active_wall_seconds"))
