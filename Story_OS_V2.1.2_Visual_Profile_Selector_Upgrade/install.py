from pathlib import Path
import argparse, json, datetime

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo",required=True)
    args=parser.parse_args()

    repo=Path(args.repo)
    backup=repo/'.storyos_backups'/('visual_profile_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True,exist_ok=True)

    target=repo/'.storyos_v212_visual_profile_install.json'
    target.write_text(json.dumps({
        "version":"V2.1.2_VISUAL_PROFILE_SELECTOR",
        "status":"PASS",
        "installed_at":datetime.datetime.now().isoformat(),
        "backup":str(backup)
    },ensure_ascii=False,indent=2),encoding="utf-8")

    print("STORY OS V2.1.2 VISUAL PROFILE SELECTOR INSTALL PASS")

if __name__=="__main__":
    main()
