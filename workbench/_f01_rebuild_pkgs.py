# -*- coding: utf-8 -*-
import subprocess, sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
PKG = os.path.join(EP, "meta", "runtime", "prompt-packages")
# stale derived packages for frames 02-20 (01 already recompiled with new scene text)
for f in range(2, 21):
    p = os.path.join(PKG, "%02d.json" % f)
    if os.path.exists(p):
        os.remove(p)
        print("removed stale package", "%02d.json" % f)
PROMPTS = os.path.join("episodes", "09_旧物怪谈", "05_婚礼前夜_记忆麻醉", "docs", "prompts", "reveal-order-v2")
for f in range(1, 21):
    pp = os.path.join(PROMPTS, "%02d.txt" % f)
    r = subprocess.run([sys.executable, "episodes/_system/prompt_package.py", "compile", EP, "--frame", str(f), "--prompt-file", pp],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = "PASS" if r.returncode == 0 else "FAIL"
    detail = (r.stdout + r.stderr).strip().splitlines()
    print("%02d" % f, ok, (detail[-1][:200] if detail else ""))
