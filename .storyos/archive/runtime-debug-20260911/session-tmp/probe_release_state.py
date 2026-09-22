# -*- coding: utf-8 -*-
import json, re, sys
from pathlib import Path

root = Path('episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉')
p1 = root / 'meta/runtime/reviews/release-semantic-attempt-1-request.json'
if p1.is_file():
    d = json.load(open(p1, encoding='utf-8'))
    print('attempt1:', json.dumps({k: d.get(k) for k in ('request_id', 'status', 'attempt', 'candidate_path', 'finalized_at', 'runtime', 'review_kind', 'created_at')}, ensure_ascii=False))
else:
    print('attempt1 file missing')

core_txt = Path('episodes/_system/release_preflight_core.py').read_text(encoding='utf-8')
for m in re.finditer(r'^([A-Z_]+)\s*=\s*Path\("([^"]+)"\)', core_txt, re.M):
    print('PATHCONST', m.group(1), '=', m.group(2))
for m in re.finditer(r'^([A-Z_]+)\s*=\s*"([^"]+)"', core_txt, re.M):
    print('STRCONST', m.group(1), '=', m.group(2))
