# -*- coding: utf-8 -*-
import shutil, pathlib
EP = pathlib.Path(r"D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉")
DOC = EP / "docs" / "06_婚礼前夜_最终发布文案_V2.0.md"
BAK = EP / "meta" / "publish-copy.v2.0-pre-style.md"
if not BAK.exists():
    shutil.copy2(DOC, BAK)
NEW = pathlib.Path(r"D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/.storyos_tmp/style_intro.txt").read_text(encoding="utf-8").strip()
T = DOC.read_text(encoding="utf-8")
A = T.find("## 简介")
B = T.find("## 话题")
assert A >= 0 and B > A
H = T.find(chr(10) + chr(10), A)
SEP = chr(10) + chr(10)
DOC.write_text(T[: H + 2] + NEW + SEP + T[B:], encoding="utf-8")
print("doc bytes:", DOC.stat().st_size)
