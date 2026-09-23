import json, urllib.request, urllib.parse
BASE='http://127.0.0.1:8080'
def get(p):
    with urllib.request.urlopen(BASE+p, timeout=10) as r:
        return json.loads(r.read().decode('utf-8'))
s=get('/api/v1/runtime/statuses?limit=50&offset=0')
d=s['data']
print('TOTAL:', d['total'])
for row in d['items']:
    print(' -', row['episode_id'][:8], '|', row['episode_ref'], '|', row['production_stage'], '|', row['state_source'], '|', row['updated_at'])
ep = d['items'][0]['episode_ref']
det = get('/api/v1/runtime/status?episode=' + urllib.parse.quote(ep))
print()
print('DETAIL ENVELOPE KEYS:', list(det.keys()))
dd = det['data']
print('DETAIL DATA KEYS:', list(dd.keys()) if isinstance(dd, dict) else type(dd))
print('DETAIL:', json.dumps(dd, ensure_ascii=False)[:2500])
