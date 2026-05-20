from __future__ import annotations

from abc import ABC, abstractmethod

from services.models.profile import Profile


class ProfileServiceBase(ABC):
    @abstractmethod
    async def get_profile(self, wand_id: str) -> Profile:
        raise NotImplementedError()
