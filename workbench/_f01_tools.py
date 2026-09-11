# -*- coding: utf-8 -*-
import os, sys, io, json, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"

print("== episodes/_system scripts ==")
for p in sorted(glob.glob(r"episodes/_system/*.py")):
    print(" ", os.path.basename(p))

print()
print("== trace-events tail ==")
tp = os.path.join(EP, "meta/runtime/trace-events.jsonl")
if os.path.exists(tp):
    lines = open(tp, 'rb').read().decode('utf-8', errors='replace').splitlines()
    for ln in lines[-60:]:
        try:
            j = json.loads(ln)
            ts = j.get("ts") or j.get("timestamp") or j.get("at") or ""
            ev = j.get("event") or j.get("type") or ""
            who = j.get("who") or j.get("agent") or ""
            msg = (j.get("message") or j.get("note") or j.get("detail") or "")[:200]
            cmd = (j.get("command") or j.get("cmd") or "")[:200]
            print(ts, "|", ev, "|", who, "|", cmd, "|", msg)
        except Exception as e:
            print("parse-fail:", str(e)[:80], ln[:160])
else:
    print("no trace file")
