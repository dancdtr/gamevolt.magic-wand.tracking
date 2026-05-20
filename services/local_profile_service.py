from __future__ import annotations

from gamevolt.logging._logger import Logger
from services.models.profile import Profile
from services.profile_service_base import ProfileServiceBase
from wizards.wizard_level import WizardLevel
from wizards.wizard_names_provider import WizardNameProvider


class LocalProfileService(ProfileServiceBase):
    """In-memory profile store. Auto-mints a profile on first request for a wand."""

    def __init__(
        self,
        logger: Logger,
        name_provider: WizardNameProvider,
        default_level: WizardLevel = WizardLevel.BEGINNER,
    ) -> None:
        self._logger = logger
        self._name_provider = name_provider
        self._default_level = default_level
        self._profiles: dict[str, Profile] = {}

    async def get_profile(self, wand_id: str) -> Profile:
        profile = self._profiles.get(wand_id)
        if profile is None:
            profile = Profile(
                wand_id=wand_id,
                wizard_name=self._name_provider.get_name(),
                wizard_level=self._default_level,
            )
            self._profiles[wand_id] = profile
            self._logger.info(
                f"LocalProfileService minted profile for wand ({wand_id}): "
                f"{profile.wizard_name} [{profile.wizard_level.name}]"
            )

        return profile
