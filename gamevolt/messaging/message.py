from abc import ABC
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, TypeVar

T = TypeVar("T", bound="Message")


@dataclass
class Message(ABC):
    Timestamp: str = field(init=False)
    MessageType: str = field(init=False)

    def __post_init__(self):
        self.Timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.MessageType = self.__class__.__name__

    @classmethod
    def from_dict(cls: type[T], dict: dict[str, Any]) -> T:
        instance = cls.__new__(cls)
        super(cls, instance).__init__()

        for k, v in dict.items():
            setattr(instance, k, v)

        instance.__post_init__()
        return instance

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)

        for key, val in result.items():
            result[key] = self._serialize_key(val)

        return result

    def _serialize_key(self, val: Any):
        if hasattr(val, "to_dict"):
            return val.to_dict()
        elif isinstance(val, list):
            return [self._serialize_key(v) for v in val]
        else:
            return val

    def __str__(self) -> str:
        return "\n".join([f"{k} : {v}" for k, v in self.__dict__.items()])
