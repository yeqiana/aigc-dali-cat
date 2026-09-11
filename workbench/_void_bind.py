import json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ep = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉")
for rel in ("meta/release-manifest.json", "meta/episode-state.json", "meta/story-gates.json"):
    d = json.loads((ep/rel).read_text(encoding="utf-8"))
    txt = json.dumps(d, ensure_ascii=False)
    print(rel, "| mentions snapshot:", "snapshot" in txt, "| len", len(txt))
    if "snapshot" in txt:
        import re
        for m in re.finditer(r'.{120}snapshot.{160}', txt):
            print("   ...", m.group(0))
