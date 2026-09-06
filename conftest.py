"""Make the repository importable when running pytest from the root."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
