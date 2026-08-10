from PIL import Image, ImageDraw, ImageFont
import os, glob

img_dir = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\douyin-horror-01\images"
font_path = r"C:\Windows\Fonts\msyh.ttc"

overlays = {
    "01": "我接了一份城中村的家教，每小时40块。\n第三周，学生的妈妈突然发来这条消息。",
    "02": "我今年大二，师范专业。\n为了赚点生活费，接了一份老小区的家教。",
    "03": "第一次去的时候，一切看起来都很普通。\n老式防盗门，门口的小学生运动鞋，\n门上还贴着褪色的福字。",
    "04": "第一次去的时候，奶奶很客气，还给我倒了杯水。\n唯一让我觉得奇怪的是，她手里一直端着一碗白米饭。",
    "05": "我在客厅给小明讲题，无意间抬头——\n厨房里，奶奶蹲在墙角，\n对着一面墙，嘴里念念有词。",
    "06": "回去的地铁上我跟闺蜜吐槽，\n她说可能就是拜灶神，老人都这样。\n我觉得有道理，就没再多想。",
    "07": "第二次、第三次、第四次。每次我去的那个下午，\n奶奶都会端一碗白米饭进厨房。\n我问小明奶奶在干什么，他说：奶奶在跟阿姨说话。",
    "08": "第四次去的时候，我忍不住走近厨房。\n灯泡突然闪了一下，\n奶奶的头……微微偏了过来。",
    "09": "那天晚上，小明的妈妈突然发来这三条消息。",
    "10": "我没有回复她。\n第二天傍晚，我直接去了那个楼道。",
    "11": "门大敞着。客厅空无一人。\n电视开着但没有声音。\n厨房里的灯亮着，地板上拖出一条长长的光斑。",
    "12": "作业本旁边压着一张纸条。\n是小明的字迹。只写了四个字。",
    "13": "通往厨房的走廊。墙上挂着一副旧日历——\n停在农历七月十五。\n地上，有一道不是我自己的影子。",
    "14": "我扶着墙，一步步挪向厨房。\n灯泡不再闪了。\n墙角那个蹲着的影子，一动不动。",
    "15": "墙角的地上，不是一碗饭。是三碗。\n筷子竖着插在米饭上。\n奶奶不在厨房里。\n但我听见身后有人轻声说了一句：你来啦。",
    "16": "我猛地回头——\n客厅沙发上坐着一个人。\n花白头发，碎花衬衫。\n端端正正地坐着，姿势太规矩了，不像活人。",
    "17": '小明妈妈说"我婆婆最近不太对"。\n但小明妈妈从没说过奶奶不在家。\n那个一直蹲在厨房墙角对着墙壁说话的人——\n是谁？',
    "18": "我冲出那扇门，跑下楼梯。\n声控灯一盏一盏灭在我身后。\n手机从口袋里滑落，屏幕亮着。",
    "19": "那个人长得跟他奶奶一模一样。",
    "20": '老师，你也是奶奶带来的吗？',
}

font = ImageFont.truetype(font_path, 28)
files = sorted(glob.glob(os.path.join(img_dir, "*.png")))

for fp in files:
    fname = os.path.basename(fp)
    prefix = fname[:2]
    if prefix not in overlays:
        continue
    
    text = overlays[prefix]
    lines = text.split("\n")
    line_h = 36
    pad = 10
    bar_h = line_h * len(lines) + pad * 2
    
    img = Image.open(fp).convert("RGBA")
    w, h = img.size
    
    # The original 3:4 image was placed at y = top_pad
    # top_pad = (target_h - original_h) // 2
    # original_h was 1448, target_h is 1930
    # top_pad = (1930 - 1448) // 2 = 241
    # The old text bar is at y = 241 in the new canvas
    old_text_y = 241
    
    # Cover old text area with dark bar
    old_bar_h = bar_h + 20
    cover = Image.new("RGBA", (w, old_bar_h), (0, 0, 0, 255))
    img.paste(cover, (0, old_text_y), cover)
    
    # Write new text at the VERY TOP (y=0)
    top_cover = Image.new("RGBA", (w, bar_h), (0, 0, 0, 220))
    img.paste(top_cover, (0, 0), top_cover)
    
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = pad + i * line_h
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    
    img = img.convert("RGB")
    img.save(fp, "PNG")
    print(f"OK: {fname}")

print("Done!")
