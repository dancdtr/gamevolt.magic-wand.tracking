from display.image_providers.configuration.image_provider_settings import ImageProviderSettings
from gamevolt.configuration.appsetting import appsetting


@appsetting
class SpellImageLibrarySettings:
    instruction: ImageProviderSettings
    success: ImageProviderSettings
