from gamevolt.configuration.appsetting import appsetting
from motion.configuration.motion_processor_settings import MotionProcessorSettings


@appsetting
class MotionSettings:
    processor: MotionProcessorSettings
