from __future__ import annotations

from pathlib import Path

import yaml

from gamevolt.io.types import PathLike, YamlObject


def load_yaml(path: PathLike) -> YamlObject:
    path = Path(path)

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"YAML file not found: {path}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file {path}: {e}") from e

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise TypeError(f"Expected YAML mapping in {path}, got {type(data).__name__}")

    return data


def load_yaml_if_exists(path: PathLike) -> YamlObject | None:
    path = Path(path)
    if not path.is_file():
        return None
    return load_yaml(path)


def save_yaml(data: YamlObject, path: PathLike) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                data=data,
                stream=f,
                sort_keys=False,
                default_flow_style=False,
                allow_unicode=True,
            )
    except OSError as e:
        raise OSError(f"Failed to save YAML to {path}: {e}") from e
