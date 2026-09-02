#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))

import visual_narrative_core_v22

if __name__ == "__main__":
    raise SystemExit(visual_narrative_core_v22.main())
