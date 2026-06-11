import json
from pathlib import Path

from gamevolt.io.types import JsonObject, PathLike


def load_json(path: PathLike) -> JsonObject:
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"JSON file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON file {path}: {e}") from e

    if not isinstance(data, dict):
        raise TypeError(f"Expected JSON object in {path}, got {type(data).__name__}")

    return data


def load_json_if_exists(path: PathLike) -> JsonObject | None:
    path = Path(path)
    if not path.is_file():
        return None
    return load_json(path)


def save_json(data: JsonObject, path: PathLike) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
