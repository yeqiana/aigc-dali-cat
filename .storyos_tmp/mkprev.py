from PIL import Image
base = r"episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉"
for name, src in [("p01", base + r"/production/publish/01.png"), ("a01", base + r"/media/approved/01.png")]:
    im = Image.open(src).convert("RGB")
    im.thumbnail((420, 525))
    im.save(r".storyos_tmp/" + name + "_prev.jpg", quality=78)
    print(name, im.size)
