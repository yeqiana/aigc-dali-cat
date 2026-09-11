# -*- coding: utf-8 -*-
import json, sys
from pathlib import Path

sys.path.insert(0, 'episodes/_system')
import release_preflight_review as rpr
from release_preflight_core import ROOT

ep = Path('episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉').resolve()

rows = rpr.release_hashes(ep)
review_rows = rpr.release_review_rows(rows)
print('== REVIEW ROWS ==')
for role, row in review_rows.items():
    print(f'{role:20s} {row["path"]}  {row["sha256"][:16]}')

print('\n== SUBTITLES (meta/subtitles.yaml) ==')
t = (ep / 'meta/subtitles.yaml').read_text(encoding='utf-8')
print(t)

import release_preflight_core as core
man = core.read_json(ep / 'meta/release-manifest.json')
art = man.get('artifacts') or {}
print('\n== MANIFEST artifact paths ==')
for k, v in art.items():
    print(f'{k:20s} {v}')
