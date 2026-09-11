
import re, glob, os
base = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system'
for f in sorted(glob.glob(os.path.join(base, '*.py'))):
    src = open(f, encoding='utf-8').read()
    if 'def cmd_tech_fail' in src:
        i = src.find('def cmd_tech_fail')
        print('FOUND in', os.path.basename(f))
        print(src[i:i+2800])
        break
else:
    print('cmd_tech_fail not found in _system/*.py')
print('=== production_recovery import lines ===')
p = os.path.join(base, 'production_recovery.py')
src = open(p, encoding='utf-8').read()
for line in src.splitlines()[:40]:
    print('   ', line)

