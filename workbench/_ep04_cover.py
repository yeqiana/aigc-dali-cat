
import pathlib,json
root=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')
ep=root/'episodes/09_旧物怪谈/04_瓶中世界'
d=json.loads((ep/'meta/release-manifest.json').read_text(encoding='utf-8'))
print('cover_path',d['release']['cover_path'])
print('publish_dir',d['release']['publish_dir'])

