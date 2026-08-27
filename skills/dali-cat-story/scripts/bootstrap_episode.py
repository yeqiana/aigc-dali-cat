from __future__ import annotations

import argparse, shutil
from pathlib import Path


def find_repo(start:Path)->Path:
    p=start.resolve()
    for cand in [p,*p.parents]:
        if (cand/"standards"/"制作规范_正式版.md").exists() and (cand/"episodes").exists():return cand
    raise SystemExit("无法定位仓库根目录（需要 standards/制作规范_正式版.md 与 episodes/）")

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("episode_dir",type=Path);ap.add_argument("--force",action="store_true")
    a=ap.parse_args();ep=a.episode_dir.resolve();ep.mkdir(parents=True,exist_ok=True);repo=find_repo(ep)
    tpl=repo/"standards"/"templates"/"episode.template.yaml"
    sub_tpl=repo/"standards"/"templates"/"subtitles.template.yaml"
    if not tpl.exists():raise SystemExit(f"缺少模板: {tpl}")
    manifest=ep/"episode.yaml"
    if manifest.exists() and not a.force:raise SystemExit(f"已存在，不覆盖: {manifest}")
    series=ep.parent.name
    title=ep.name
    text=tpl.read_text(encoding="utf-8").replace("__EPISODE_ID__",ep.name).replace("__EPISODE_TITLE__",title).replace("__SERIES__",series)
    manifest.write_text(text,encoding="utf-8")
    sub=ep/"docs"/"subtitles.yaml"
    if sub_tpl.exists() and not sub.exists():
        sub.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(sub_tpl,sub)
    print(f"created: {manifest.relative_to(repo)}")
    if sub.exists():print(f"created: {sub.relative_to(repo)}")
    print("next: 填写 manifest → stage=story_locked → 运行 validate_all.py")
    return 0
if __name__=="__main__":raise SystemExit(main())
