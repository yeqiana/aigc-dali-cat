# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
lines = open(r"episodes/_system/codex_subscription_image.py", encoding="utf-8").read().splitlines()
for a, b in [(1, 44), (155, 377), (453, 520)]:
    print("##### lines", a + 1, "-", b)
    for i in range(a, min(b, len(lines))):
        print(lines[i])
