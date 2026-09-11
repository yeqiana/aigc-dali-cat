
p = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system/production_recovery.py'
src = open(p, encoding='utf-8').read()
print('len', len(src))
import re
for m in re.finditer(r'^def\s+(\w+)', src, re.M):
    print(m.start(), m.group(1))
i = src.find('def reconcile_locked')
print('=' * 30)
print(src[i:i+3000])

