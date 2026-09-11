
import hashlib,pathlib,json
root=pathlib.Path(r'D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat')
for ser in sorted((root/'episodes').glob('09_*')):
    for ep in sorted(ser.iterdir()):
        if not ep.is_dir() or ep.name.startswith('_'): continue
        man=ep/'meta/release-manifest.json'
        if not man.is_file(): continue
        d=json.loads(man.read_text(encoding='utf-8'))
        rel=d.get('release') or {}
        cp=rel.get('cover_path'); pd=rel.get('publish_dir')
        if not cp or not pd: continue
        c=root/cp; p1=sorted((root/pd).glob('[0-9][0-9].png'))
        if not c.is_file() or not p1: continue
        hs=lambda x: hashlib.sha256(x.read_bytes()).hexdigest()[:10]
        print(ep.name, 'cover',hs(c), 'body01',hs(p1[0]), 'same' if hs(c)==hs(p1[0]) else 'DIFF')

