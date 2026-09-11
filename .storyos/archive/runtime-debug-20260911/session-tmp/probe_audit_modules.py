# -*- coding: utf-8 -*-
import json, re, sys
from pathlib import Path

sys.path.insert(0, 'episodes/_system')
import subtitle_layout, caption_image_audit

for mod, name in ((subtitle_layout, 'subtitle_layout'), (caption_image_audit, 'caption_image_audit')):
    src = Path(mod.__file__).read_text(encoding='utf-8')
    print(f'## {name} defs')
    for m in re.finditer(r'^def |^[A-Z_]+\s*=\s*(Path\(|\")', src, re.M):
        line = src[:m.start()].count('\n') + 1
        print(line, m.group(0)[:100])
    for const in ('REL', 'REPORT_REL'):
        m = re.search(rf'^{const}\s*=\s*([^\n]+)', src, re.M)
        if m:
            print(' ', const, '=', m.group(1)[:100])

ep = Path('episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉')
d = json.load(open(ep / 'meta/caption-image-audit.json', encoding='utf-8'))
frames = d.get('frames') or []
print('caption audit frames count:', len(frames))
print(json.dumps(frames[0] if isinstance(frames, list) else frames, ensure_ascii=False, indent=1)[:2500])
