# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont

V3_DIR = r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat\episodes\02_折多山守夜人\v3_final"
OUT_DIR = os.path.join(V3_DIR, "subtitled")
os.makedirs(OUT_DIR, exist_ok=True)

FONT_PATH = r"C:\Windows\Fonts\msyh.ttc"
FONT_SIZE = 28
PADDING_X = 28
PADDING_Y = 20
BAR_ALPHA = 150
BUBBLE_RADIUS = 20
BUBBLE_MAX_WIDTH_RATIO = 0.75

SUBTITLES = {
    "图01": ("我叫林晚，22岁，成都人。爷爷三十年前在折多山修路，十二个人失踪只找到十一具。他遗照背面有一行发抖的字：山下面有东西。它醒了。", 0.55),
    "图02": ("在爷爷箱子底找到一张照片。十二个穿蓝色工装的人站在道班房门口。背面是爷爷的字，笔迹在发抖。", 0.58),
    "图02b": ("那天晚上我没睡着。爷爷失踪那年我还没出生。但那个发抖的笔迹——我认识。那是害怕。", 0.12),
    "图03": ("没有人知道第三道班在哪。一个老藏民看到照片背面那行字，把照片扣在桌上。他说：这条路，不在太阳照得到的地方。", 0.08),
    "图03b": ("路边藏民小卖部，矿泉水和青稞饼。太阳很大，318上偶尔有车经过。那是我最后一次觉得一切都很正常。", 0.55),
    "图04": ("路口被经幡遮住了。歪脖子树上刻满了藏文经文，密密麻麻，像在盖住什么。这条路GPS上没有。", 0.08),
    "图04b": ("我一只脚踩在柏油路上，一只脚踩在碎石上。太阳在头顶，但旧路上没有阳光。小周说：进不进？我说：进。", 0.52),
    "图05": ("路越来越窄，GPS信号断了。明明是中午，天空像黄昏。来路是一片雾，雾里有光在闪。像呼吸。", 0.10),
    "图05b": ("音乐什么时候停的。窗外的树一直在重复。不是相似的树，是同一棵。过了十七次。", 0.55),
    "图06": ("门口旧自行车轮胎完全瘪了。但车把手上挂着一条白毛巾。白毛巾是新的。铁门是温的。", 0.78),
    "图06a": ("树林突然断开。前面是空地，中间一个灰色水泥建筑。和照片里一模一样。门缝里透出暖黄色的光。", 0.50),
    "图07": ("屋子中央长条木桌——十二副碗筷。白米饭冒热气。小周摸了摸碗：是烫的。好像十二个人刚刚放下筷子。", 0.80),
    "图07b": ("墙上老日历翻在七月。十五号被人用指甲画了三条竖线。我找到爷爷的杯子——里面有半杯茶。茶是温的。", 0.05),
    "图08": ("桌子尽头——第十三副碗筷。碗是新的，米饭比别人都满。碗下面压着纸条。纸条上是我的名字。林晚。", 0.78),
    "图08b": ("小周的脸一半在灯光里，一半在阴影里。她没说话，但握着我的手——很紧。从小到大她从来不握人的手。", 0.62),
    "图09": ("电视自己亮了。同一间屋子，同一张桌子。十二个穿蓝色工装的工人围坐在一起。1987年7月15日。下午四点十分。", 0.05),
    "图10": ("画面里有人放下碗，抬起头，朝镜头看过来。是爷爷。比照片上老，比我想象中瘦。他说：晚晚，你不该来的。", 0.05),
    "图10b": ("我从来没见过爷爷。他在叫我——晚晚。只有家里人这么叫。一个我从来没见过的老人，隔着三十年，叫了我的小名。", 0.05),
    "图10c": ("爷爷站在漩涡般的黑暗里，双臂张开。身后的虚空中排列着无数暖黄光窗——那是全中国深山里的一百零八个道班。他挡了三十年。", 0.05),
    "图10d": ("屏幕里爷爷在吃饭。但门口站着一个东西——极高极瘦的人形，两只黄眼睛在黑暗中发亮。它就这样看着。", 0.05),
    "图11": ("爷爷也伸出了手，按在屏幕内侧。积了三十年的灰尘裂开了。他不是影像。他在里面。推了三十年的玻璃。", 0.05),
    "图11b": ("GPS重新启动了。屏幕上的轨迹——一个完美的圆。里程十公里。这条路长度只有一点六公里。我们一直在绕。", 0.55),
    "图12": ("推开门。外面不是川西。是一片巨大的黑暗。不是夜晚——是没有光的空间。黑暗中排列着无数暖黄光点。每一个都是一间道班房。", 0.55),
    "图12b": ("那些光窗均匀排列，像另一片星空。但每一个光点背后都有一个守夜人。一百零八个。已经有人撑不住了。", 0.10),
    "图12c": ("黑暗中有东西在往窗里看。一张巨大的脸。皮肤像石头，像树皮。那只眼睛直直地盯着屋里——它感觉到了。这个锁快碎了。", 0.06),
    "图13": ("黑暗中走出一个人。是那个老藏民。他脚不沾地。他说：折多山下面是格萨尔王斩杀的最后一个魔物。每三十年需要一个守夜人。", 0.55),
    "图14": ("多了一封信。爷爷的笔迹——不是1987年写的，是昨天。晚晚，你还是找来了。对不起。爷爷没有失踪。我是自愿留下的。", 0.55),
    "图14b": ("我把信翻过来。背面还有一句话，字更小更抖。但我希望你不要走。爷爷等了你二十二年。是想看看你长大的样子。", 0.55),
    "图15": ("我拉开椅子坐下，拿起筷子。小周在门口喊我，声音越来越远。电视画面里——爷爷也坐下了。他说：欢迎回家。", 0.80),
    "图15b": ("小周走了。黑暗给她让了一条道。因为锁不需要两个人。一个就够了。桌上她那杯水还是满的。没喝过。", 0.55),
    "图16": ("醒来时手机里多了一张照片。十三个人坐在长桌前。十二个穿蓝色工装，一个是我。爷爷把手搭在我肩膀上。他在笑。", 0.08),
    "图16b": ("1987年7月。十五号——一个勾，林德厚。十六号以后全部空白。最后一页夹着一张工作证。上面写着两个字：守夜。", 0.78),
    "图18": ("小周发来消息：已经报警了。他们说根本没有什么第三道班。GPS显示你的位置是无人区。海拔负的。我说不用了。爷爷做的炒土豆丝——还是1987年的味道。", 0.08),
    "图19": ("铁门内侧——从上到下四道一组的抓痕。上千组。最下面那组还没刻完，只有三道。什么时候变成一秒——锁就锁不住了。", 0.08),
    "图19b": ("我坐在门槛上。一百零七盏光窗。昨晚少了一盏。今天又亮了，但位置变了，更近了。少了一个守夜人，多了一个快碎的锁。", 0.12),
    "图20": ("最后发送——收件人小周。如果有人经过折多山，看到歪脖子树上挂满经幡，树下面有条旧路。不要走进去。替我跟爷爷说一声——碗里的饭凉了，帮他热一下。他不喜欢太满。", 0.08),
}

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)

