from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

from gamevolt.io.types import PathLike

T = TypeVar("T")


class FileHandler(ABC, Generic[T]):
    @abstractmethod
    def load(self, path: PathLike) -> T:
        raise NotImplementedError

    @abstractmethod
    def save(self, data: T, path: PathLike) -> None:
        raise NotImplementedError

    def load_if_exists(self, path: PathLike) -> T | None:
        if not Path(path).is_file():
            return None
        return self.load(path)

    def load_or_default(self, path: PathLike, default: T) -> T:
        data = self.load_if_exists(path)
        return default if data is None else data
