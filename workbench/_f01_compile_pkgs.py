# -*- coding: utf-8 -*-
import subprocess, sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
EP = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
PROMPTS = os.path.join("episodes", "09_旧物怪谈", "05_婚礼前夜_记忆麻醉", "docs", "prompts", "reveal-order-v2")
for f in range(1, 21):
    p = os.path.join(PROMPTS, "%02d.txt" % f)
    r = subprocess.run([sys.executable, "episodes/_system/prompt_package.py", "compile", EP, "--frame", str(f), "--prompt-file", p],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = "PASS" if r.returncode == 0 else "FAIL"
    print("%02d" % f, ok, (r.stdout + r.stderr)[-260:].replace("\n", " | ").strip())