def process_image(img_path, out_path, subtitle, pos_ratio):
    img = Image.open(img_path).convert("RGBA")
    W, H = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    max_text_width = int(W * BUBBLE_MAX_WIDTH_RATIO) - PADDING_X * 2
    lines = []
    current = ""
    for char in subtitle:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_text_width:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    line_height = FONT_SIZE + 6
    text_h = line_height * len(lines)
    bubble_w = int(W * BUBBLE_MAX_WIDTH_RATIO)
    bubble_h = text_h + PADDING_Y * 2
    bubble_x = (W - bubble_w) // 2
    bubble_y = int(H * pos_ratio)
    draw_rounded_rect(draw, (bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h), BUBBLE_RADIUS, (0, 0, 0, BAR_ALPHA))
    text_start_y = bubble_y + PADDING_Y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = bubble_x + (bubble_w - tw) // 2
        draw.text((tx, text_start_y), line, font=font, fill=(255, 255, 255, 255))
        text_start_y += line_height
    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(out_path, "PNG", quality=95)

files = sorted(os.listdir(V3_DIR))
processed = 0
for f in files:
    if not f.endswith(".png"):
        continue
    key = f.replace(".png", "")
    if key not in SUBTITLES:
        continue
    img_path = os.path.join(V3_DIR, f)
    out_path = os.path.join(OUT_DIR, f)
    subtitle, pos = SUBTITLES[key]
    print(f"Processing {key} (pos={pos})...")
    process_image(img_path, out_path, subtitle, pos)
    processed += 1
print(f"Done! {processed} images -> {OUT_DIR}")
