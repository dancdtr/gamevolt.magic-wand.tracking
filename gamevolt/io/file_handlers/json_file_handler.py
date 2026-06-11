from __future__ import annotations

from gamevolt.io.file_handlers.file_handler import FileHandler
from gamevolt.io.types import JsonObject, PathLike
from gamevolt.io.utils.json import load_json, save_json


class JsonFileHandler(FileHandler[JsonObject]):
    def load(self, path: PathLike) -> JsonObject:
        return load_json(path)

    def save(self, data: JsonObject, path: PathLike) -> None:
        save_json(data, path)
