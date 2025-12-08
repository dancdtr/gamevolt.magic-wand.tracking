from dataclasses import dataclass

from display.image_providers.configuration.image_provider_settings import ImageProviderSettings


@dataclass
class SpellImageLibrarySettings:
    instruction: ImageProviderSettings
    success: ImageProviderSettings
