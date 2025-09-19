from dataclasses import dataclass

from display.image_providers.configuration.image_provider_settings import ImageProviderSettings


@dataclass
class SpellImageLibrarySettings:
    instruction_active: ImageProviderSettings
    instruction_inactive: ImageProviderSettings
    success: ImageProviderSettings
