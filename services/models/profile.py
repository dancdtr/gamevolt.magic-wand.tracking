from __future__ import annotations

from dataclasses import dataclass

from wizards.wizard_level import WizardLevel


@dataclass(frozen=True)
class Profile:
    wand_id: str
    wizard_name: str
    wizard_level: WizardLevel
