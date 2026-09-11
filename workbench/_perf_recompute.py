
import json, glob, io, os
from datetime import datetime, timedelta

ep = r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'

def load_ts():
    ts = []
    p = os.path.join(ep, 'meta/runtime/trace-events.jsonl')
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l: continue
        d = json.loads(l)
        a = d.get('at')
        if a: ts.append((a, d.get('event'), d.get('name')))
    led = json.load(open(os.path.join(ep, 'meta/episode-performance-ledger.json'), encoding='utf-8'))
    for st in led.get('state_transitions', []):
        ts.append((st['at'], 'STATE', st['to']))
    for span, obj in (led.get('named_spans') or {}).items():
        for r in obj.get('runs', []):
            ts.append((r['started_at'], 'REVIEW_START', span))
            ts.append((r['ended_at'], 'REVIEW_END', span))
    def parse(s):
        return datetime.fromisoformat(s)
    ts.sort(key=lambda x: parse(x[0]))
    return ts

def analyze(ts, gap_minutes=30):
    parse = lambda s: datetime.fromisoformat(s)
    total = timedelta()
    sessions = []
    cur_start = parse(ts[0][0]); prev = cur_start
    for t, ev, name in ts[1:]:
        dt = parse(t)
        if dt - prev > timedelta(minutes=gap_minutes):
            sessions.append((cur_start, prev, prev - cur_start))
            cur_start = dt
        else:
            total += dt - prev
        prev = dt
    sessions.append((cur_start, prev, prev - cur_start))
    return total, sessions

ts = load_ts()
print('timestamps', len(ts), 'from', ts[0][0], 'to', ts[-1][0])
for gap in (15, 30, 60):
    total, sessions = analyze(ts, gap)
    print('--- gap>%dmin treated as pause: active=%s (%.2f h) sessions=%d' % (gap, total, total.total_seconds()/3600, len(sessions)))
    for s, e, d in sessions:
        print('    %s -> %s  %.2f h' % (s.strftime('%m-%d %H:%M'), e.strftime('%m-%d %H:%M'), d.total_seconds()/3600))

