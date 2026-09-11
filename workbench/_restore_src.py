
import os, re
base = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system'
src = open(os.path.join(base, 'production_ledger_run.py'), encoding='utf-8').read()
i = src.find('def cmd_restore_evidence_gap_review')
print(src[i:i+2200])
print('==== core states ====')
core = open(os.path.join(base, 'production_ledger_core.py'), encoding='utf-8').read()
for kw in ['READY_LEDGER_STATES', 'ACTIVE_LEDGER_STATES', 'LEDGER_STATES']:
    j = core.find(kw)
    print(kw, '->', core[j:j+260].split('\n')[0] if j >= 0 else 'not found')
print('==== restore subcommand wiring ====')
f = open(os.path.join(base, 'production_ledger.py'), encoding='utf-8').read()
k = f.find('restore')
print(f[max(0,k-300):k+500])

