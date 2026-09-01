from pathlib import Path
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parent.parent
SYSTEM = REPO / "episodes" / "_system"
if str(SYSTEM) not in sys.path:
    sys.path.insert(0, str(SYSTEM))

from validation_stage_v223 import main

if __name__ == "__main__":
    main()
