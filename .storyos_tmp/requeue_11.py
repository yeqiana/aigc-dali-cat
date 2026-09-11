# -*- coding: utf-8 -*-
import json
from pathlib import Path

p = Path("episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/production-queue.json")
q = json.loads(p.read_text(encoding="utf-8"))
changed = []
for x in q.get("items", []):
    if x.get("frame") == 11 and x.get("status") == "blocked":
        x["status"] = "queued"
        x["last_error"] = None
        x["retry_pending"] = True
        changed.append(11)
p.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")
print("requeued_frame_11:", changed)
print("now:", [(x.get("frame"), x.get("status")) for x in q.get("items", [])])
