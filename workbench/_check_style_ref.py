import sys
sys.stdout.reconfigure(encoding='utf-8')
P = r'standards/参考_字幕与简介风格解析_第一人称自述闭环体.md'
L = open(P, encoding='utf-8').read().split(chr(10))
for i, l in enumerate(L):
    if l.startswith('#') or l.startswith('| #') or l.startswith('| 项'):
        print(i + 1, '|', l)
print('---spot check---')
print(chr(10).join(L[8:14]))
print('BT', sum(l.count(chr(96)) for l in L), 'PIPES', sum(l.count('|') for l in L))
