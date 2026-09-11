# -*- coding: utf-8 -*-
import pathlib
DOC = pathlib.Path(r"D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/docs/06_婚礼前夜_最终发布文案_V2.0.md")
T = DOC.read_text(encoding="utf-8")
T = T.replace("# 《婚礼前夜·记忆麻醉》最终发布文案 V2.0", "# 《婚礼前夜·记忆麻醉》最终发布文案 V2.1 风格版")
note = "> 2026-09-09 V2.1 修订：简介按用户指定风格文本压缩改写，保留首尾闭环、口语碎句、确定与怀疑拉扯；信息链与发布顺序不变，虚构声明保留。"
marker = "> 2026-09-09 V2 修订"
i = T.find(marker)
assert i >= 0
e = T.find(chr(10), i)
T = T[:e] + chr(10) + note + T[e:]
DOC.write_text(T, encoding="utf-8")
print(T[:300])
