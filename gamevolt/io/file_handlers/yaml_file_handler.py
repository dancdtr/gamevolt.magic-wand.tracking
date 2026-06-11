from __future__ import annotations

from gamevolt.io.file_handlers.file_handler import FileHandler
from gamevolt.io.types import PathLike, YamlObject
from gamevolt.io.utils.yaml import load_yaml, save_yaml


class YamlFileHandler(FileHandler[YamlObject]):
    def load(self, path: PathLike) -> YamlObject:
        return load_yaml(path)

    def save(self, data: YamlObject, path: PathLike) -> None:
        save_yaml(data, path)
