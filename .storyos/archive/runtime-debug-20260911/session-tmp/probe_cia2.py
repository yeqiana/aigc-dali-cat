# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, 'episodes/_system')
import caption_image_audit as cia

lines = Path(cia.__file__).read_text(encoding='utf-8').splitlines()
for a, b in ((235, 300), (300, 460)):
    print(f'--- {a}-{b} ---')
    for i in range(a - 1, min(b, len(lines))):
        print(f'{i+1:4}: {lines[i]}')
