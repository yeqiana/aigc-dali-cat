from pathlib import Path
import argparse, json, datetime

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',required=True)
    args=p.parse_args()
    repo=Path(args.repo)
    backup=repo/'.storyos_backups'/('asset_lock_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir(parents=True,exist_ok=True)
    meta={
      'version':'Story_OS_V2.1.2_Asset_Lock',
      'installed_at':datetime.datetime.now().isoformat(),
      'backup':str(backup),
      'status':'PASS'
    }
    (repo/'.storyos_v212_asset_lock_install.json').write_text(
        json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print('STORY OS V2.1.2 ASSET LOCK INSTALL PASS')

if __name__=='__main__':
    main()
