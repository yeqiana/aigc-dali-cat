#!/usr/bin/env python3
from pathlib import Path
import os,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
SYSTEM=ROOT/"episodes"/"_system"
def main():
    cmds=[
        [sys.executable,str(SYSTEM/"visual_profile_bridge_v224.py")],
        [sys.executable,str(SYSTEM/"test_stage_v224.py"),"self-test"],
        [sys.executable,str(SYSTEM/"codex_subscription_image.py"),"self-test"],
    ]
    for cmd in cmds:
        if os.environ.get('STORYOS_CI_PYTHON_BOOTSTRAP') == '1':
            cmd.insert(1, str(ROOT / 'scripts/ci_storyos_python.py'))
        r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace")
        print((r.stdout or "").strip())
        if r.returncode!=0:
            print(r.stderr); return r.returncode
    print("STORY OS V2.2.4 INTEGRATION SELF-TEST PASS"); return 0
if __name__=="__main__": raise SystemExit(main())
