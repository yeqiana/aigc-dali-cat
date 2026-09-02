#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYSTEM))

import world_identity_contract

if __name__ == "__main__":
    raise SystemExit(world_identity_contract.main())
