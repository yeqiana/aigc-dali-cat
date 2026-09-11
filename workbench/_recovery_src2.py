
p = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system/production_recovery.py'
src = open(p, encoding='utf-8').read()
i = src.find('def reconcile_locked')
seg = src[i:i+5200]
print(seg[2900:5200])
print('==== ACTIVE_LEDGER_STATES ====')
j = src.find('ACTIVE_LEDGER_STATES')
print(src[max(0,j-400):j+400])

