from __future__ import annotations

from services.models.profile import Profile


class WizardSessionStore:
    """Per-wand profile cache. Populated on zone entry, cleared on exit."""

    def __init__(self) -> None:
        self._profiles: dict[str, Profile] = {}

    def set(self, profile: Profile) -> None:
        self._profiles[profile.wand_id] = profile

    def get(self, wand_id: str) -> Profile | None:
        return self._profiles.get(wand_id)

    def clear(self, wand_id: str) -> None:
        self._profiles.pop(wand_id, None)

    def clear_all(self) -> None:
        self._profiles.clear()
