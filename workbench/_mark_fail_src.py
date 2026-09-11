
p = r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system/production_recovery.py'
src = open(p, encoding='utf-8').read()
i = src.find('def _mark_technical_failure')
print('==== _mark_technical_failure ====')
print(src[i:i+1800])
j = src.find('def mark_terminal')
print('==== mark_terminal ====')
print(src[j:j+1000])

