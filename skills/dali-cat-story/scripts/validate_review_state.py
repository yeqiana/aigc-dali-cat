from __future__ import annotations

import argparse
from pathlib import Path
from _common import Report, VALID_REVIEW, load_yaml, stage_at_least


def _status(value):
    if isinstance(value,str): return value
    if isinstance(value,dict): return value.get("status")
    return None

def validate(manifest_path:Path,*,release:bool=False)->Report:
    r=Report("review state")
    try:d=load_yaml(manifest_path)
    except Exception as e:r.error(str(e));return r
    review=d.get("review") or {}
    if not isinstance(review,dict):r.error("review 必须是 mapping");return r
    required=review.get("release_required") or []
    if not isinstance(required,list):r.error("review.release_required 必须是数组");required=[]
    for key,value in review.items():
        if key in {"release_required","waivers"}:continue
        status=_status(value)
        if status not in VALID_REVIEW:r.error(f"review.{key} 状态非法: {status!r}")
    need=release or stage_at_least(str(d.get("stage","candidate")),"release_ready")
    if need:
        waivers=review.get("waivers") or {}
        for key in required:
            status=_status(review.get(key))
            if status=="passed":continue
            if status=="waived":
                reason=waivers.get(key) if isinstance(waivers,dict) else None
                if not str(reason or "").strip():r.error(f"review.{key}=waived 但没有 waiver 原因")
                continue
            r.error(f"发布门禁未通过: review.{key}={status or 'missing'}")
    return r

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("manifest",type=Path);ap.add_argument("--release",action="store_true")
    a=ap.parse_args();r=validate(a.manifest.resolve(),release=a.release);r.print();return 0 if r.ok else 1
if __name__=="__main__":raise SystemExit(main())
