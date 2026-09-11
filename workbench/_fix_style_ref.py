import sys
sys.stdout.reconfigure(encoding='utf-8')
P = r'standards/参考_字幕与简介风格解析_第一人称自述闭环体.md'
t = open(P, encoding='utf-8').read()
print('bs_total', t.count(chr(92)))
print('bs_n', t.count(chr(92) + 'n'))
t2 = t.replace(chr(92) + 'n', chr(10))
print('leftover_bs', t2.count(chr(92)))
open(P, 'w', encoding='utf-8', newline=chr(10)).write(t2)
print('LINES', t2.count(chr(10)), 'BYTES', len(t2.encode('utf-8')))
