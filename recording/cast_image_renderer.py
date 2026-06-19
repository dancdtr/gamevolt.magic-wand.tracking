from __future__ import annotations

from pathlib import Path
from typing import Protocol

from spells.scoring.cast_attempt import CastAttempt


class CastImageRenderer(Protocol):
    """Renders a single cast attempt to an image file. Implemented by the Qt visualiser
    layer (reusing the snapshot view); the recorder stays free of any GUI dependency."""

    def render(self, attempt: CastAttempt, path: Path) -> None: ...
