
import os
base = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system'
src = open(os.path.join(base, 'production_ledger_manage.py'), encoding='utf-8').read()
for name in ['def cmd_promote', 'def cmd_lock', 'def cmd_authorize_user_locked_repair']:
    i = src.find(name)
    print('=' * 12, name)
    print(src[i:i+1800])

