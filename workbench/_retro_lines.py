import sys
sys.stdout.reconfigure(encoding='utf-8')
p = r"reports\09-05婚礼前夜生产问题复盘_20260910.md"
lines = open(p, encoding="utf-8").read().splitlines()
for i in list(range(0, 8)) + list(range(91, 102)) + list(range(len(lines)-6, len(lines))):
    if 0 <= i < len(lines):
        print(f"{i+1:4d}|{lines[i]!r}")
