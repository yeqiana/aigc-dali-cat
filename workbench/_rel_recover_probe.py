
# -*- coding: utf-8 -*-
"""Recover the critic-written candidate JSON from the isolated session transcript."""
import json, pathlib, re
ep = pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat') / r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
log = ep / 'meta/release-semantic-host-critic-attempt-1.jsonl'
text = log.read_text(encoding='utf-8-sig', errors='replace')
hits = [m.start() for m in re.finditer('release_checks', text)]
print('release_checks occurrences', len(hits))
print('--- context around last occurrences ---')
for h in hits[-3:]:
    print('===')
    print(text[max(0, h-260):h+120].replace(chr(10),' | ')[:900])

