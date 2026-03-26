from dataclasses import dataclass

from anchor_area.configuration.anchor_area_manager_settings import AnchorAreaManagerSettings
from anchor_bridge.configuration.anchor_bridge_settings import AnchorBridgeSettings
from display.image_libraries.configuration.spell_image_library_settings import SpellImageLibrarySettings
from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.logging.configuration.logging_settings import LoggingSettings
from motion.configuration.motion_settings import MotionSettings
from presentation.configuration.zone_visualiser_settings import ZoneVisualiserSettings
from show_system.configuration.show_system_controller_settings import ShowSystemControllerSettings
from spell_cues.configuration.wand_spell_cue_controller_settings import WandSpellCueControllerSettings
from spells.accuracy.configuration.accuracy_scorer_settings import SpellAccuracyScorerSettings
from spells.configuration.spell_registry_settings import SpellRegistrySettings
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from wand.configuration.input_settings import InputSettings
from wand.configuration.wand_device_controller_settings import WandDeviceControllerSettings
from wand.configuration.wand_server_settings import WandServerSettings
from wizards.configuration.wizard_stats_manager_settings import WizardStatsManagerSettings
from zones.configuration.zones_settings import ZonesSettings


@dataclass
class AppSettings(AppSettingsBase):
    name: str
    is_dev: bool
    logging: LoggingSettings
    input: InputSettings
    motion: MotionSettings
    wand_visualiser: WandVisualiserSettings
    accuracy: SpellAccuracyScorerSettings
    zones: ZonesSettings
    server: WandServerSettings
    show_system_controller: ShowSystemControllerSettings
    anchor_bridge: AnchorBridgeSettings
    zone_visualisation: ZoneVisualiserSettings
    spell_image_library: SpellImageLibrarySettings
    wand_colours: list[str]
    spell_registry: SpellRegistrySettings
    anchor_area_manager: AnchorAreaManagerSettings
    wand_spell_cue_controller: WandSpellCueControllerSettings
    wand_device_controller: WandDeviceControllerSettings
    wizard_stats_manager: WizardStatsManagerSettings
