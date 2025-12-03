from gamevolt.io.file_handlers.file_handler import FileHandler
from gamevolt.io.typing import JsonLike
from gamevolt.io.utils import load_json, save_json, try_load_json


class JsonFileHandler(FileHandler):
    def load(self, path: str) -> JsonLike:
        return load_json(path)

    def try_load(self, path: str) -> JsonLike:
        return try_load_json(path)

    def save(self, data: JsonLike, path: str) -> None:
        save_json(data, path)
