import json
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
d = json.load(open(base + "/meta/caption-image-audit.json", encoding="utf8"))
print("summary:", json.dumps(d.get("summary"), ensure_ascii=False))
for k in ["01","02","10","11","20"]:
    f = d["frames"].get(k, {})
    print(k, "| sha", str(f.get("image_sha256"))[:16], "| capsha", str(f.get("caption_sha256"))[:12], "| passed", f.get("passed"), "| mode", f.get("mode"))
    prov = f.get("critic_provenance") or {}
    print("   prov:", prov.get("execution_source"), prov.get("runtime"), prov.get("attempt"), prov.get("reviewed_at"), prov.get("request_id"))

