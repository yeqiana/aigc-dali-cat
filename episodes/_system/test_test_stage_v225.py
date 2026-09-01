#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[2]; SYSTEM=ROOT/"episodes"/"_system"
def main():
 for cmd in [[sys.executable,str(SYSTEM/"test_stage_v225.py"),"self-test"],[sys.executable,str(SYSTEM/"test_stage_v224.py"),"self-test"],[sys.executable,str(SYSTEM/"codex_subscription_image.py"),"self-test"]]:
  r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,encoding="utf-8",errors="replace"); print(r.stdout.strip());
  if r.returncode!=0: print(r.stderr.strip()); return r.returncode
 print("STORY OS V2.2.5 FAST PATH INTEGRATION SELF-TEST PASS"); return 0
if __name__=="__main__": raise SystemExit(main())
