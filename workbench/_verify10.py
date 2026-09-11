import json
d=json.load(open(r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/production-ledger.json',encoding='utf-8'))
print('TOPKEYS', list(d.keys()))
fr=d.get('frames')
print('TYPE_FRAMES', type(fr).__name__)
if isinstance(fr,dict):
    ks=list(fr.keys()); print('FRAME_KEYS', ks[:25])
    f=fr.get('01') or fr.get('1')
    print(json.dumps(f,ensure_ascii=False)[:2200])
else:
    print(json.dumps(fr,ensure_ascii=False)[:2200])
