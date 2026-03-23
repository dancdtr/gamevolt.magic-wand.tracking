from dataclasses import dataclass

from display.image_providers.configuration.image_provider_settings import ImageProviderSettings
from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class SpellImageLibrarySettings(SettingsBase):
    instruction: ImageProviderSettings
    success: ImageProviderSettings
