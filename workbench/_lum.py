
from PIL import Image, ImageStat
import pathlib
ep=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
im=Image.open(ep/'media/approved/01.png').convert('L')
w,h=im.size
rows=6; cols=6
print('size',w,h)
hdr='      '+''.join(f'c{c:<7}' for c in range(cols))
print(hdr)
for r in range(rows):
    vals=[]
    for c in range(cols):
        box=(int(w*c/cols),int(h*r/rows),int(w*(c+1)/cols),int(h*(r+1)/rows))
        vals.append(round(ImageStat.Stat(im.crop(box)).mean[0],1))
    print(f'r{r} '+'  '.join(f'{v:<7}' for v in vals))

