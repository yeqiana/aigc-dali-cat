import json
import shutil
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))

from validation_stage_v223 import validate_bootstrap, validate_preproduction


def w(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory() as td:
        ep = Path(td) / "EP001"
        ep.mkdir()
        w(ep/"meta/episode_blueprint.json", {"episode_id":"EP001","status":"BOOTSTRAPPED"})
        w(ep/"meta/chapter_lock.json", {"chapter":"EP01","scope":"start-to-end"})
        w(ep/"meta/visual_profile.json", {"visual_profile_id":"TEST_V1"})
        w(ep/"meta/asset_manifest.json", {"required":["character","location","prop"]})

        r1 = validate_bootstrap(ep)
        assert r1["status"] == "BOOTSTRAP_VALIDATE_PASS", r1

        w(ep/"meta/character_contract.json", {"character":"A"})
        w(ep/"meta/location_contract.json", {"location":"L"})
        w(ep/"meta/prop_contract.json", {"prop":"P"})
        w(ep/"meta/resolved_frame_contracts.json", {"frames":[{"id":"01"}]})
        w(ep/"meta/authority.json", {
            "authority_scope":"current_story_branch",
            "authority_sha":"abcdef1234567890"
        })

        r2 = validate_preproduction(ep)
        assert r2["status"] == "PREPRODUCTION_VALIDATE_PASS", r2

    print("STORY OS V2.2.3 VALIDATION STAGE SPLIT SELF TEST PASS")


if __name__ == "__main__":
    main()
