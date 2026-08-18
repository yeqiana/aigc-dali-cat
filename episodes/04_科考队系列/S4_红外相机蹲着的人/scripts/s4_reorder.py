# -*- coding: utf-8 -*-
"""历史脚本：S4 发布后源图已清理，不再作为当前生产入口。"""
import os
import re

STAGE = os.environ["S4_STAGE"]
DST = os.environ["S4_DST"]
PAT = re.compile(r"^S4_\u56fe(\d+)_(.+)\.png$")

# (source_num, source_keyword, target_num)
RULES = [
    ("01", "\u5c01\u9762", "01"),
    ("02", "\u8fdb\u5c71", "02"),
    ("03", "\u65e0\u8db3\u8ff9", "04"),
    ("04", "\u7b2c\u4e00\u4ef6\u8bc1\u636e", "03"),
    ("05", "\u8c8c\u4f3c", "05"),
    ("06", "\u7b2c\u4e8c\u5f20", "06"),
    ("07", "\u7b2c\u4e09\u5f20", "07"),
    ("08", "\u8db3\u8ff9", "08"),
    ("09", "\u65e5\u5fd7\u7ffb\u9875", "09"),
    ("10", "\u961f\u5185", "10"),
    ("11", "\u6253\u5370", "11"),
    ("12", "\u81ea\u62cd", "12"),
    ("13", "\u5b9e\u4f53", "13"),
    ("14", "\u5168\u8c8c\u52a0\u7801", "14"),
    ("14", "\u5bf9\u5cd9", "15"),
    ("16", "\u96fe\u5728\u6536\u62e2", "16"),
    ("15", "\u652f\u67b6", "17"),
    ("16", "\u5feb\u95e8", "18"),
    ("19", "\u65f6\u95f4\u8d85\u524d", "19"),
    ("17", "1985", "20"),
    ("18", "\u89c4\u5219\u786e\u8ba4", "21"),
    ("19", "\u8425\u5730\u76f8\u673a", "22"),
    ("23", "\u6380\u5e18", "23"),
    ("24", "\u5185\u5b58\u5361\u5f39\u51fa", "24"),
    ("20", "\u7ec8\u5c40", "25"),
]


def find(src_num, kw):
    for name in os.listdir(STAGE):
        m = PAT.match(name)
        if not m:
            continue
        if m.group(1) == src_num and kw in m.group(2):
            return name
    return None


def main():
    moved = 0
    for src_num, kw, tgt in RULES:
        f = find(src_num, kw)
        if not f:
            print("MISS", src_num, kw)
            continue
        suffix = f.split("_", 2)[2].rsplit(".", 1)[0]
        new_name = "S4_" + tgt + "_" + suffix + ".png"
        os.rename(os.path.join(STAGE, f), os.path.join(DST, new_name))
        moved += 1
        print("OK", f, "->", new_name)
    print("moved:", moved, "/", len(RULES))


if __name__ == "__main__":
    main()
