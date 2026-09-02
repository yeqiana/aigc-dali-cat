#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys, json

ROOT = Path(__file__).resolve().parents[2]
SYSTEM = ROOT / "episodes" / "_system"

def main():
    r = subprocess.run(
        [sys.executable, str(SYSTEM / "capture_grammar_v228.py")],
        cwd=ROOT, text=True, capture_output=True, encoding="utf-8", errors="replace"
    )
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr)
        raise SystemExit(r.returncode)

    grammar_path = ROOT / "standards/capture_grammars/FIRST_PERSON_CASUAL_SNAPSHOT_V1.json"
    g = json.loads(grammar_path.read_text(encoding="utf-8-sig"))

    assert g["story_os_version"] == "2.2.8"
    assert g["camera_authorship"]["ghost_camera_forbidden"] is True
    assert g["camera_roster"]["primary_photographer_required"] is True
    assert g["shot_grammar_diversity"]["repeated_hand_phone_distant_anomaly_template_forbidden"] is True
    assert g["camera_defect_physics"]["defects_must_have_physical_cause"] is True
    assert g["visual_memory_continuity"]["time_of_day_must_progress_plausibly"] is True
    assert g["screen_content_physics"]["must_be_internally_consistent"] is True

    bridge = (SYSTEM / "visual_profile_bridge_v224.py").read_text(encoding="utf-8")
    assert "import capture_grammar_v228" in bridge
    assert "capture_grammar_v228.compile_capture_contract(ep)" in bridge

    backend = (SYSTEM / "codex_subscription_image.py").read_text(encoding="utf-8")
    assert "visual_profile_bridge_v224" in backend
    assert "compile_prompt_contract" in backend

    rules = (ROOT / "rules/photography_os_default_rules.md").read_text(encoding="utf-8")
    assert "STORY_OS_V228_PHOTOGRAPHY_CONTINUITY_START" in rules

    print("STORY OS V2.2.8 R2 LOCAL-SAFE INTEGRATION SELF-TEST PASS")

if __name__ == "__main__":
    main()
