# -*- coding: utf-8 -*-
import pathlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/_system")
ROOT = pathlib.Path(r"D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat")
EP = ROOT / "episodes" / "09_旧物怪谈" / "05_婚礼前夜_记忆麻醉"

import product_review_adapter
import release_preflight_review as rpr

candidate = EP / rpr.RELEASE_CANDIDATE_REL
data, provenance = product_review_adapter.finalize_candidate(
    EP, kind="release-semantic", runtime="WORK", attempt=2, candidate_path=candidate,
)
rc = rpr._finalize_release_review(EP, data, provenance)
if rc == 0:
    product_review_adapter.mark_complete(
        EP, "release-semantic", attempt=2, final_path=EP / rpr.RELEASE_REVIEW_REL
    )
print("FINALIZE_RC:", rc)
