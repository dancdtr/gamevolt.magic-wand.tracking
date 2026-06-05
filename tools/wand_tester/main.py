"""Entry point for the wand LED + haptic GUI tester. See README.md."""

from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
# Project root for `wand.streaming.eliko.*`; tools/ so the `wand_tester`
# package resolves as a top-level import.
sys.path.insert(0, str(_here.parent.parent))
sys.path.insert(0, str(_here.parent))

from wand_tester.app import main  # noqa: E402

if __name__ == "__main__":
    main()
