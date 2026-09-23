import json, urllib.request
BASE='http://127.0.0.1:8080'
def get(p):
    with urllib.request.urlopen(BASE+p, timeout=10) as r:
        return json.loads(r.read().decode('utf-8'))
s=get('/api/v1/runtime/statuses?limit=3&offset=0')
d=s['data']
print('DATA TYPE:', type(d).__name__)
if isinstance(d, dict):
    print('DATA KEYS:', list(d.keys()))
    for k,v in d.items():
        if isinstance(v, list): print('  list', k, 'len', len(v))
print(json.dumps(s, ensure_ascii=False)[:3000])
