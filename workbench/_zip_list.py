
import zipfile,pathlib
zp=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')/r'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'/'deliveries'/'05_婚礼前夜_记忆麻醉_DELEGATED_AUTO_F01FACE.zip'
with zipfile.ZipFile(zp) as zf:
    names=zf.namelist()
for n in names:
    if 'cover' in n or n.endswith('.json') or n.endswith('.yaml') or n.endswith('.md'):
        print(n)

