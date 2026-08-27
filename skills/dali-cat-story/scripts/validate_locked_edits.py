from __future__ import annotations

import argparse,re
from pathlib import Path
from _common import Report, load_yaml, resolve_episode_path, sha256_file
HEX64=re.compile(r"^[0-9a-fA-F]{64}$")

def validate(manifest_path:Path,*,release:bool=False)->Report:
    r=Report("locked assets")
    try:d=load_yaml(manifest_path)
    except Exception as e:r.error(str(e));return r
    locks=d.get("locks") or {}
    assets=locks.get("assets") or []
    if not isinstance(assets,list):r.error("locks.assets 必须是数组");return r
    mode=str(locks.get("edit_mode","none"))
    if mode not in {"none","subtitle_only","crop_only","regenerate_frame","regenerate_sequence"}:
        r.error(f"locks.edit_mode 非法: {mode}")
    if mode=="subtitle_only" and not assets:
        r.warn("edit_mode=subtitle_only 但没有登记任何锁定底图 hash")
    for i,item in enumerate(assets,1):
        if not isinstance(item,dict):r.error(f"locks.assets[{i}] 必须是 mapping");continue
        rel=item.get("path");expected=str(item.get("sha256","")).lower()
        if not rel:r.error(f"locks.assets[{i}] 缺 path");continue
        if not HEX64.match(expected):r.error(f"锁定资产 {rel} 的 sha256 必须是64位十六进制");continue
        p=resolve_episode_path(manifest_path,str(rel))
        if not p or not p.exists():r.error(f"锁定资产不存在: {p}");continue
        actual=sha256_file(p)
        if actual!=expected:r.error(f"锁定资产已变化: {rel}\n    expected={expected}\n    actual  ={actual}")
    return r

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("manifest",type=Path);ap.add_argument("--release",action="store_true")
    a=ap.parse_args();r=validate(a.manifest.resolve(),release=a.release);r.print();return 0 if r.ok else 1
if __name__=="__main__":raise SystemExit(main())
