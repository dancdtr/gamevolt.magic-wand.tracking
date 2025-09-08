import os
from tkinter import Tk, Toplevel

from PIL.ImageTk import PhotoImage

from classification.gesture_type import GestureType
from display.image_providers.gestures.arc_180_image_provider import Arc180ImageProvider
from display.image_providers.gestures.arc_270_image_provider import Arc270ImageProvider
from display.image_providers.gestures.arc_360_image_provider import Arc360ImageProvider
from display.image_providers.gestures.cardinal_line_image_provider import CardinalLineImageProvider
from display.image_providers.gestures.crook_image_provider import CrookImageProvider
from display.image_providers.gestures.debug_image_provider import DebugImageProvider
from display.image_providers.gestures.gesture_image_provider import GestureImageProvider
from display.image_providers.gestures.hook_image_provider import HookImageProvider
from display.image_providers.gestures.intercardinal_line_image_provider import IntercardinalLineImageProvider
from display.image_providers.gestures.inverse_crook_image_provider import InverseCrookImageProvider
from display.image_providers.gestures.inverse_hook_image_provider import InverseHookImageProvider
from display.image_providers.gestures.sine_360_image_provider import Sine360ImageProvider
from display.image_providers.gestures.sine_540_image_provider import Sine540ImageProvider
from display.image_providers.gestures.sub_intercardinal_line_image_provider import SubIntercardinalLineImageProvider
from display.images.libraries.configuration.image_library_settings import ImageLibrarySettings


class GestureImageLibrary:
    def __init__(self, settings: ImageLibrarySettings) -> None:
        self._settings = settings

    def load(self, tk_master: Toplevel | Tk) -> None:
        def build_path(png: str) -> str:
            return os.path.join(self._settings.assets_dir, png)

        image_size = self._settings.image_size

        image_providers: list[GestureImageProvider] = [
            DebugImageProvider(build_path("unknown.png"), build_path("none.png"), image_size),
            CardinalLineImageProvider(build_path("cardinal_line.png"), image_size),
            CrookImageProvider(build_path("crook.png"), image_size),
            HookImageProvider(build_path("hook.png"), image_size),
            InverseHookImageProvider(build_path("inverse_hook.png"), image_size),
            InverseCrookImageProvider(build_path("inverse_crook.png"), image_size),
            IntercardinalLineImageProvider(build_path("intercardinal_line.png"), image_size),
            SubIntercardinalLineImageProvider(build_path("sub_intercardinal_line.png"), image_size),
            Arc180ImageProvider(build_path("arc_180.png"), image_size),
            Arc270ImageProvider(build_path("arc_270.png"), image_size),
            Arc360ImageProvider(build_path("arc_360.png"), image_size),
            Sine360ImageProvider(build_path("sine_360.png"), image_size),
            Sine540ImageProvider(build_path("sine_540.png"), image_size),
        ]

        self._images: dict[GestureType, PhotoImage] = {}

        for provider in image_providers:
            provider.load()

            for type, image in provider.items():
                self._images[type] = PhotoImage(image, master=tk_master)

    def get_image(self, gesture_type: GestureType) -> PhotoImage:
        image = self._images.get(gesture_type)
        if image is not None:
            return image

        raise RuntimeError(f"No image to display for gesture: '{gesture_type}'!")
