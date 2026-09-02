#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))

import production_readiness_v221

if __name__ == "__main__":
    raise SystemExit(production_readiness_v221.main())
