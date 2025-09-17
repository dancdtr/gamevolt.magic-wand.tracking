from logging import Logger

from classification.classifiers.flicks import (
    is_flick_ccw_ne,
    is_flick_ccw_nw,
    is_flick_ccw_se,
    is_flick_ccw_sw,
    is_flick_cw_ne,
    is_flick_cw_nw,
    is_flick_cw_se,
    is_flick_cw_sw,
)
from classification.gesture_type import GestureType
from detection.gesture import Gesture
from detection.gesture_func_provider import GestureFuncProvider, GestureIdentifier
from gamevolt.messaging.events.message_handler import MessageHandler
from gamevolt.messaging.message import Message
from messaging.target_gestures_message import TargetGesturesMessage


class GestureIdentifierController:
    def __init__(self, logger: Logger, func_provider: GestureFuncProvider, message_handler: MessageHandler) -> None:
        self._logger = logger
        self._func_provider = func_provider
        self._message_handler = message_handler

        self._active_funcs: dict[GestureType, GestureIdentifier] = {}

    def start(self) -> None:
        print("STARTED!!")
        self._message_handler.subscribe(TargetGesturesMessage, self._on_target_gestures_message)

    def stop(self) -> None:
        self._message_handler.unsubscribe(TargetGesturesMessage, self._on_target_gestures_message)

    def identify(self, gesture: Gesture) -> list[GestureType]:
        types: list[GestureType] = []

        # print(f"General V dir: {get_vertical_dir(gesture)}")
        # print(f"General H dir: {get_horizontal_direction(gesture)}")

        # print(f"EN: {is_flick_e_then_n(gesture)}")
        print(f"NE: {is_flick_ccw_ne(gesture)}")
        print(f"SE: {is_flick_ccw_se(gesture)}")
        print(f"SW: {is_flick_ccw_sw(gesture)}")
        print(f"NW: {is_flick_ccw_nw(gesture)}")
        # print(f"NE: {is_flick_cw_ne(gesture)}")
        # print(f"SE: {is_flick_cw_se(gesture)}")
        # print(f"SW: {is_flick_cw_sw(gesture)}")
        # print(f"NW: {is_flick_cw_nw(gesture)}")
        # print(f"SE: {is_flick_s_then_e(gesture)}")
        # print(f"WS: {is_flick_w_then_s(gesture)}")
        # print(f"NW: {is_flick_n_then_w(gesture)}")

        for type, func in self._active_funcs.items():
            if func(gesture):
                types.append(type)

        return types

    def _on_target_gestures_message(self, message: Message) -> None:
        if not isinstance(message, TargetGesturesMessage):
            return

        print(message.Timestamp)

        self._active_funcs.clear()
        for name in message.GestureNames:
            gesture_type = GestureType(name)
            self._active_funcs[gesture_type] = self._func_provider.get(gesture_type)

        self._logger.info(f"Updated target gestures to: {[g.name for g in self._active_funcs.keys()]}")
