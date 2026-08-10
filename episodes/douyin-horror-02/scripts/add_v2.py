# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont

V3_DIR = r'D:\workspace\YeQianWorkSpace\yeqianigc-dali-cat\episodes\douyin-horror-023_final'
OUT_DIR = os.path.join(V3_DIR, 'subtitled')
os.makedirs(OUT_DIR, exist_ok=True)

FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'
FONT_SIZE = 28
PX, PY = 28, 20
ALPHA = 150
R = 20
W_RATIO = 0.75

DATA = {}
