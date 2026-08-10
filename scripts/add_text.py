import os, glob
from PIL import Image, ImageDraw, ImageFont

img_dir = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-01\images"
font_path = r"C:\Windows\Fonts\msyh.ttc"

overlays = {
    "02": "我今年大二，师范专业。\n为了赚点生活费，接了一份老小区的家教。",
    "03": "第一次去的时候，一切看起来都很普通。\n老式防盗门，门口的小学生运动鞋，\n门上还贴着褪色的福字。",
    "05": "我在客厅给小明讲题，无意间抬头——\n厨房里，奶奶蹲在墙角，\n对着一面墙，嘴里念念有词。",
    "06": "回去的地铁上我跟闺蜜吐槽，\n她说可能就是拜灶神，老人都这样。\n我觉得有道理，就没再多想。",
    "08": "第四次去的时候，我忍不住走近厨房。\n灯泡突然闪了一下，\n奶奶的头……微微偏了过来。",
    "09": "那天晚上，小明的妈妈突然发来这三条消息。",
    "10": "我没有回复她。\n第二天傍晚，我直接去了那个楼道。",
    "11": "门大敞着。客厅空无一人。\n电视开着但没有声音。\n厨房里的灯亮着，地板上拖出一条长长的光斑。",
    "13": "通往厨房的走廊。墙上挂着一副旧日历——\n停在农历七月十五。\n地上，有一道不是我自己的影子。",
    "14": "我扶着墙，一步步挪向厨房。\n灯泡不再闪了。\n墙角那个蹲着的影子，一动不动。",
    "16": "我猛地回头——\n客厅沙发上坐着一个人。\n花白头发，碎花衬衫。\n端端正正地坐着，姿势太规矩了，不像活人。",
    "18": "我冲出那扇门，跑下楼梯。\n声控灯一盏一盏灭在我身后。\n手机从口袋里滑落，屏幕亮着。",
}

font = ImageFont.truetype(font_path, 26)
files = sorted(glob.glob(os.path.join(img_dir, "*.png")))

for fp in files:
    fname = os.path.basename(fp)
    prefix = fname[:2]
    if prefix not in overlays:
        continue
    text = overlays[prefix]
    img = Image.open(fp).convert("RGBA")
    w, h = img.size
    lines = text.split("\n")
    line_h = 34
    bar_h = line_h * len(lines) + 20
    
    top_bar = Image.new("RGBA", (w, bar_h), (0, 0, 0, 180))
    img.paste(top_bar, (0, 0), top_bar)
    
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = 6 + i * line_h
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    
    img = img.convert("RGB")
    img.save(fp, "PNG")
    print(f"OK: {fname}")
print("Done!")
