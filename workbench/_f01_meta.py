# -*- coding: utf-8 -*-
import os, sys, io, json, glob, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"

def jload(p):
    try:
        with open(p, 'rb') as f:
            return json.load(f)
    except Exception as e:
        return {"_error": str(e)}

def dump(title, obj, maxlen=8000):
    s = json.dumps(obj, ensure_ascii=False, indent=1)
    print("=" * 15, title, "=" * 15)
    print(s[:maxlen])

# mtimes of contracts/prompt packages
print("== contract frames mtime ==")
for p in sorted(glob.glob(os.path.join(EP, "meta/runtime/contracts/frames/*.json"))):
    st = os.stat(p)
    t = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S')
    j = jload(p)
    print(t, os.path.basename(p), "gen=%s" % j.get("generated_at", ""), "sb=%s" % str(j.get("source_trace", {}).get("storyboard", {}).get("sha256", ""))[:12])

print()
print("== prompt packages mtime ==")
for p in sorted(glob.glob(os.path.join(EP, "meta/runtime/prompt-packages/*.json"))):
    st = os.stat(p)
    t = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S')
    j = jload(p)
    print(t, os.path.basename(p), "prompt_sha=%s" % str(j.get("scene_prompt_sha256", ""))[:12], "fc_sha=%s" % str(j.get("frame_contract_sha256", ""))[:12])

for rel in ["meta/runtime-checkpoint.json", "meta/runtime/production-reconciliation.json", "meta/production-queue.json"]:
    dump(rel, jload(os.path.join(EP, rel)), maxlen=5000)
