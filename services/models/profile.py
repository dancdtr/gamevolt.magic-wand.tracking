from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    wand_id: str
    wizard_name: str
