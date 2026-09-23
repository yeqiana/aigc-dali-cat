import json, urllib.request
BASE='http://127.0.0.1:8080'
def get(p):
    with urllib.request.urlopen(BASE+p, timeout=10) as r:
        return json.loads(r.read().decode('utf-8'))
s=get('/api/v1/runtime/statuses?limit=3&offset=0')
print('STATUSES TOP KEYS:', list(s.keys()))
print('COUNT/TOTAL:', s.get('count'), s.get('total'))
print('STAGE_COUNTS:', json.dumps(s.get('stage_counts'), ensure_ascii=False))
data = s.get('data') if isinstance(s.get('data'), list) else s.get('items')
print('DATA LIST LEN:', len(data) if data is not None else None)
it = data[0] if data else {}
print('SUMMARY ITEM KEYS:', list(it.keys()))
print('SUMMARY_ITEM:', json.dumps(it, ensure_ascii=False)[:1600])
e=get('/api/v1/runtime/events?limit=2&offset=0')
print('EVENTS TOP KEYS:', list(e.keys()))
edata = e.get('data') if isinstance(e.get('data'), list) else e.get('items')
ei = edata[0] if edata else {}
print('EVENT ITEM KEYS:', list(ei.keys()))
print('EVENT_ITEM:', json.dumps(ei, ensure_ascii=False)[:900])
t=get('/api/v1/traces?limit=2&offset=0')
print('TRACES TOP KEYS:', list(t.keys()))
tdata = t.get('data') if isinstance(t.get('data'), list) else t.get('items')
ti = tdata[0] if tdata else {}
print('TRACE ITEM KEYS:', list(ti.keys()))
print('TRACE_ITEM:', json.dumps(ti, ensure_ascii=False)[:900])
