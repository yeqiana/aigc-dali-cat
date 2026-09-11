import json, glob, os
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
for p in ["meta/delegated-release.json", "meta/raw-candidate-budget.json", "meta/raw-candidate-budget-override.json"]:
    try:
        d = json.load(open(base + "/" + p, encoding="utf8"))
        print("=====", p)
        print(json.dumps(d, ensure_ascii=False, indent=1)[:3000])
    except Exception as e:
        print("ERR", p, e)
print("zips:")
for p in glob.glob(base + "/**/*.zip", recursive=True) + glob.glob(".storyos_tmp/*.zip") + glob.glob(base + "/release/*.zip"):
    print(" ", p, os.path.getsize(p))

