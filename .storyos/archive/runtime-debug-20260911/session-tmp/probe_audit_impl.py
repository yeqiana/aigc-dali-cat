# -*- coding: utf-8 -*-
import sys
from pathlib import Path

sys.path.insert(0, 'episodes/_system')
import subtitle_layout as sl
import caption_image_audit as cia


def show(mod, name, spans):
    lines = Path(mod.__file__).read_text(encoding='utf-8').splitlines()
    print(f'===== {name} =====')
    for a, b in spans:
        print(f'--- lines {a}-{b} ---')
        for i in range(a - 1, min(b, len(lines))):
            print(f'{i+1:4}: {lines[i]}')


show(sl, 'subtitle_layout', [(86, 210)])
show(cia, 'caption_image_audit', [(83, 235)])
