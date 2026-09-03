import argparse, json
from pathlib import Path
from datetime import datetime

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True)
    a=p.parse_args()
    repo=Path(a.repo)
    target=repo/"config/story_os/narrative_rules/narrative_experience_v222.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps({
        "version":"2.2.2",
        "rules":{
            "PHOTO_EVIDENCE_ENDING_FORBIDDEN":True,
            "IMMERSIVE_FIRST_PERSON_PRESENTATION":True,
            "CN_YOUNG_FEMALE_ANCHOR_DEFAULT_V1":True,
            "FEMALE_CHARACTER_NARRATIVE_ROLE_V1":True,
            "NO_SILENT_TWIST_ENDING":True
        }
    },ensure_ascii=False,indent=2),encoding="utf-8")
    print("STORY OS V2.2.2 NARRATIVE EXPERIENCE PATCH INSTALL PASS")
    print("PHOTO_EVIDENCE_ENDING_FORBIDDEN=ENABLED")
    print("IMMERSIVE_FIRST_PERSON_PRESENTATION=ENABLED")
    print("CN_YOUNG_FEMALE_ANCHOR_DEFAULT=ENABLED")
    print("FEMALE_CHARACTER_NARRATIVE_ROLE=ENABLED")
    print("NO_SILENT_TWIST_ENDING=ENABLED")

if __name__=="__main__":
    main()
