
import sys
from PIL import Image
p1 = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉\media\approved\01.png"
out = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉\workbench\_preview_01.jpg"
im = Image.open(p1); print("src", im.size, im.mode)
im2 = im.convert("RGB")
im2.thumbnail((500, 625), Image.LANCZOS)
im2.save(out, "JPEG", quality=82)
print("saved", out)

