# -*- coding: utf-8 -*-
import json, shutil, sys
from pathlib import Path

sys.path.insert(0, 'episodes/_system')

import release_preflight_review as rpr
import product_review_adapter as pra
from release_preflight_core import ROOT

ep = Path('episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉').resolve()

# backup current review evidence before replacing (keep immutable history)
review_file = ep / rpr.RELEASE_REVIEW_REL
if review_file.is_file():
    bak = review_file.with_name(review_file.name + '.pre-v2.1-subtitle.json')
    if not bak.is_file():
        shutil.copy2(review_file, bak)
        print('backup ->', bak.name)
    else:
        print('backup exists:', bak.name)

candidate = ep / rpr.RELEASE_CANDIDATE_REL

rows = rpr.release_hashes(ep)
prompt = rpr.release_critic_prompt(ep, candidate, rows)
review_rows = rpr.release_review_rows(rows)

import subtitle_layout, caption_image_audit
source_paths = list(dict.fromkeys(
    [ (ROOT / row['path']) for row in review_rows.values() ] +
    [ ep / subtitle_layout.REPORT_REL, ep / caption_image_audit.REL,
      Path('standards/制作规范_正式版.md').resolve(), Path('standards/release_preflight_guard_V2.0.3.5.md').resolve() ]
))

req = pra.prepare(
    ep, kind='release-semantic', runtime='WORK', attempt=2,
    prompt=prompt, source_paths=source_paths, candidate_path=candidate,
)
print(json.dumps({k: req.get(k) for k in ('request_id', 'request_fingerprint', 'attempt', 'status', 'runtime', 'critic_runtime', 'request_path', 'candidate_path', 'created_at')}, ensure_ascii=False, indent=1))
print('source_count:', len(req.get('source_files') or []))
