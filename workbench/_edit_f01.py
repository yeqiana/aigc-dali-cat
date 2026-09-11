
# -*- coding: utf-8 -*-
import json, io, sys
from pathlib import Path
ep = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\09_旧物怪谈\05_婚礼前夜_记忆麻醉")

SCENE = "P01站在婚房门口对镜头，正面看向相机（持机者为院里男方，用她的卡片机拍婚前夜留影）；黑发红绳、浅色碎花长袖、深色裤、旧布鞋，神情平和微怔。身后婚房红彤彤：红被铺好的木床、桌边亲友整理搪瓷盆与红绸，喜字与红布窗完整，土墙可见。无药瓶、药片、铁栏或锁链。"
assert SCENE.count("药瓶")==1 and "铁栏" in SCENE

# ---------- docs/03 ----------
p03 = ep/"docs"/"03_婚礼前夜_20张正式分镜_V2.0.md"
t03 = p03.read_text(encoding="utf-8")

g_old = "P01第一人称；浅色碎花长袖、深色裤、旧布鞋，黑发红绳不变。禁止女主正脸、第三人称、白婚纱、电影灯、HDR、文字水印。"
g_new = "P01第一人称；浅色碎花长袖、深色裤、旧布鞋，黑发红绳不变。全篇禁止女主清晰正脸，仅图01例外：婚前夜门口留影，院里男方用她的卡片机持机，女主正面看向相机，为全篇唯一露脸帧。禁止第三人称旁观、白婚纱、电影灯、HDR、文字水印。"
assert g_old in t03
t03 = t03.replace(g_old, g_new)

b_old = "- 第一人称涉及操作时左手操作、右手持机；03—04与19—20允许主观梦/醒视觉，不宣称熟睡时相机仍在拍。镜面只取身体局部，姿态、衣服、物件必须真实对应。"
b_new = b_old + "\n- 图01持机例外：男主婚前夜在院里用P01的卡片机给她拍门口留影，相机来源可解释、仅此一张；02—20仍为P01第一人称，不出现女主清晰正脸。"
assert b_old in t03
t03 = t03.replace(b_old, b_new)

f01_old = """- 画面：P01站在婚房门口向内看，左手扶门框，男人侧后身铺红被，亲友整理搪瓷盆与红绸。土墙可见，窗上红布完整遮住结构。无药瓶、药片、铁栏或锁链。
- 字幕：明天就要结婚了，我却想不起他求婚的样子。
- 本帧允许知道：只建立婚前记忆缺口，不能指向药物控制。
- 逐帧硬约束：药瓶禁止入画。 P01仅手脚肩袖局部；同一碎花袖、深色裤。画面动作单一，证据不被字幕遮挡。
- Scene Prompt：P01站在婚房门口向内看，左手扶门框，男人侧后身铺红被，亲友整理搪瓷盆与红绸。土墙可见，窗上红布完整遮住结构。无药瓶、药片、铁栏或锁链。"""
f01_new = """- 画面：""" + SCENE + """
- 字幕：明天就要结婚了，我却想不起他求婚的样子。
- 本帧允许知道：只建立婚前记忆缺口，不能指向药物控制。
- 逐帧硬约束：药瓶禁止入画。 图01为全篇唯一允许女主清晰正脸帧（院里男方用她的卡片机拍留影，持机来源可解释）；同一碎花袖、深色裤、旧布鞋、黑发红绳必须与02—20同一身体。画面动作单一，字幕不遮挡人脸，证据不被字幕遮挡。
- Scene Prompt：""" + SCENE
assert f01_old in t03, "frame01 block not found in docs/03"
t03 = t03.replace(f01_old, f01_new)
p03.write_text(t03, encoding="utf-8")
print("docs/03 ok")

# ---------- docs/04 ----------
p04 = ep/"docs"/"04_婚礼前夜_视觉规范_V2.0.md"
t04 = p04.read_text(encoding="utf-8")
assert g_old in t04
t04 = t04.replace(g_old, g_new)
assert b_old in t04
t04 = t04.replace(b_old, b_new)
p04.write_text(t04, encoding="utf-8")
print("docs/04 ok")

# ---------- story-gates.json ----------
pg = ep/"meta"/"story-gates.json"
g = json.loads(pg.read_text(encoding="utf-8"))
g["visual"]["continuity"]["anchors"]["protagonist"] = "23岁碎花长袖上衣+深色长裤+旧布鞋；02—20仅露手/脚/局部，不露清晰正脸；图01为全篇唯一露脸帧（院中男方用她的卡片机拍门口留影，女主正面看向相机）"
g["visual"]["authenticity_card"]["camera_rules"]["photographer_visibility_explanation"] = "主角作为摄影者通常仅局部入画（手、脚步、半身、镜中反射），避免露清晰正脸；图01为全篇唯一正面入镜帧：院中男方用她的卡片机在门口拍婚前夜留影"
g["visual"]["authenticity_card"]["secondary_source_explanation"] = "除图01由院中男方用P01的卡片机拍门口留影外，其余画面均由主角手持旧数码相机记录"
d01 = g["visual"]["frame_directives"]["01"]
d01["required_visual_cues"] = [SCENE]
d01["pov_and_wardrobe"] = "P01浅色碎花长袖、深色裤、旧布鞋；01—18不换装，16—18布鞋沾泥；19梦里同衣同姿态，20同碎花袖；男方深色外套。图01例外：女主正面看向相机（院中男方持她的卡片机拍留影），为全篇唯一露脸帧；02—20 P01第一人称，不能出现自己的脸；镜内外同人同衣同姿态。"
pg.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
print("story-gates ok")

# ---------- shot-progression-review.json ----------
ps = ep/"meta"/"shot-progression-review.json"
s = json.loads(ps.read_text(encoding="utf-8"))
fr = s["frames"][0]
assert fr["frame"] == "01"
fr["camera_position"] = "门口留影机位：院中男方持P01的卡片机，P01在门口面向镜头"
fr["action"] = SCENE
fr["pov_mode"] = "P01正面看向相机（图01全篇唯一露脸帧；同行者持机记录）"
ps.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
print("shot-progression ok")

# ---------- prompt 01.txt ----------
pp = ep/"docs"/"prompts"/"reveal-order-v2"/"01.txt"
lines = [
 SCENE,
 "信息边界：只建立婚前记忆缺口，不能指向药物控制。",
 "CP03现场光，4:5，禁电影灯、HDR、文字水印。",
 "画面中不得出现药瓶、药片、铁链、铁栏；本帧女主是全篇唯一露脸帧，画面内不出现第二张清晰人脸。",
]
txt = "\n".join(lines) + "\n"
c = len(txt.strip()); b = len(txt.encode("utf-8"))
print("prompt chars", c, "bytes", b)
assert c <= 260 and b <= 900, (c, b)
pp.write_text(txt, encoding="utf-8")
print("prompt 01 ok")

