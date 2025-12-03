from gamevolt.io.file_handlers.file_handler import FileHandler
from gamevolt.io.typing import YamlLike
from gamevolt.io.utils import load_yaml, save_yaml, try_load_yaml


class YamlFileHandler(FileHandler):
    def load(self, path: str) -> YamlLike:
        return load_yaml(path)

    def try_load(self, path: str) -> YamlLike:
        return try_load_yaml(path)

    def save(self, data: YamlLike, path: str) -> None:
        save_yaml(data, path)
