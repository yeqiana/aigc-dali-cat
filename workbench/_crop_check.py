
from PIL import Image
import pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
for name,src in (('cover','production/cover/cover.png'),('pub01','production/publish/01.png'),('pub12','production/publish/12.png')):
    im=Image.open(ep/src)
    w,h=im.size
    crop=im.crop((0,int(h*0.72),w,h))
    out=ep/f'meta/.crop-{name}-bottom.png'
    crop.save(out)
    print(name,im.size,'->',out.name)

