# -*- coding: utf-8 -*-
import os, sys, io, json, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
for rel in ["meta/runtime/raw-candidate-budget.json", "meta/runtime/raw-candidate-budget-override.json", "meta/runtime/circuit-breaker.json", "meta/runtime/raw-candidate-budget-par.json"]:
    p = os.path.join(EP, rel)
    if os.path.exists(p):
        st = os.stat(p)
        t = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S')
        j = json.load(open(p, 'rb'))
        print("=====", rel, "mtime", t)
        print(json.dumps(j, ensure_ascii=False, indent=1)[:2500])
    else:
        print("=====", rel, "(missing)")
