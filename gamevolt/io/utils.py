import json
import os
import sys
from pathlib import Path

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


def _entry_dir() -> Path:
    """
    Directory of the entrypoint script you executed (e.g. main.py).
    This is the repo root when you run `python main.py` from the repo.
    """
    try:
        p = Path(sys.argv[0]).resolve()
        if p.is_file():
            return p.parent
    except Exception:
        pass
    return Path.cwd()


def bundled_root() -> str:
    """
    Where bundled resources live.
    - PyInstaller: sys._MEIPASS (extracted bundle dir)
    - Dev: directory of the entry script (repo root)
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return str(Path(getattr(sys, "_MEIPASS")).resolve())
    return str(_entry_dir())


def install_root() -> str:
    """
    Where user-editable/runtime files live.
    - PyInstaller: directory containing the executable
    - Dev: directory of the entry script (repo root)
    """
    if getattr(sys, "frozen", False):
        return str(Path(sys.executable).resolve().parent)
    return str(_entry_dir())


def bundled_path(*parts: str) -> str:
    return os.path.join(bundled_root(), *parts)


def install_path(*parts: str) -> str:
    return os.path.join(install_root(), *parts)
