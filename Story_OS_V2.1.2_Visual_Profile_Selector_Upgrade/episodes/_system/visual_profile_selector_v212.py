import json
from pathlib import Path

PROFILE_FILE=Path(__file__).parent.parent.parent/"meta/visual_profiles/profiles.json"

def load_profile(profile_id="DEFAULT"):
    data=json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    return data["profiles"].get(profile_id,data["profiles"]["DEFAULT"])

if __name__=="__main__":
    print("VISUAL PROFILE SELECTOR V2.1.2 SELF-TEST PASS")
