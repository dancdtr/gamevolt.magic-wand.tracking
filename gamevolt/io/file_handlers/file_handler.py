from abc import ABC, abstractmethod

from gamevolt.io.typing import JsonLike


class FileHandler(ABC):
    @abstractmethod
    def load(self, path: str) -> JsonLike:
        pass

    @abstractmethod
    def try_load(self, path: str) -> JsonLike:
        pass

    @abstractmethod
    def save(self, data: JsonLike, path: str) -> None:
        pass
