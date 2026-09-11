
import os
base = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system'
src = open(os.path.join(base, 'production_ledger.py'), encoding='utf-8').read()
for key in ['"tech-fail"', '"lock"', '"promote"', '"success"']:
    i = src.find(key)
    print('=' * 10, key, i)
    if i >= 0:
        print(src[i-20:i+700])

