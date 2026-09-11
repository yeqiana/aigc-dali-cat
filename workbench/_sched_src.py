
import re
src = open(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system/image_scheduler.py', encoding='utf-8').read()
for name in ['def cmd_reconcile', 'def _reconcile', 'def cmd_retry_tech']:
    i = src.find(name)
    print('=' * 20, name, i)
    if i >= 0:
        print(src[i:i+1800])

