import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ep = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉")
q = json.loads((ep/"meta"/"production-queue.json").read_text(encoding="utf-8"))
from collections import Counter
print("queue statuses:", dict(Counter(i["status"] for i in q["items"])))
print("frame01 items:")
for i in q["items"]:
    if int(i.get("frame") or 0) == 1:
        print("  ", i["id"], i["status"], i.get("capture_id"), "| out:", (i.get("output_path") or "-")[-24:])
led = json.loads((ep/"meta"/"production-ledger.json").read_text(encoding="utf-8"))
print("ledger statuses:", dict(Counter(f.get("status") for f in led["frames"].values())))
st = json.loads((ep/"meta"/"episode-state.json").read_text(encoding="utf-8"))
print("episode-state.current_state:", st.get("current_state"))
snap = json.loads((ep/"meta"/"final-candidate-snapshot.json").read_text(encoding="utf-8"))
print("snapshot_sha256:", snap.get("snapshot_sha256"))
