from input.factories.configuration.input_type import InputType
from input.motion_input_base import MotionInputBase
from input.motion_input_factory import MotionInputFactory


class InputFactory:
    def __init__(self, factories: list[tuple[InputType, MotionInputFactory]]) -> None:
        self._factories: dict[InputType, MotionInputFactory] = {input_type: factory for input_type, factory in factories}

    def create(self, input_type: InputType) -> MotionInputBase:
        factory = self._factories.get(input_type)
        if factory is not None:
            return factory.create()

        raise ValueError(f"No factory defined for input type: '{input_type.name}'.")
