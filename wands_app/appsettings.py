from dataclasses import dataclass

from display.image_libraries.configuration.spell_image_library_settings import SpellImageLibrarySettings
from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.logging.configuration.logging_settings import LoggingSettings
from motion.configuration.motion_settings import MotionSettings
from zones.visualisation.configuration.zone_visualiser_settings import ZoneVisualiserSettings
from show_system.configuration.show_system_controller_settings import ShowSystemControllerSettings
from visualisation.configuration.wand_visualiser_settings import WandVisualiserSettings
from wand.configuration.input_settings import InputSettings
from wand.configuration.wand_device_controller_settings import WandDeviceControllerSettings
from wand.configuration.wand_server_settings import WandServerSettings
from wand.streaming.configuration.wand_imu_stream_settings import WandImuStreamSettings
from wands_app.configuration.system_type import SystemType
from zones.configuration.zones_settings import ZonesSettings


@dataclass
class AppSettings(AppSettingsBase):
    name: str
    system_type: SystemType
    tracked_wand_ids: list[str]
    logging: LoggingSettings
    input: InputSettings
    motion: MotionSettings
    wand_visualiser: WandVisualiserSettings
    zones: ZonesSettings
    server: WandServerSettings
    imu_stream: WandImuStreamSettings
    show_system_controller: ShowSystemControllerSettings
    zone_visualisation: ZoneVisualiserSettings
    spell_image_library: SpellImageLibrarySettings
    wand_colours: list[str]
    wand_device_controller: WandDeviceControllerSettings
