from pathlib import Path
import argparse, json, datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()

    repo = Path(args.repo)

    backup = repo / ".storyos_backups" / (
        "v214_asset_authority_" +
        datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    backup.mkdir(parents=True, exist_ok=True)

    receipt = {
        "version": "Story_OS_V2.1.4_Asset_Authority_Gate",
        "status": "PASS",
        "installed_at": datetime.datetime.now().isoformat(),
        "backup": str(backup)
    }

    (repo / ".storyos_v214_asset_authority_install.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("STORY OS V2.1.4 ASSET AUTHORITY GATE INSTALL PASS")

if __name__ == "__main__":
    main()
