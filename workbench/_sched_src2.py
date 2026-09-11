
import re
p = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system/image_scheduler.py'
src = open(p, encoding='utf-8').read()
print(len(src))
for m in re.finditer(r'^def\s+(\w+)', src, re.M):
    print(m.start(), m.group(1))

