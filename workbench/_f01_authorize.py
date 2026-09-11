
import json, os
ep = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
p = os.path.join(ep, "meta/runtime/raw-candidate-budget-override.json")
d = json.load(open(p, encoding="utf-8"))
entry = {
    "frame": "01",
    "kind": "repair",
    "additional": 1,
    "reason": "user-directed frame-01 framing fix 2026-09-10: the approved frame 01 reads as a full-length doorway snapshot, not the requested front-face / selfie-like portrait. Prompt-only change (docs/prompts/reveal-order-v2/01.txt -> close-up front face); Story / Storyboard / Frame Contract stay frozen (contract 551c1be4), so the approved pixels are regenerated once against the same contract.",
    "authorization": {
        "approved": True,
        "source": "user direct instruction 2026-09-10: \"还有一个问题，就是第一张不是我想要的人物正脸或者自拍之类的\"",
        "authorized_at": "2026-09-10T14:05:00+08:00",
    },
    "restore_defaults_by": "remove this entry (module falls back to the fixed per-frame limit)",
}
rows = d.setdefault("per_frame_authorizations", [])
if not any(r.get("reason", "").startswith("user-directed frame-01 framing fix") for r in rows):
    rows.append(entry)
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("entries:", len(rows))
import sys
sys.path.insert(0, "episodes/_system")
import raw_candidate_budget as b
from pathlib import Path
epP = Path(ep)
print("frame01 repair raise:", json.dumps(b.authorized_frame_raise(epP, "01", "repair"), ensure_ascii=False))
st = b.load(epP)
print("frame01 repair used:", st["frames"]["01"]["repair"]["used"])

