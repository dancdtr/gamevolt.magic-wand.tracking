import random

from wizards.configuration.wizard_settings import WizardSettings


class WizardNameProvider:
    def __init__(self, settings: WizardSettings):
        self._settings = settings

    def get_name(self) -> str:
        return random.choice(self._settings.names)
