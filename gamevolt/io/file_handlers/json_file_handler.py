from gamevolt.io.typing import JsonLike

from ..utils import load_json, save_json, try_load_json
from .file_handler import FileHandler


class JsonFileHandler(FileHandler):
    def load(self, path: str) -> JsonLike:
        return load_json(path)

    def try_load(self, path: str) -> JsonLike:
        return try_load_json(path)

    def save(self, data: JsonLike, path: str) -> None:
        save_json(data, path)
