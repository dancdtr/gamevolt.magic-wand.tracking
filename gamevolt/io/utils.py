import json
import os

import yaml

from gamevolt.io.typing import JsonLike, YamlLike


def load_json(path: str) -> JsonLike:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"JSON file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON file {path}: {e}")
    except Exception as e:
        raise IOError(f"Failed to load JSON from {path}: {e}")


def try_load_json(path: str) -> JsonLike:
    if path and os.path.isfile(path):
        return load_json(path)

    return {}


def save_json(data: JsonLike, path: str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Failed to save JSON to {path}: {e}")


def load_yaml(path: str) -> YamlLike:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data is not None else {}
    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: {path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file {path}: {e}")
    except Exception as e:
        raise IOError(f"Failed to load YAML from {path}: {e}")


def try_load_yaml(path: str) -> YamlLike:
    if path and os.path.isfile(path):
        return load_yaml(path)

    return {}


def save_yaml(data: YamlLike, path: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
    except Exception as e:
        raise IOError(f"Failed to save YAML to {path}: {e}")
