
import re
p = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system/production_ledger.py'
src = open(p, encoding='utf-8').read()
print('len', len(src))
i = src.find('def cmd_tech_fail')
print(src[i:i+2600] if i >= 0 else 'not found')
print('=== related names ===')
for m in re.finditer(r'^def\s+(\w+)', src, re.M):
    n = m.group(1)
    if any(k in n for k in ('tech', 'fail', 'lock', 'restore', 'revert', 'ready')):
        print(' ', m.start(), n)

