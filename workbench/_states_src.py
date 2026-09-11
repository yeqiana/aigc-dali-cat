
import re, os
base = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system'
for name in ['production_ledger.py', 'production_ledger_run.py', 'production_ledger_manage.py']:
    p = os.path.join(base, name)
    src = open(p, encoding='utf-8').read()
    print('=' * 15, name, len(src))
    for m in re.finditer(r'^def\s+(\w+)', src, re.M):
        print('   ', m.group(1))
print('==== production_ledger.py head (states) ====')
print(open(os.path.join(base, 'production_ledger.py'), encoding='utf-8').read()[:2600])

