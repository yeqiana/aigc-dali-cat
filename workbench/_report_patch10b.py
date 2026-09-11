import sys
sys.stdout.reconfigure(encoding='utf-8')
BT = chr(96)
P = 'reports/09-05婚礼前夜生产问题复盘_20260910.md'
t = open(P, encoding='utf-8', newline='').read()
def rep(old, new):
    global t
    c = t.count(old)
    if c != 1:
        raise SystemExit('MATCH_FAIL %d :: %s' % (c, old[:60]))
    t = t.replace(old, new, 1)
rep('- @BT@meta/runtime/trace-events.jsonl@BT@（164 条事件）', '- @BT@meta/runtime/trace-events.jsonl@BT@（164 条事件；作废后为 165 条，最后一条是第 10 节那个没有配对 @BT@SPAN_END@BT@ 的 @BT@SPAN_START@BT@）')
rep('@BT@meta/episode-performance-ledger.json@BT@、@BT@meta/image-workers/*.jsonl@BT@（46 个）', '@BT@meta/episode-performance-ledger.json@BT@、@BT@meta/image-workers/*.jsonl@BT@（46 个，作废后 47 个）')
t = t.replace('@BT@', BT)
open(P, 'w', encoding='utf-8', newline='').write(t)
print('OK bytes', len(t.encode('utf-8')))
