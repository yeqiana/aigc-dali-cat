# -*- coding: utf-8 -*-
import json, shutil, sys, pathlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "episodes/_system")
import release_preflight_review as rpr
import product_review_adapter as pra
from release_preflight_core import ROOT
ep = pathlib.Path("episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉").resolve()
rev = ep / rpr.RELEASE_REVIEW_REL
if rev.is_file():
    bak = rev.with_name(rev.name + ".pre-style.json")
    if not bak.is_file():
        shutil.copy2(rev, bak)
        print("review backup ->", bak.name)
reqf = ep / "meta/runtime/reviews/release-semantic-attempt-2-request.json"
if reqf.is_file():
    bak2 = reqf.with_name(reqf.name + ".pre-style.json")
    if not bak2.is_file():
        shutil.copy2(reqf, bak2)
        print("request backup ->", bak2.name)
    reqf.unlink()
    print("old FINALIZED attempt-2 request retired (history kept in backup)")
cand = ep / rpr.RELEASE_CANDIDATE_REL
if cand.is_file():
    cand.unlink()
rows = rpr.release_hashes(ep)
prompt = rpr.release_critic_prompt(ep, cand, rows)
review_rows = rpr.release_review_rows(rows)
import subtitle_layout, caption_image_audit
source_paths = list(dict.fromkeys(
    [(ROOT / row["path"]) for row in review_rows.values()]
    + [ep / subtitle_layout.REPORT_REL, ep / caption_image_audit.REL,
       pathlib.Path("standards/制作规范_正式版.md").resolve(),
       pathlib.Path("standards/release_preflight_guard_V2.0.3.5.md").resolve()]
))
req = pra.prepare(ep, kind="release-semantic", runtime="WORK", attempt=2,
                  prompt=prompt, source_paths=source_paths, candidate_path=cand)
print(json.dumps({k: req.get(k) for k in ("request_id", "request_fingerprint", "attempt", "status", "runtime", "candidate_path", "created_at")}, ensure_ascii=False, indent=1))
print("source_count:", len(req.get("source_files") or []))
for s in req.get("source_files") or []:
    if "docs/06" in s["path"] or "subtitles.yaml" in s["path"]:
        print("src:", s["path"][-60:], s["sha256"][:16])
