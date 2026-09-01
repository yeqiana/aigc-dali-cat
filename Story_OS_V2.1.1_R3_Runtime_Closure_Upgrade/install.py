from pathlib import Path
import json, shutil, datetime, sys

VERSION="Story_OS_V2.1.1_R3_Runtime_Closure"

def main():
    repo = Path(sys.argv[sys.argv.index("--repo")+1]).resolve() if "--repo" in sys.argv else Path.cwd()
    backup = repo / ".storyos_backups" / ("r3_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": VERSION,
        "installed_at": datetime.datetime.now().isoformat(),
        "repo": str(repo),
        "backup": str(backup),
        "status": "INSTALL_TEMPLATE_READY"
    }

    out = repo / ".storyos_v211_r3_install.json"
    out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Story OS R3 upgrade framework installed")
    print(out)

if __name__=="__main__":
    main()
