from __future__ import annotations

import argparse
from pathlib import Path
from _common import Report
import validate_episode, validate_package, validate_subtitles, validate_review_state, validate_locked_edits

def validate(manifest:Path,*,release:bool=False)->Report:
    out=Report("DALI CAT STORY GATES")
    for mod in (validate_episode,validate_package,validate_subtitles,validate_review_state,validate_locked_edits):
        out.merge(mod.validate(manifest,release=release))
    return out

def main()->int:
    ap=argparse.ArgumentParser(description="Run all story gates")
    ap.add_argument("manifest",type=Path)
    ap.add_argument("--release",action="store_true",help="enforce release-ready gates")
    a=ap.parse_args();r=validate(a.manifest.resolve(),release=a.release);r.print();return 0 if r.ok else 1
if __name__=="__main__":raise SystemExit(main())
