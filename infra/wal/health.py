"""A stale heartbeat means the WAL archive writer is not processing the spool."""

import sys
import time
from pathlib import Path

try:
    age = time.time() - Path("/varal/wal-anchor/heartbeat").stat().st_mtime
    sys.exit(0 if 0 <= age < 60 else 1)
except OSError:
    sys.exit(1)
